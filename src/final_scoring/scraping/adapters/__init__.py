"""Non-Scrapy ingestion adapters.

Some sources are easier to ingest via direct API or RSS calls than via
a full Scrapy spider. Those live here and follow the same convention:
produce :class:`RawReviewItem` records that the LLM extraction pipeline
can process identically to spider output.

Placeholder for now; populated in Phase 2 when adding text RSS sources.
"""
