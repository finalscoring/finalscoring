"""Spider for "Shut Up & Sit Down", a multi-writer English review site.

Self-hosted WordPress, but `/wp-json/` is a Cloudflare 403 for every user
agent tried, so — as with space-biff — the rendered page is the only source.

Discovery does not use the sitemap. Review slugs are inconsistent (`review-*`,
`miniatures-game-review-*`, `board-game-review-*`, and punning titles with no
"review" in them at all), so a `SitemapSpider` rule would have to match every
one of the ~870 posts and filter by category — ~870 fetches for ~220 reviews.
The `/category/reviews/` archive lists exactly those ~220, newest first, ten to
a page over 22 pages, so the spider walks that instead and warns if it stops
before the last page the pager advertises.

The archive's newest entry is 7 May 2020 (Gaslands: Refueled and Dropzone
Commander); every review-slugged post in the sitemap stops on the same day.
Shut Up & Sit Down moved to video reviews after that, so this is effectively a
closed back catalogue of ~220 reviews: a re-crawl walks the 22 list pages to
discover nothing new, and the newest-first order buys no incremental benefit
the way it does for the other spiders.

The reviews are conversational prose with no score, graphic or structured
verdict of any kind — nothing to gate on but the category, which also carries
the odd buyer's guide and awards round-up. That is a coarse cut, matching
space-biff; every category and tag on the page reaches the model through `tags`
regardless.
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

BASE_URL = "https://www.shutupandsitdown.com/"
REVIEWS_URL = f"{BASE_URL}category/reviews/"

_CATEGORY_SLUG = re.compile(r"/category/([^/]+)/?$")
_PAGE_NUMBER = re.compile(r"/page/(\d+)/?$")
# "March 17, 2015" — the entry-date span; parsed without leaning on the locale.
_DATE = re.compile(r"([A-Za-z]+)\s+(\d{1,2}),\s+(\d{4})")
_MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}


def _cls(name: str) -> str:
    """An XPath predicate matching one class token, tolerating others beside it."""
    return f"contains(concat(' ', normalize-space(@class), ' '), ' {name} ')"


def category_slug(href: str | None) -> str | None:
    match = _CATEGORY_SLUG.search(href or "")
    return match.group(1) if match else None


def page_number(url: str | None) -> int | None:
    match = _PAGE_NUMBER.search(url or "")
    return int(match.group(1)) if match else None


def published_at(text: str | None) -> datetime | None:
    """ "March 17, 2015" -> a datetime, month names matched explicitly."""
    match = _DATE.search(text or "")
    if not match:
        return None
    month = _MONTHS.get(match.group(1).lower())
    if month is None:
        return None
    try:
        return datetime(int(match.group(3)), month, int(match.group(2)))
    except ValueError:
        return None


class ShutUpAndSitDownSpider(Spider):
    name = "shut-up-and-sit-down"
    allowed_domains = ("shutupandsitdown.com",)

    outlet_slug = "shut-up-and-sit-down"
    language = "en"  # the site is English-only

    reviews_only = True

    @classmethod
    def update_settings(cls, settings: BaseSettings) -> None:
        # Not custom_settings: that would read the environment at import time.
        super().update_settings(settings)
        settings.setdict(scrapy_settings(cls.name), priority="spider")

    async def start(self) -> AsyncIterator[Request]:
        yield self.list_request(REVIEWS_URL)

    def list_request(self, url: str) -> Request:
        # dont_filter for the same reason sitemaps are exempt from the dupefilter:
        # a list page is not content, and JOBDIR would otherwise make every run
        # after the first do nothing at all.
        return Request(url, callback=self.parse_list, dont_filter=True)

    def parse_list(self, response: Response) -> Iterator[Request]:
        if not isinstance(response, TextResponse):
            self.logger.error("Non-text list response from %s", response.url)
            return

        hrefs = response.xpath(f"//h2[{_cls('entry-title')}]/a/@href").getall()
        for href in hrefs:
            yield response.follow(href, callback=self.parse_review)

        pager = response.xpath(f"//div[{_cls('nav-links')}]//a[{_cls('page-numbers')}]/@href")
        last_page = max((page_number(u) or 0 for u in pager.getall()), default=1)
        this_page = page_number(response.url) or 1
        next_url = response.xpath(f"//div[{_cls('nav-links')}]//a[{_cls('next')}]/@href").get()

        if not hrefs:
            self.logger.warning("list page %s yielded no reviews", response.url)
        if next_url:
            yield self.list_request(response.urljoin(next_url))
        elif this_page < last_page:
            self.logger.warning("review walk stopped at page %d of %d", this_page, last_page)

    # Wrapped, never bare: a pydantic model is iterable, so Scrapy would shred
    # a returned RawItem into (name, value) pairs.
    def parse_review(self, response: Response) -> tuple[RawItem] | None:
        if not isinstance(response, TextResponse):
            self.logger.error("Non-text response from %s", response.url)
            return None

        content = response.xpath(f"//div[{_cls('entry-content')}]")
        if not content:
            self.logger.warning("No article content at %s", response.url)
            return None

        category_links = content.xpath(f"./span[{_cls('meta-category')}]//a")
        categories = [c.strip() for c in category_links.xpath("text()").getall() if c.strip()]
        category_slugs = {
            slug for href in category_links.xpath("@href").getall() if (slug := category_slug(href))
        }
        if self.reviews_only and "reviews" not in category_slugs:
            self.logger.debug("Not in the reviews category (%s): %s", categories, response.url)
            return None

        # The entry-date / author / category / comment spans and the tag list are
        # the theme's meta strip, injected at the top of entry-content; drop them.
        body_html = "".join(
            content.xpath(
                f"./node()[not(self::span) and not(self::div[{_cls('meta-tags')}])]"
            ).getall()
        )
        raw_text = html_to_text(body_html)
        if not raw_text:
            self.logger.warning("No article text at %s", response.url)
            return None

        fun_tags = response.xpath(f"normalize-space(//div[{_cls('fun-tags')}])").get() or None
        meta_tags = [
            t.strip()
            for t in content.xpath(f"./div[{_cls('meta-tags')}]//a/text()").getall()
            if t.strip()
        ]
        author = content.xpath(f"./span[{_cls('author')}]/text()").get()
        image_url = response.xpath("//meta[@property='og:image']/@content").get()

        return (
            RawItem(
                url=response.url,
                spider_slug=self.name,
                raw_text=raw_text,
                raw_html=body_html,
                title=self.title(response),
                description=response.xpath("//meta[@name='description']/@content").get(),
                published_at=published_at(
                    content.xpath(f"./span[{_cls('entry-date')}]/text()").get()
                ),
                language=self.language,
                locale=response.xpath("//meta[@property='og:locale']/@content").get(),
                image_url=image_url,
                tags=meta_tags + categories + ([fun_tags] if fun_tags else []),
                outlet_slug=self.outlet_slug,
                og_site_name=response.xpath("//meta[@property='og:site_name']/@content").get(),
                extra=self.extra(author, fun_tags, category_slugs),
            ),
        )

    def title(self, response: TextResponse) -> str | None:
        heading = response.xpath(f"normalize-space(//h1[{_cls('entry-title')}])").get()
        if heading:
            return heading
        # og:title and <title> both carry a " - Shut Up & Sit Down" suffix.
        og_title = response.xpath("//meta[@property='og:title']/@content").get() or ""
        return og_title.rsplit(" - Shut Up", 1)[0].strip() or None

    def extra(
        self, author: str | None, fun_tags: str | None, category_slugs: set[str]
    ) -> dict[str, object]:
        collected: dict[str, object] = {}
        # Migrated posts credit "webdeveloper"; the real byline is in the prose.
        if author and author != "webdeveloper":
            collected["author"] = author
        if fun_tags:
            collected["fun_tags"] = fun_tags
        if category_slugs:
            collected["categories"] = sorted(category_slugs)
        return collected
