"""Spider for Harald Schrapers' site "games we play".

A second single-critic source, and a third publishing platform: no CMS at all,
just hand-written XHTML served as ISO-8859-1, one file per game. No feed, no
REST API. Between this, the WordPress roundups and the Blogger feed, nothing
shared can quietly assume one platform.

Two things about this site drive the design.

**Its sitemap is stale.** It lists 1081 pages and omits about 200, including
every review from the last couple of years — `dewan.html` among them, which is
the one Spiel des Jahres cites. The yearly archives (`index.html`,
`index00.html` … ) list 844, and miss 367 the sitemap has. Neither enumerates
the site, so the spider reads both and lets the dupefilter merge them.

**He rates in up to six ways at once,** and no single one of them is present
across the archive: a graphic whose *filename* is the score, schema.org
microdata out of ten, a signature line pairing a number with a die face and a
trend arrow, a difficulty grade carrying an age recommendation, a packaging
mark, and a "TOPspiel" badge. Most live in markup the plain text throws away —
a filename, an `alt` attribute — so all of them are collected here and phrased
into `tags`, which is what actually reaches the model. Nothing is reconciled or
converted: which of his scales becomes a score is a load-step decision, and the
extractor is meant to weigh them itself.
"""

import re
from collections.abc import AsyncIterator, Iterator
from html import unescape
from typing import Any

from scrapy import Request
from scrapy.http.response import Response
from scrapy.http.response.text import TextResponse
from scrapy.settings import BaseSettings
from scrapy.spiders.sitemap import SitemapSpider

from finalscoring.scraping.item import RawItem
from finalscoring.scraping.scrapy_settings import scrapy_settings
from finalscoring.scraping.text import html_to_text

BASE_URL = "https://gamesweplay.de/"

# The graphic is the verdict, and its name is the number.
RATING_POINTS = {
    "null": 0,
    "eins": 1,
    "zwei": 2,
    "drei": 3,
    "vier": 4,
    "fuenf": 5,
    "sechs": 6,
}
RATING_MAX = 6

_RATING_IMAGE = re.compile(rf"({'|'.join(RATING_POINTS)})\.(?:png|gif)$", re.IGNORECASE)
_INDEX_PAGE = re.compile(r"^index\d*\.html?$", re.IGNORECASE)
# "Rating: 8/10 ⚄ ⇗" — number, die face, trend arrow, on the newest reviews only.
_SIGNATURE = re.compile(r"Rating:\s*\d+\s*/\s*\d+[^\n<]{0,20}")
_FILLED, _EMPTY = "◼", "◻"  # ◼ ◻ — the difficulty squares


def rating_from_image(src: str | None) -> int | None:
    """5 from ".../fuenf.png". None when the image is not a rating graphic."""
    if not src:
        return None
    match = _RATING_IMAGE.search(src.strip())
    return RATING_POINTS[match.group(1).lower()] if match else None


def _int(value: str | None) -> int | None:
    try:
        return int(value) if value is not None else None
    except ValueError:
        return None


class GamesWePlaySpider(SitemapSpider):
    name = "games-we-play"
    allowed_domains = ("gamesweplay.de",)

    sitemap_urls = (f"{BASE_URL}sitemap.xml",)
    # Every review is <game>.html; the sitemap also lists a spreadsheet and a
    # handful of index pages, which the rating graphic weeds out later.
    sitemap_rules = ((r"\.html?$", "parse_review"),)

    outlet_slug = "games-we-play"
    # Nowhere in the markup; the masthead is an image whose alt text says it.
    site_name = "games we play"
    language = "de"

    reviews_only = True

    @classmethod
    def update_settings(cls, settings: BaseSettings) -> None:
        # Not custom_settings: that would read the environment at import time.
        super().update_settings(settings)
        settings.setdict(scrapy_settings(cls.name), priority="spider")

    async def start(self) -> AsyncIterator[Request]:
        """The sitemap misses ~200 pages, so the archives are crawled as well."""
        async for request in super().start():
            yield request
        yield Request(f"{BASE_URL}index.html", callback=self.parse_index)

    def parse_index(self, response: Response) -> Iterator[Request]:
        """Yearly archives link on to each other; everything else is a candidate."""
        # Response, not TextResponse: that is what Scrapy promises a callback.
        if not isinstance(response, TextResponse):
            self.logger.error("Non-text index response from %s", response.url)
            return
        for href in response.xpath("//a/@href").getall():
            slug = href.rsplit("/", 1)[-1]
            if not slug.lower().endswith((".html", ".htm")):
                continue
            callback = self.parse_index if _INDEX_PAGE.match(slug) else self.parse_review
            yield response.follow(href, callback=callback)

    # Wrapped, never bare: a pydantic model is iterable, so Scrapy would shred
    # a returned RawItem into (name, value) pairs.
    def parse_review(self, response: Response) -> tuple[RawItem] | None:
        if not isinstance(response, TextResponse):
            self.logger.error("Non-text response from %s", response.url)
            return None

        ratings = self.ratings(response)
        if "graphic" not in ratings and self.reviews_only:
            self.logger.debug("No rating graphic, not a review: %s", response.url)
            return None

        article_html = (
            response.xpath("//div[@class='besprechung']").get()
            or response.xpath("//body").get()
            or ""
        )
        raw_text = html_to_text(article_html)
        if not raw_text:
            self.logger.warning("No article content at %s", response.url)
            return None

        image_url = response.xpath("//meta[@property='og:image']/@content").get()

        return (
            RawItem(
                url=response.url,
                spider_slug=self.name,
                raw_text=raw_text,
                raw_html=article_html,
                title=response.xpath("//title/text()").get(),
                language=self.language,
                # Relative on this site — "dewani.jpg", not an address.
                image_url=response.urljoin(image_url) if image_url else None,
                tags=self.rating_tags(ratings),
                outlet_slug=self.outlet_slug,
                og_site_name=self.site_name,
                extra={"ratings": ratings} if ratings else {},
            ),
        )

    def ratings(self, response: TextResponse) -> dict[str, Any]:
        """Every verdict the page states, in whatever form it states it."""
        found: dict[str, Any] = {}

        # Per element, never two zipped attribute lists: most images here carry
        # no alt, so the lists are different lengths and pairing them silently
        # drops every image past the shorter one — the rating graphic included.
        for image in response.xpath("//img"):
            src = image.attrib.get("src")
            alt = image.attrib.get("alt")
            points = rating_from_image(src)
            if points is not None and "graphic" not in found:
                found["graphic"] = {"points": points, "max": RATING_MAX, "alt": alt or None}
            if alt and "TOPspiel" in alt:
                found["badge"] = alt

        value = _int(response.xpath("//*[@itemprop='ratingValue']/@content").get())
        best = _int(response.xpath("//*[@itemprop='bestRating']/@content").get())
        if value is not None:
            found["microdata"] = {"value": value, "max": best}

        signature = _SIGNATURE.search(unescape(response.text))
        if signature:
            # Verbatim: the die face and arrow mean something to him, and
            # guessing what would be worse than passing them along.
            found["signature"] = signature.group(0).strip()

        difficulty = self.difficulty(response)
        if difficulty:
            found["difficulty"] = difficulty

        packaging = response.xpath("//text()[contains(., 'Verpackung')]").re_first(
            r"Verpackung\s*(\S+)"
        )
        if packaging:
            found["packaging"] = packaging

        return found

    def difficulty(self, response: TextResponse) -> dict[str, Any] | None:
        """A grade with an age recommendation — as an image, or as filled squares."""
        squares = response.xpath("//span[@class='schwierigkeit']/text()").get()
        if squares and (_FILLED in squares or _EMPTY in squares):
            return {
                "filled": squares.count(_FILLED),
                "max": squares.count(_FILLED) + squares.count(_EMPTY),
            }
        alt = (
            response.xpath("//p[contains(., 'Schwierigkeit')]//img/@alt").get()
            or response.xpath(
                "//img[contains(@src, 'schwer') or contains(@src, 'einfach')"
                " or contains(@src, 'mittel')]/@alt"
            ).get()
        )
        return {"label": alt} if alt else None

    def rating_tags(self, ratings: dict[str, Any]) -> list[str]:
        """The verdicts, phrased so they survive into the model's context.

        The prose states none of them: the score is a picture, the difficulty is
        a picture, the badge is a picture. Without this the review reaches
        extraction carrying no verdict at all.
        """
        tags = []
        if graphic := ratings.get("graphic"):
            tags.append(f"Wertung: {graphic['points']} von {graphic['max']} Punkten")
        if micro := ratings.get("microdata"):
            best = micro["max"]
            tags.append(f"Rating: {micro['value']}/{best}" if best else f"Rating: {micro['value']}")
        if signature := ratings.get("signature"):
            tags.append(signature)
        if difficulty := ratings.get("difficulty"):
            tags.append(
                f"Schwierigkeit: {difficulty['filled']} von {difficulty['max']}"
                if "filled" in difficulty
                else f"Schwierigkeit: {difficulty['label']}"
            )
        if packaging := ratings.get("packaging"):
            tags.append(f"Verpackung: {packaging}")
        if badge := ratings.get("badge"):
            tags.append(badge)
        return tags
