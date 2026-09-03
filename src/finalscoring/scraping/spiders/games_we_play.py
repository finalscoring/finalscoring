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
a filename, an `alt` attribute. Each scored verdict becomes a `SourceRating` on
the page's one review hint, the difficulty goes on the game hint, and the
packaging mark and badge become editorial flags. Nothing is reconciled or
converted: which of his scales becomes the score is a load-step decision. The
raw parse stays in `raw_metadata` alongside.

He is the sole critic, so `known_critic_name` carries Harald Schrapers.
"""

import re
from collections.abc import AsyncIterator, Iterator
from html import unescape
from typing import Any

from scrapy import Request
from scrapy.http.response import Response
from scrapy.http.response.text import TextResponse

from finalscoring.models import RatingSystem
from finalscoring.scraping.item import RawGameHint, RawItem, RawReviewHint, SourceRating
from finalscoring.scraping.spider import ReviewSitemapSpider
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
_SIGNATURE_SCORE = re.compile(r"(\d+)\s*/\s*(\d+)")
_FILLED, _EMPTY = "◼", "◻"  # ◼ ◻ — the difficulty squares


def _complexity_label(difficulty: dict[str, Any] | None) -> str | None:
    """The difficulty grade as a string: "2 von 4" from squares, or the alt text."""
    if not difficulty:
        return None
    if "filled" in difficulty:
        return f"{difficulty['filled']} von {difficulty['max']}"
    return difficulty.get("label")


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


class GamesWePlaySpider(ReviewSitemapSpider):
    name = "games-we-play"
    allowed_domains = ("gamesweplay.de",)

    sitemap_urls = (f"{BASE_URL}sitemap.xml",)
    # Every review is <game>.html; the sitemap also lists a spreadsheet and a
    # handful of index pages, which the rating graphic weeds out later.
    sitemap_rules = ((r"\.html?$", "parse_review"),)

    outlet_slug = "games-we-play"
    known_critic_name = "Harald Schrapers"
    # Nowhere in the markup; the masthead is an image whose alt text says it.
    site_name = "games we play"
    language = "de"

    reviews_only = True

    async def start(self) -> AsyncIterator[Request]:
        """The sitemap misses ~200 pages, so the archives are crawled as well."""
        async for request in super().start():
            yield request
        yield Request(f"{BASE_URL}index.html", callback=self.parse_index)

    def parse_index(self, response: Response) -> Iterator[Request]:
        """Yearly archives link on to each other; everything else is a candidate.

        @url https://gamesweplay.de/index.html
        @returns requests 1
        """
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

    def parse_review(self, response: Response) -> tuple[RawItem] | None:
        """Smoke-test that a live scored review still yields a populated item.

        @url https://gamesweplay.de/dewan.html
        @returns items 1 1
        @populated url spider_slug raw_text outlet_slug known_critic_name language title reviews
        """
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
        hint = self.review_hint(response, ratings)

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
                reviews=[hint] if hint is not None else [],
                known_critic_name=self.known_critic_name,
                outlet_slug=self.outlet_slug,
                site_name=self.site_name,
                raw_metadata={"ratings": ratings} if ratings else {},
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

    def review_hint(self, response: TextResponse, ratings: dict[str, Any]) -> RawReviewHint | None:
        """The page's verdicts, structured. The prose states none of them.

        One hint per page — he reviews one game per file. The graphic, the
        microdata and the signature line are three readings of the same verdict
        on different scales, kept as three `SourceRating`s for the load step to
        choose between.
        """
        scores: list[SourceRating] = []
        if graphic := ratings.get("graphic"):
            scores.append(
                SourceRating(
                    system=RatingSystem.editorial,
                    value=graphic["points"],
                    scale_min=0,
                    scale_max=graphic["max"],
                    verbatim=graphic["alt"],
                )
            )
        if micro := ratings.get("microdata"):
            scores.append(
                SourceRating(
                    system=RatingSystem.schema_org, value=micro["value"], scale_max=micro["max"]
                )
            )
        if signature := ratings.get("signature"):
            match = _SIGNATURE_SCORE.search(signature)
            scores.append(
                SourceRating(
                    system=RatingSystem.signature,
                    value=int(match.group(1)) if match else None,
                    scale_max=int(match.group(2)) if match else None,
                    verbatim=signature,
                )
            )

        flags: list[str] = []
        if packaging := ratings.get("packaging"):
            flags.append(f"Verpackung: {packaging}")
        if badge := ratings.get("badge"):
            flags.append(badge)

        name = response.xpath("normalize-space(//p[@class='head'])").get() or ""
        complexity = _complexity_label(ratings.get("difficulty"))
        game = (
            RawGameHint(
                titles=[name] if name else [],
                complexity_label=complexity,
                source="games we play page",
            )
            if name or complexity
            else None
        )

        if not scores and not flags and game is None:
            return None
        return RawReviewHint(ratings=scores, editorial_flags=flags, game=game)
