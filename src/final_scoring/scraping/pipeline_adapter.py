"""Scrapy item pipeline that runs LLM extraction on every scraped item.

This is the bridge between the Scrapy world and the LLM extraction
module. It enriches each :class:`RawReviewItem` with a ``reviews`` field
containing the structured records produced by the LLM, plus an
``extraction_model_version`` provenance tag.

Items that have no ``raw_text`` (e.g. listing pages, redirects) pass
through unchanged.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from scrapy.exceptions import NotConfigured

from final_scoring.config import get_settings
from final_scoring.pipeline.extraction import LLMExtractionPipeline

if TYPE_CHECKING:
    from scrapy.crawler import Crawler
    from scrapy.spiders import Spider


class ScrapyLLMPipeline:
    """Scrapy item pipeline wrapping :class:`LLMExtractionPipeline`.

    The crawler-level ``from_crawler`` constructor lets Scrapy own the
    lifecycle while the pipeline itself stays usable outside of Scrapy
    (e.g. from a backfill script).
    """

    def __init__(self, extractor: LLMExtractionPipeline) -> None:
        self.extractor = extractor

    @classmethod
    def from_crawler(cls, crawler: "Crawler") -> "ScrapyLLMPipeline":
        cfg = get_settings()
        if not cfg.llm.api_base_url and cfg.llm.api_key == "local":
            # Hard fail — silent fallback to non-extraction would
            # produce JSONL that *looks* complete but isn't.
            raise NotConfigured(
                "LLM_API_BASE_URL is unset. Configure a model endpoint "
                "or run with the no-extract spider mode."
            )
        return cls(LLMExtractionPipeline(cfg.llm))

    async def process_item(
        self,
        item: dict[str, Any],
        spider: "Spider",
    ) -> dict[str, Any]:
        raw_text = item.get("raw_text")
        if not raw_text:
            spider.logger.debug("Item has no raw_text; skipping extraction.")
            return item

        result = await self.extractor.extract(
            raw_text,
            title=item.get("title"),
            description=item.get("description"),
        )

        item["reviews"] = [r.model_dump() for r in result.reviews]
        item["extraction_model_version"] = self.extractor.extraction_version_tag

        if spider.crawler.stats:
            spider.crawler.stats.inc_value("fs/reviews_extracted", len(result.reviews))

        return item
