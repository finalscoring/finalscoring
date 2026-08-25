"""Tests for the sitemap-aware dupefilter."""

from scrapy.http import Request

from finalscoring.scraping.dupefilter import SitemapAwareDupeFilter


def _seen(url: str) -> bool:
    return SitemapAwareDupeFilter().request_seen(Request(url))


def test_sitemap_urls_are_never_seen():
    """Without this, JOBDIR would fingerprint the sitemap forever, and every
    crawl after the first would filter it out and do nothing."""
    dupefilter = SitemapAwareDupeFilter()

    assert dupefilter.request_seen(Request("https://example.com/sitemap.xml")) is False
    assert dupefilter.request_seen(Request("https://example.com/sitemap.xml")) is False


def test_gzipped_sitemap_urls_are_never_seen():
    assert _seen("https://example.com/sitemap.xml.gz") is False
    assert _seen("https://example.com/sitemap.xml.gz") is False


def test_other_urls_are_still_deduped():
    """Pages a sitemap lists should not be re-fetched every crawl."""
    dupefilter = SitemapAwareDupeFilter()
    request = Request("https://example.com/kritikenrundschau-beispiel/")

    assert dupefilter.request_seen(request) is False
    assert dupefilter.request_seen(request) is True


def test_only_the_suffix_matters_not_the_path():
    assert _seen("https://example.com/post-sitemap.xml") is False
    assert _seen("https://example.com/sitemaps/index.xml") is False
