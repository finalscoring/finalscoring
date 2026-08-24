"""Scrapy configuration derived from the project settings object.

Spiders take these through `custom_settings` so crawler configuration has one
source — the environment, via `Settings` — rather than `os.getenv` calls
scattered across each spider.
"""

from typing import Any

from finalscoring.settings import Settings, load_settings

# Batch the feed so a long crawl does not accumulate into one enormous file,
# and so an interrupted run leaves its completed batches behind.
FEED_BATCH_ITEM_COUNT = 10_000

# %(name)s is the spider's name, %(time)s the crawl start, %(batch_id)s the
# batch counter — all substituted by Scrapy. This is the filename convention
# `docs/DECISIONS_OPEN.md` left to the first spider.
FEED_TEMPLATE = "%(name)s-%(time)s-%(batch_id)05d.jl"


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
        "FEED_EXPORT_BATCH_ITEM_COUNT": FEED_BATCH_ITEM_COUNT,
        "FEEDS": {
            str(settings.results_dir / FEED_TEMPLATE): {
                "format": "jsonlines",
                "overwrite": False,
                "store_empty": False,
            },
        },
    }
