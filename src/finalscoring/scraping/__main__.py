"""Run a spider by hand: `uv run python -m finalscoring.scraping <name>`.

Crawls are meant to be watched the first few times — run this, read the log,
look at what lands in the results directory. The build pipeline (Phase F) will
drive spiders its own way.
"""

import sys

from scrapy.crawler import CrawlerProcess

from finalscoring.scraping.spiders import (
    GamesWePlaySpider,
    RezensionenFuerMillionenSpider,
    ShutUpAndSitDownSpider,
    SpaceBiffSpider,
    SpielDesJahresSpider,
)

SPIDERS = {
    spider.name: spider
    for spider in (
        GamesWePlaySpider,
        ShutUpAndSitDownSpider,
        SpaceBiffSpider,
        SpielDesJahresSpider,
        RezensionenFuerMillionenSpider,
    )
}


def main(argv: list[str]) -> int:
    if len(argv) != 1 or argv[0] not in SPIDERS:
        print(f"usage: python -m finalscoring.scraping {{{'|'.join(SPIDERS)}}}")
        return 2

    process = CrawlerProcess()
    process.crawl(SPIDERS[argv[0]])
    process.start()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
