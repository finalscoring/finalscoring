"""A dupefilter that never remembers sitemap requests.

RFPDupeFilter persists fingerprints across crawls via JOBDIR, so a sitemap's
entry points would be filtered as permanent duplicates after the first
successful crawl — the spider would do nothing on every later invocation. The
pages a sitemap lists should still be deduped; the sitemap itself should not.
"""

from scrapy.dupefilters import RFPDupeFilter
from scrapy.http import Request

# Scrapy's own SitemapSpider uses this exact suffix check to decide whether a
# response is a sitemap (scrapy.spiders.sitemap._get_sitemap_body).
_SITEMAP_SUFFIXES = (".xml", ".xml.gz")


class SitemapAwareDupeFilter(RFPDupeFilter):
    def request_seen(self, request: Request) -> bool:
        if request.url.endswith(_SITEMAP_SUFFIXES):
            return False
        return super().request_seen(request)
