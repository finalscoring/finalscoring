"""Base classes and shared conventions for Final Scoring spiders.

Every source spider inherits from :class:`BaseReviewSpider` (or one of its
medium-specific subclasses, when those exist). The base ensures that:

* All spiders emit items in the same :class:`RawReviewItem` shape, so the
  shared LLM extraction pipeline and JSONL load step apply uniformly.
* Politeness settings (user agent, delay, concurrency) are centralised
  in :func:`base_settings`.
* JOBDIR resume state is automatic.
* The item pipeline runs LLM extraction before items are written, so the
  resulting JSONL files contain both raw scrape data and extracted
  reviews.
"""

from __future__ import annotations

from typing import Any, TypedDict

from scrapy import Spider

from final_scoring.config import get_settings


class RawReviewItem(TypedDict, total=False):
    """The shape every spider produces.

    Fields are optional because different sources expose different
    metadata, but every spider should populate at minimum: ``url``,
    ``critic_slug``, ``raw_text``.

    The LLM extraction stage adds the ``reviews`` field downstream.
    """

    # Provenance
    url: str
    critic_slug: str
    scraped_at: str

    # Source metadata
    title: str | None
    description: str | None
    date_published: str | None
    image: str | None
    language: str | None

    # Optional source-specific helpers
    wp_json_url: str | None
    oembed_json_url: str | None
    wp_json: dict[str, Any] | None
    oembed_json: dict[str, Any] | None

    # Content
    raw_text: str

    # Populated by the LLM extraction pipeline
    reviews: list[dict[str, Any]] | None
    extraction_model_version: str | None


def base_settings() -> dict[str, Any]:
    """Scrapy settings shared across all Final Scoring spiders.

    Reads from the central config so the same values that govern a
    development run also govern a CI rebuild.
    """

    cfg = get_settings()
    s = cfg.scraper

    return {
        "USER_AGENT": s.user_agent,
        "DOWNLOAD_DELAY": s.download_delay,
        "CONCURRENT_REQUESTS_PER_DOMAIN": s.concurrent_requests,
        "FEED_EXPORT_BATCH_ITEM_COUNT": s.export_batch_item_count,
        "FEEDS": {
            s.feed_uri: {
                "format": "jsonlines",
                "overwrite": False,
                "store_empty": False,
            },
        },
        "JOBDIR": str(s.jobdir),
        "ITEM_PIPELINES": {
            "final_scoring.scraping.pipeline_adapter.ScrapyLLMPipeline": 500,
        },
        # Robots.txt is respected by default. Overriding to True here
        # for explicitness; spiders should not toggle this off.
        "ROBOTSTXT_OBEY": True,
    }


class BaseReviewSpider(Spider):
    """Base class for all Final Scoring review spiders.

    Subclasses must set:

    * ``name`` — Scrapy spider name. Use the critic slug.
    * ``critic_slug`` — the canonical slug registered in
      ``data/overrides/critics.csv``. Usually equal to ``name``.
    * ``allowed_domains``, plus appropriate start URLs / sitemaps.
    * A ``parse_review`` method (or equivalent) that yields
      :class:`RawReviewItem` dicts.

    The shared item pipeline takes those raw items, runs LLM extraction,
    and writes the enriched items to the configured JSONL feed.
    """

    #: Critic slug — used to tag items with their source identity and to
    #: join against the critic registry at load time.
    critic_slug: str

    #: Language code spoken by this source. Override per spider.
    language: str = "en"

    custom_settings = base_settings()
