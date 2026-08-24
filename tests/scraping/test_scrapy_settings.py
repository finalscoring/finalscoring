"""Tests for the Scrapy settings derived from the project config."""

from pathlib import Path

from finalscoring.scraping.scrapy_settings import (
    FEED_TEMPLATE,
    scrapy_settings,
)
from finalscoring.settings import Settings

SETTINGS = Settings(
    llm_base_url="http://localhost:11434/v1",
    llm_model="llama3.2",
    scraper_user_agent="TestBot/1.0 (+https://example.com/)",
    scraper_delay=2.5,
    scraper_concurrency=8,
    results_dir=Path("/data/out"),
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


def test_feed_writes_json_lines_into_the_results_directory():
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
