"""Spider for Dan Thurot's "SPACE-BIFF!", a single-critic WordPress.com blog.

WordPress.com, not self-hosted WordPress: there is no `/wp-json/` (404), and
the public content API at public-api.wordpress.com disallows everything but
one share endpoint in its robots.txt — `ROBOTSTXT_OBEY` is fixed to True for
every spider in `scrapy_settings`, so that route is closed regardless of what
the API itself would allow. The rendered page is therefore the only source.

The site's own `sitemap.xml` is far stranger than "stale": it holds exactly
1001 of 1847 posts, all from mid-2019 onward, and nothing before. What covers
every post instead is the blog's own chronological pagination — follow "Older
Posts" from the front page and it terminates, by construction, at the first
post ever published. 185 pages times ~10 posts each accounts for all 1847.

Thurot writes prose verdicts, not a score of any kind — no graphic, no
microdata, nothing structured to gate on the way the other two single-critic
spiders do. What the theme does expose, only on the single-post template and
not on the paginated listing, is the post's categories and tags as plain
links. The site is a board game blog through and through — "Board Game" is
the category on 1674 of 1847 posts — but that category also covers his
podcast episodes, session diaries, year-end lists, and convention reports,
none of which is a verdict on one game. `reviews_only` excludes those
categories; it is a coarse cut; a handful of posts on either side of the line
have no consistent taxonomy in fifteen years of the blog for anything cleaner
to key on. Every category and tag on the page reaches the model regardless,
through `tags`, in case the cut is wrong on a given post.
"""

import re
from collections.abc import AsyncIterator, Iterator
from datetime import datetime

from scrapy import Request, Spider
from scrapy.http.response import Response
from scrapy.http.response.text import TextResponse
from scrapy.settings import BaseSettings

from finalscoring.scraping.item import RawItem
from finalscoring.scraping.scrapy_settings import scrapy_settings
from finalscoring.scraping.text import html_to_text

BASE_URL = "https://spacebiff.com/"

# Columns and roundups, not a verdict on one game.
NON_REVIEW_CATEGORIES = frozenset(
    {
        "podcast",
        "game-diary",
        "lists",
        "index",
        "convention",
        "home-life",
        "how-to",
        "impressions",
        "holiday-special",
        "retrospective",
    }
)

_CATEGORY_SLUG = re.compile(r"/category/([^/]+)/?$")


def category_slug(href: str | None) -> str | None:
    match = _CATEGORY_SLUG.search(href or "")
    return match.group(1) if match else None


def is_review(category_slugs: set[str]) -> bool:
    """Board Game, and none of his recurring non-review columns."""
    return "board-game" in category_slugs and not (category_slugs & NON_REVIEW_CATEGORIES)


def published_at(timestamp: str | None) -> datetime | None:
    if not timestamp:
        return None
    try:
        return datetime.fromisoformat(timestamp)
    except ValueError:
        return None


class SpaceBiffSpider(Spider):
    name = "space-biff"
    allowed_domains = ("spacebiff.com",)

    outlet_slug = "space-biff"
    language = "en"  # he writes only in English

    reviews_only = True

    @classmethod
    def update_settings(cls, settings: BaseSettings) -> None:
        # Not custom_settings: that would read the environment at import time.
        super().update_settings(settings)
        settings.setdict(scrapy_settings(cls.name), priority="spider")

    async def start(self) -> AsyncIterator[Request]:
        yield self.index_request(BASE_URL)

    def index_request(self, url: str) -> Request:
        # dont_filter for the same reason sitemaps are exempt from the
        # dupefilter: an index page is not content, and JOBDIR would
        # otherwise make every run after the first do nothing at all.
        return Request(url, callback=self.parse_index, dont_filter=True)

    def parse_index(self, response: Response) -> Iterator[Request]:
        if not isinstance(response, TextResponse):
            self.logger.error("Non-text index response from %s", response.url)
            return

        hrefs = response.xpath('//div[@id="content"]//h2[@class="post-title"]/a/@href').getall()
        for href in hrefs:
            yield response.follow(href, callback=self.parse_review)

        older = response.xpath('//div[contains(@class, "nav-previous")]/a/@href').get()
        if older:
            yield self.index_request(older)

    # Wrapped, never bare: a pydantic model is iterable, so Scrapy would shred
    # a returned RawItem into (name, value) pairs.
    def parse_review(self, response: Response) -> tuple[RawItem] | None:
        if not isinstance(response, TextResponse):
            self.logger.error("Non-text response from %s", response.url)
            return None

        category_links = response.xpath('//div[@class="post-utility"]//a[@rel="category tag"]')
        categories = [c.strip() for c in category_links.xpath("text()").getall()]
        category_slugs = {
            slug for href in category_links.xpath("@href").getall() if (slug := category_slug(href))
        }
        tag_names = [
            t.strip()
            for t in response.xpath('//div[@class="post-utility"]//a[@rel="tag"]/text()').getall()
        ]

        if self.reviews_only and not is_review(category_slugs):
            self.logger.debug("Not a single-game review (%s): %s", categories, response.url)
            return None

        content_html = response.xpath("//div[@class='entry clear-block']").get() or ""
        raw_text = html_to_text(content_html)
        if not raw_text:
            self.logger.warning("No article content at %s", response.url)
            return None

        image_url = response.xpath("//meta[@property='og:image']/@content").get()

        return (
            RawItem(
                url=response.url,
                spider_slug=self.name,
                raw_text=raw_text,
                raw_html=content_html,
                title=(
                    response.xpath('//h1[@class="single-title"]/text()').get()
                    or response.xpath("//title/text()").get()
                ),
                published_at=published_at(
                    response.xpath("//meta[@property='article:published_time']/@content").get()
                ),
                language=self.language,
                image_url=response.urljoin(image_url) if image_url else None,
                tags=categories + tag_names,
                outlet_slug=self.outlet_slug,
                og_site_name=response.xpath("//meta[@property='og:site_name']/@content").get(),
                extra={"categories": sorted(category_slugs)} if category_slugs else {},
            ),
        )
