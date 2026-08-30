"""Run a spider by hand: `uv run python -m finalscoring.scraping <name> [-a key=value ...]`.

Crawls are meant to be watched the first few times — run this, read the log,
look at what lands in the results directory. The build pipeline (Phase F) will
drive spiders its own way.

Spiders that read their targets from a file — `luding` — take the path as a
spider argument, the same `-a key=value` Scrapy's own CLI uses:

    python -m finalscoring.scraping luding -a files=~/path/to/luding_GameItem.jl
"""

import sys

from scrapy.crawler import CrawlerProcess

from finalscoring.scraping.spiders import (
    GamesWePlaySpider,
    LudingSpider,
    RezensionenFuerMillionenSpider,
    SpaceBiffSpider,
    SpielDesJahresSpider,
)

SPIDERS = {
    spider.name: spider
    for spider in (
        GamesWePlaySpider,
        SpaceBiffSpider,
        SpielDesJahresSpider,
        RezensionenFuerMillionenSpider,
        LudingSpider,
    )
}

USAGE = f"usage: python -m finalscoring.scraping {{{'|'.join(SPIDERS)}}} [-a key=value ...]"


def spider_args(tokens: list[str]) -> dict[str, str]:
    """Parse `-a key=value` pairs (the bare `-a` separators optional)."""
    kwargs: dict[str, str] = {}
    for token in tokens:
        if token == "-a":
            continue
        key, sep, value = token.partition("=")
        if not sep:
            raise ValueError(f"spider arguments look like key=value, got {token!r}")
        kwargs[key] = value
    return kwargs


def main(argv: list[str]) -> int:
    if not argv or argv[0] not in SPIDERS:
        print(USAGE)
        return 2

    try:
        kwargs = spider_args(argv[1:])
    except ValueError as err:
        print(err)
        return 2

    process = CrawlerProcess()
    process.crawl(SPIDERS[argv[0]], **kwargs)
    process.start()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
