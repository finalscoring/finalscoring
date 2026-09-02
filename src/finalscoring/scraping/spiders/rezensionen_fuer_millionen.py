"""Spider for Udo Bartsch's blog "Rezensionen für Millionen".

The structural inverse of the Spiel des Jahres roundups: one post is one
critic's verdict on one game, in his own words. So the outlet is the blog
itself and it *is* known at scrape time — unlike a meta-source, where who
published a cited review is the extraction step's problem.

Blogger publishes every post through its feed API, preferred over the rendered
page for the same reason the WordPress REST API is on the other spider: the
entry's `content` is the post body, where the page around it is 260 kB of
theme. The feed also carries each post's labels, and Bartsch's labels are his
star rating — `**** solide`, `******* genial` — which is why a post without one
is not a review.
"""

import json
import re
from collections.abc import AsyncIterator, Iterator
from datetime import datetime
from typing import Any

from scrapy import Request
from scrapy.http.response import Response
from scrapy.http.response.text import TextResponse

from finalscoring.scraping.item import RawItem
from finalscoring.scraping.spider import ReviewSpider
from finalscoring.scraping.text import html_to_text

FEED_URL = "https://rezensionen-fuer-millionen.blogspot.com/feeds/posts/default"

# Blogger caps a page at 150 however many you ask for.
PAGE_SIZE = 150

_RATING_LABEL = re.compile(r"^\*+(\s|$)")


def _text(node: Any) -> str | None:
    """Blogger wraps every scalar as {"$t": value}."""
    return node.get("$t") if isinstance(node, dict) else None


def _published(entry: dict[str, Any]) -> datetime | None:
    stamp = _text(entry.get("published"))
    if not stamp:
        return None
    try:
        return datetime.fromisoformat(stamp)
    except ValueError:
        return None


def _thumbnail(entry: dict[str, Any]) -> str | None:
    """Media RSS puts the address in an attribute, not in Blogger's usual $t."""
    node = entry.get("media$thumbnail")
    return node.get("url") if isinstance(node, dict) else None


def _alternate_url(entry: dict[str, Any]) -> str | None:
    """The post's own address, as opposed to the feed's view of it."""
    for link in entry.get("link") or []:
        if link.get("rel") == "alternate" and link.get("href"):
            return link["href"]
    return None


def labels(entry: dict[str, Any]) -> list[str]:
    return [term for c in entry.get("category") or [] if (term := c.get("term"))]


def is_review(entry: dict[str, Any]) -> bool:
    """A star label is the rating, so its absence marks a non-review.

    The other labels are his recurring columns — "Gern gespielt", a monthly note
    on what his groups enjoyed, and "Vor 20 Jahren", a retrospective. Neither
    carries a verdict, and across all 876 reviews no post mixes a column label
    with a star. Four posts carry *two* stars: those cover two games at once.
    """
    return any(_RATING_LABEL.match(label) for label in labels(entry))


class RezensionenFuerMillionenSpider(ReviewSpider):
    name = "rezensionen-fuer-millionen"
    allowed_domains = ("rezensionen-fuer-millionen.blogspot.com",)

    # One author, one blog — so unlike the roundups, both are known up front.
    outlet_slug = "rezensionen-fuer-millionen"
    language = "de"  # the feed carries no locale, and he writes only in German

    reviews_only = True

    async def start(self) -> AsyncIterator[Request]:
        yield self.feed_request(start_index=1)

    def feed_request(self, start_index: int) -> Request:
        url = f"{FEED_URL}?alt=json&max-results={PAGE_SIZE}&start-index={start_index}"
        # dont_filter for the same reason sitemaps are exempt from the dupefilter:
        # an index page is not content, and JOBDIR would otherwise make every run
        # after the first do nothing at all.
        return Request(url, callback=self.parse_feed, dont_filter=True)

    def parse_feed(self, response: Response) -> Iterator[RawItem | Request]:
        if not isinstance(response, TextResponse):
            self.logger.error("Non-text feed response from %s", response.url)
            return

        try:
            feed = json.loads(response.text)["feed"]
        except ValueError, KeyError:
            self.logger.exception("Unparseable feed at %s", response.url)
            return

        entries = feed.get("entry") or []
        site_name = _text(feed.get("title"))
        skipped = 0

        for entry in entries:
            if self.reviews_only and not is_review(entry):
                skipped += 1
                continue
            item = self.item_from_entry(entry, site_name)
            if item is not None:
                yield item

        start_index = int(_text(feed.get("openSearch$startIndex")) or 1)
        total = int(_text(feed.get("openSearch$totalResults")) or 0)
        self.logger.info(
            "feed %d-%d of %d: %d posts, %d not reviews",
            start_index,
            start_index + len(entries) - 1,
            total,
            len(entries),
            skipped,
        )

        next_index = start_index + len(entries)
        if entries and next_index <= total:
            yield self.feed_request(next_index)

    def item_from_entry(self, entry: dict[str, Any], site_name: str | None) -> RawItem | None:
        url = _alternate_url(entry)
        if not url:
            self.logger.warning("Feed entry without a post url: %s", _text(entry.get("title")))
            return None

        content_html = _text(entry.get("content")) or ""
        raw_text = html_to_text(content_html)
        if not raw_text:
            self.logger.warning("Empty post body at %s", url)
            return None

        return RawItem(
            url=url,
            spider_slug=self.name,
            raw_text=raw_text,
            raw_html=content_html,
            title=_text(entry.get("title")),
            published_at=_published(entry),
            language=self.language,
            image_url=_thumbnail(entry),
            tags=labels(entry),
            outlet_slug=self.outlet_slug,
            og_site_name=site_name,
            extra={"blogger_entry": entry},
        )
