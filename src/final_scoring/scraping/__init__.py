"""Scrapy-based ingestion layer.

One spider per critic source. The base settings, item pipeline wiring,
and adapter conventions are shared; per-source quirks live in each
spider subclass under ``spiders/``.

The Final Scoring ingestion strategy: be broad about sources, weight by
tier rather than gatekeep. New critics are added by writing a spider
that produces raw items matching the schema this package expects, then
registering the critic in ``data/overrides/critics.csv``.
"""

from final_scoring.scraping.base import BaseReviewSpider, RawReviewItem

__all__ = ["BaseReviewSpider", "RawReviewItem"]
