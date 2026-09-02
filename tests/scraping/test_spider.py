"""Tests for the shared spider base classes."""

import pytest
from scrapy import Spider
from scrapy.settings import SETTINGS_PRIORITIES, Settings
from scrapy.spiders.sitemap import SitemapSpider

from finalscoring.scraping.spider import ReviewSitemapSpider, ReviewSpider
from finalscoring.scraping.spiders import (
    GamesWePlaySpider,
    Hall9000Spider,
    LudingSpider,
    MeepleMountainSpider,
    ReviewLinksSpider,
    RezensionenFuerMillionenSpider,
    ShutUpAndSitDownSpider,
    SpaceBiffSpider,
    SpielDesJahresSpider,
)

SPIDERS = (
    GamesWePlaySpider,
    Hall9000Spider,
    LudingSpider,
    MeepleMountainSpider,
    ReviewLinksSpider,
    RezensionenFuerMillionenSpider,
    ShutUpAndSitDownSpider,
    SpaceBiffSpider,
    SpielDesJahresSpider,
)


class _Plain(ReviewSpider):
    name = "test-plain-source"


class _Sitemap(ReviewSitemapSpider):
    name = "test-sitemap-source"


@pytest.mark.parametrize("base", [_Plain, _Sitemap])
def test_the_base_applies_project_config_at_spider_priority(base, monkeypatch):
    monkeypatch.setenv("FS_SCRAPER_DELAY", "6.5")
    settings = Settings()

    base.update_settings(settings)

    assert settings["DOWNLOAD_DELAY"] == 6.5
    assert settings["JOBDIR"].endswith(base.name)
    assert settings.getpriority("DOWNLOAD_DELAY") == SETTINGS_PRIORITIES["spider"]


def test_sitemap_base_resolves_update_settings_to_review_spider():
    """The extra base must not shadow the config hook."""
    assert ReviewSitemapSpider.update_settings.__func__ is ReviewSpider.update_settings.__func__


def test_sitemap_base_keeps_the_sitemap_machinery():
    assert ReviewSitemapSpider.__mro__[:4] == (
        ReviewSitemapSpider,
        ReviewSpider,
        SitemapSpider,
        Spider,
    )
    assert hasattr(ReviewSitemapSpider, "_parse_sitemap")


@pytest.mark.parametrize("spider_cls", SPIDERS)
def test_every_spider_builds_on_the_shared_base(spider_cls):
    assert issubclass(spider_cls, ReviewSpider)


@pytest.mark.parametrize("spider_cls", SPIDERS)
def test_no_spider_redefines_the_config_hook(spider_cls):
    """The whole point of the base: update_settings lives in exactly one place."""
    assert "update_settings" not in spider_cls.__dict__
