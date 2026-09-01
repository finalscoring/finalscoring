"""Base classes shared by every Final Scoring spider.

`ReviewSpider` carries the one thing all spiders have in common: crawler
configuration derived from the project `Settings` object. It goes through
`update_settings` rather than `custom_settings` because `custom_settings` is
read at import time, before the environment the settings come from is in scope.

`ReviewSitemapSpider` is the same, for the spiders that discover their targets
from a sitemap. `update_settings` lives only on `Spider`, so the extra base adds
nothing to the method-resolution order that would shadow `SitemapSpider`.

Two conventions every parse method follows, kept here so they read as
deliberate rather than repeated:

- Guard the callback with ``isinstance(response, TextResponse)``. Scrapy types a
  callback argument as `Response`; the `isinstance` check both handles the rare
  non-text response and narrows the type for the parsing that follows.
- Return a `RawItem` wrapped in a one-tuple, never bare: a pydantic model is
  iterable, and Scrapy would otherwise shred it into ``(name, value)`` pairs.
"""

from scrapy import Spider
from scrapy.settings import BaseSettings
from scrapy.spiders.sitemap import SitemapSpider

from finalscoring.scraping.scrapy_settings import scrapy_settings


class ReviewSpider(Spider):
    @classmethod
    def update_settings(cls, settings: BaseSettings) -> None:
        super().update_settings(settings)
        settings.setdict(scrapy_settings(cls.name), priority="spider")


class ReviewSitemapSpider(ReviewSpider, SitemapSpider): ...
