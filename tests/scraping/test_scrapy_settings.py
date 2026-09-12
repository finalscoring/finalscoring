"""Tests for the Scrapy settings derived from the project config."""

from pathlib import Path

from finalscoring.scraping.dupefilter import SitemapAwareDupeFilter
from finalscoring.scraping.scrapy_settings import (
    FEED_TEMPLATE,
    THROTTLE_HTTP_CODES,
    scrapy_settings,
)
from finalscoring.settings import Settings

SETTINGS = Settings(
    llm_base_url="http://localhost:11434/v1",
    llm_model="llama3.2",
    llm_api_key="not-needed",  # pragma: allowlist secret
    llm_timeout=120.0,
    llm_max_attempts=3,
    llm_context="html",
    scraper_user_agent="TestBot/1.0 (+https://example.com/)",
    scraper_delay=2.5,
    scraper_concurrency=8,
    scraping_dir=Path("/data/out"),
    extraction_dir=Path("/data/extract"),
    jobs_dir=Path("/data/state"),
    db_path=Path("/data/fs.db"),
)


def test_settings_flow_through_from_the_config_object():
    s = scrapy_settings("spiel-des-jahres", SETTINGS)

    assert s["USER_AGENT"] == "TestBot/1.0 (+https://example.com/)"
    assert s["DOWNLOAD_DELAY"] == 2.5
    assert s["CONCURRENT_REQUESTS_PER_DOMAIN"] == 8


def test_robots_txt_is_obeyed():
    """Scrapy defaults this to False outside a generated project. We do not."""
    assert scrapy_settings("spiel-des-jahres", SETTINGS)["ROBOTSTXT_OBEY"] is True


def test_job_directory_is_per_spider():
    """Two spiders sharing a JOBDIR would read each other's request state."""
    first = scrapy_settings("spiel-des-jahres", SETTINGS)["JOBDIR"]
    second = scrapy_settings("other-source", SETTINGS)["JOBDIR"]

    assert first == str(Path("/data/state/spiel-des-jahres"))
    assert first != second


def test_feed_writes_json_lines_into_the_scraping_directory():
    feeds = scrapy_settings("spiel-des-jahres", SETTINGS)["FEEDS"]

    ((uri, options),) = feeds.items()
    assert uri == str(Path("/data/out") / FEED_TEMPLATE)
    assert options["format"] == "jsonlines"


def test_feed_never_overwrites_an_earlier_crawl():
    """Output is an intermediate artifact, but losing a finished crawl is not free."""
    feeds = scrapy_settings("spiel-des-jahres", SETTINGS)["FEEDS"]

    (options,) = feeds.values()
    assert options["overwrite"] is False


def test_settings_fall_back_to_the_environment(monkeypatch):
    monkeypatch.setenv("FS_SCRAPER_DELAY", "3.5")

    assert scrapy_settings("spiel-des-jahres")["DOWNLOAD_DELAY"] == 3.5


def test_sitemap_aware_dupefilter_is_used():
    """Otherwise JOBDIR fingerprints the sitemap forever after the first crawl."""
    assert (
        scrapy_settings("spiel-des-jahres", SETTINGS)["DUPEFILTER_CLASS"] is SitemapAwareDupeFilter
    )


def test_quiet_log_formatter_replaces_the_default():
    assert scrapy_settings("spiel-des-jahres", SETTINGS)["LOG_FORMATTER"] == (
        "scrapy_extensions.QuietLogFormatter"
    )


def test_retry_middleware_is_replaced_with_the_delayed_variant():
    middlewares = scrapy_settings("spiel-des-jahres", SETTINGS)["DOWNLOADER_MIDDLEWARES"]

    assert middlewares["scrapy.downloadermiddlewares.retry.RetryMiddleware"] is None
    assert middlewares["scrapy_extensions.DelayedRetryMiddleware"] == 550


def test_delayed_retry_backs_off_on_rate_limit_codes():
    s = scrapy_settings("spiel-des-jahres", SETTINGS)

    assert s["DELAYED_RETRY_HTTP_CODES"] == THROTTLE_HTTP_CODES
    assert s["DELAYED_RETRY_BACKOFF"] is True


def test_autothrottle_extension_is_replaced_with_the_nicer_variant():
    extensions = scrapy_settings("spiel-des-jahres", SETTINGS)["EXTENSIONS"]

    assert extensions["scrapy.extensions.throttle.AutoThrottle"] is None
    assert extensions["scrapy_extensions.NicerAutoThrottle"] == 0


def test_autothrottle_is_enabled_and_backs_off_on_rate_limit_codes():
    s = scrapy_settings("spiel-des-jahres", SETTINGS)

    assert s["AUTOTHROTTLE_ENABLED"] is True
    assert s["AUTOTHROTTLE_HTTP_CODES"] == THROTTLE_HTTP_CODES
