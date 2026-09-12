"""Scrapy configuration derived from the project settings object.

Spiders take these through `custom_settings` so crawler configuration has one
source — the environment, via `Settings` — rather than `os.getenv` calls
scattered across each spider.
"""

from typing import Any

from finalscoring.scraping.dupefilter import SitemapAwareDupeFilter
from finalscoring.settings import Settings, load_settings

# Lets `scrapy check` (spider contracts) discover the spiders; the project
# otherwise runs them through `python -m finalscoring.scraping`, not the CLI.
SPIDER_MODULES = ["finalscoring.scraping.spiders"]

# `@populated` / `@raw_item` — see finalscoring.scraping.contracts.
SPIDER_CONTRACTS = {
    "finalscoring.scraping.contracts.PopulatedContract": 10,
    "finalscoring.scraping.contracts.RawItemContract": 10,
}

# So an interrupted crawl leaves its completed batches behind.
FEED_BATCH_ITEM_COUNT = 10_000

FEED_TEMPLATE = "%(name)s-%(time)s-%(batch_id)05d.jl"

# Rate-limit signals: back off harder on these than plain AutoThrottle latency
# tuning would, since a 429/503 means the site is asking us to slow down, not
# just responding slowly.
THROTTLE_HTTP_CODES = (429, 503)

LOG_FORMATTER = "scrapy_extensions.QuietLogFormatter"

DOWNLOADER_MIDDLEWARES = {
    # Replaces the default RetryMiddleware slot (550) so rate-limit responses
    # are retried after a backoff delay instead of immediately.
    "scrapy.downloadermiddlewares.retry.RetryMiddleware": None,
    "scrapy_extensions.DelayedRetryMiddleware": 550,
}

EXTENSIONS = {
    # Replaces the default AutoThrottle extension so it also backs off on
    # THROTTLE_HTTP_CODES, not just response latency.
    "scrapy.extensions.throttle.AutoThrottle": None,
    "scrapy_extensions.NicerAutoThrottle": 0,
}


def scrapy_settings(spider_name: str, settings: Settings | None = None) -> dict[str, Any]:
    """Build the Scrapy settings for one spider.

    The job directory is per spider: Scrapy stores the pending-request queue
    and seen-request fingerprints there, and two spiders sharing a directory
    would read each other's state.
    """
    settings = settings if settings is not None else load_settings()
    return {
        "USER_AGENT": settings.scraper_user_agent,
        "ROBOTSTXT_OBEY": True,
        "DOWNLOAD_DELAY": settings.scraper_delay,
        "CONCURRENT_REQUESTS_PER_DOMAIN": settings.scraper_concurrency,
        "JOBDIR": str(settings.jobs_dir / spider_name),
        "DUPEFILTER_CLASS": SitemapAwareDupeFilter,
        "FEED_EXPORT_BATCH_ITEM_COUNT": FEED_BATCH_ITEM_COUNT,
        "FEEDS": {
            str(settings.scraping_dir / FEED_TEMPLATE): {
                "format": "jsonlines",
                "overwrite": False,
                "store_empty": False,
            },
        },
        "LOG_FORMATTER": LOG_FORMATTER,
        "DOWNLOADER_MIDDLEWARES": DOWNLOADER_MIDDLEWARES,
        "DELAYED_RETRY_HTTP_CODES": THROTTLE_HTTP_CODES,
        "DELAYED_RETRY_BACKOFF": True,
        "AUTOTHROTTLE_ENABLED": True,
        "EXTENSIONS": EXTENSIONS,
        "AUTOTHROTTLE_HTTP_CODES": THROTTLE_HTTP_CODES,
    }
