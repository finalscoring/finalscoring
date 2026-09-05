"""Spider for Meeple Mountain, a multi-writer English review site.

The first source that is neither a solo blog nor an outlet-unknown meta-source:
one known outlet, many critics, one review per page. WordPress, and the
`reviews` custom post type has its own sitemap that enumerates the archive on
its own — no pagination fallback needed, unlike space-biff or games-we-play.

The catch is where the verdict lives. The post body in the REST API
(`content.rendered`) carries none of it: the star rating is appended by the
theme when the page renders. So this spider reads the rendered page, not the
API, which would hand extraction a review with no score at all.

The theme states the rating twice. A `rating-container` element's `title`
reads "4.0 / 5 stars — Great - Would recommend." — value, scale and tier in
one string — and a JSON-LD `Review` node repeats the number. Both become
`SourceRating`s (a `star_label` and a `schema_org`) and the load step picks.
On reviews with no numeric score — mostly video — the JSON-LD still carries
`ratingValue` 0.0, below its own `worstRating`; that is a placeholder, not a
verdict, and is dropped. Nothing is converted to the 0-100 scale.

One review per page by one named critic, so the `<meta name=author>` byline
goes on the review hint. The info box — designers, publishers, mechanisms,
release year, each a link whose text is the display name — feeds the game hint
as match evidence; the `<article>` class carries the same terms only as slugs
(and the release year as an unusable term id), so it is kept for `taxonomy` but
not trusted for names.
"""

import json
import re
from datetime import date
from typing import Any

from scrapy.http.response import Response
from scrapy.http.response.text import TextResponse

from finalscoring.models import RatingSystem
from finalscoring.scraping.item import RawGameHint, RawItem, RawReviewHint, SourceRating
from finalscoring.scraping.spider import ReviewSitemapSpider
from finalscoring.scraping.text import html_to_text
from finalscoring.scraping.timestamps import parse_iso

BASE_URL = "https://www.meeplemountain.com/"

# "4.0 / 5 stars — Great - Would recommend." — value, scale, then tier.
_STAR_TITLE = re.compile(r"^\s*([\d.]+)\s*/\s*([\d.]+)\s*stars?\s*—\s*(.+?)\.?\s*$")
# The theme prefixes every taxonomy term onto the <article> class with its kind.
_TAXONOMY = re.compile(r"^(category|mechanisms|designers|publishers|artists|release_year)-(.+)$")
# The info box repeats each term as a link — /designers/reiner-knizia/ with
# "Reiner Knizia" as its text. The href says the kind, the text is the name.
_TAXONOMY_HREF = re.compile(r"/(designers|publishers|artists|mechanisms|release_year)/[^/]+/?$")
# "Azul Game Review" / "Azul Review" -> "Azul"; the game name is what is left.
_REVIEW_SUFFIX = re.compile(r"\s+(?:Game\s+)?Review$", re.IGNORECASE)


def _float(value: Any) -> float | None:
    try:
        return float(value)
    except TypeError, ValueError:
        return None


def star_rating(title: str | None) -> dict[str, str] | None:
    """Value, scale and tier from the rating element's title attribute."""
    if not title:
        return None
    match = _STAR_TITLE.match(title)
    if not match:
        return None
    return {"value": match.group(1), "best": match.group(2), "tier": match.group(3).strip()}


def schema_org_rating(response: TextResponse) -> dict[str, Any] | None:
    """The `reviewRating` from the page's JSON-LD `Review` node, if present."""
    for blob in response.xpath('//script[@type="application/ld+json"]/text()').getall():
        try:
            data = json.loads(blob)
        except ValueError:
            continue
        for node in data.get("@graph", [data]) if isinstance(data, dict) else []:
            if isinstance(node, dict) and node.get("@type") == "Review":
                rating = node.get("reviewRating")
                if isinstance(rating, dict) and rating.get("ratingValue") is not None:
                    return rating
    return None


class MeepleMountainSpider(ReviewSitemapSpider):
    name = "meeple-mountain"
    allowed_domains = ("meeplemountain.com",)

    # The reviews CPT has its own sitemap; it lists /reviews/ itself, which the
    # rule's trailing segment requirement drops.
    sitemap_urls = (f"{BASE_URL}reviews-sitemap.xml",)
    sitemap_rules = ((r"/reviews/[^/]+/?$", "parse_review"),)

    outlet_slug = "meeple-mountain"
    language = "en"  # the site is English-only

    def parse_review(self, response: Response) -> tuple[RawItem] | None:
        """Smoke-test that a live review page still yields a populated item.

        @url https://www.meeplemountain.com/reviews/azul/
        @returns items 1 1
        @populated url spider_slug raw_text outlet_slug language title reviews
        """
        if not isinstance(response, TextResponse):
            self.logger.error("Non-text response from %s", response.url)
            return None

        content_html = response.xpath(
            "//div[contains(concat(' ', normalize-space(@class), ' '), ' entry-content ')]"
        ).get()
        raw_text = html_to_text(content_html or "")
        if not raw_text:
            self.logger.warning("No article content at %s", response.url)
            return None

        rating = star_rating(response.xpath('//li[@class="rating"]/@title').get())
        schema_rating = schema_org_rating(response)
        taxonomy = self.taxonomy(response)
        info_box = self.info_box(response)
        author = response.xpath("//meta[@name='author']/@content").get()
        # og:title and <title> both carry a "Meeple Mountain" suffix; the h1 does not.
        heading = response.xpath(
            "normalize-space(//h1[contains(concat(' ', normalize-space(@class), ' '),"
            " ' entry-title ')])"
        ).get()

        return (
            RawItem(
                url=response.url,
                spider_slug=self.name,
                raw_text=raw_text,
                raw_html=content_html,
                title=heading or response.xpath("//title/text()").get(),
                description=response.xpath("//meta[@name='description']/@content").get(),
                published_at=parse_iso(
                    response.xpath("//meta[@property='article:published_time']/@content").get()
                ),
                language=self.language,
                locale=response.xpath("//meta[@property='og:locale']/@content").get(),
                image_url=response.xpath("//meta[@property='og:image']/@content").get(),
                categories=taxonomy.get("category", []),
                taxonomy=taxonomy,
                reviews=self.review_hints(author, rating, schema_rating, heading, info_box),
                outlet_slug=self.outlet_slug,
                site_name=response.xpath("//meta[@property='og:site_name']/@content").get(),
                raw_metadata=self.raw_metadata(rating, schema_rating),
            ),
        )

    def taxonomy(self, response: TextResponse) -> dict[str, list[str]]:
        """The theme's per-post taxonomy, read off the <article> class list."""
        grouped: dict[str, list[str]] = {}
        classes = response.xpath("//article[contains(@class, 'herald-single')]/@class").get()
        for token in (classes or "").split():
            match = _TAXONOMY.match(token)
            if match:
                grouped.setdefault(match.group(1), []).append(match.group(2))
        return grouped

    def info_box(self, response: TextResponse) -> dict[str, list[str]]:
        """The game's metadata as the info box names it — human-readable, not slugs.

        The theme repeats every taxonomy term here as a link whose href states
        the kind (`/publishers/999-games/`) and whose text is the display name
        ("999 Games"). Preferred over the `<article>` class slugs so the game
        hint carries names a reader and the model recognise.
        """
        grouped: dict[str, list[str]] = {}
        links = response.xpath(
            "//div[contains(concat(' ', normalize-space(@class), ' '), ' entry-content ')]"
            "//a[contains(concat(' ', normalize-space(@class), ' '), ' taxonomy-link ')]"
        )
        for link in links:
            href = link.xpath("@href").get() or ""
            match = _TAXONOMY_HREF.search(href)
            name = (link.xpath("normalize-space(.)").get() or "").strip()
            if match and name:
                grouped.setdefault(match.group(1), []).append(name)
        return grouped

    def review_hints(
        self,
        author: str | None,
        rating: dict[str, str] | None,
        schema_rating: dict[str, Any] | None,
        heading: str | None,
        info_box: dict[str, list[str]],
    ) -> list[RawReviewHint]:
        """The page's one review — its critic, its verdict, and the game it names.

        The score is theme markup, not prose; without the SourceRatings the
        review would reach extraction with no verdict at all.
        """
        scores: list[SourceRating] = []
        if rating:
            scores.append(
                SourceRating(
                    system=RatingSystem.star_label,
                    value=_float(rating["value"]),
                    scale_max=_float(rating["best"]),
                    label=rating["tier"],
                )
            )
        schema_value = _float((schema_rating or {}).get("ratingValue"))
        schema_floor = _float((schema_rating or {}).get("worstRating"))
        # The CMS emits ratingValue 0.0 — below its own worstRating — on reviews
        # that carry no numeric score (mostly video). That is a placeholder, not
        # a verdict.
        if (
            schema_value is not None
            and schema_value > 0
            and (schema_floor is None or schema_value >= schema_floor)
        ):
            scores.append(
                SourceRating(
                    system=RatingSystem.schema_org,
                    value=schema_value,
                    scale_min=schema_floor,
                    scale_max=_float((schema_rating or {}).get("bestRating")),
                )
            )

        game = self.game_hint(heading, info_box)
        if not (author or scores or game):
            return []
        return [
            RawReviewHint(
                critic_names=[author] if author else [],
                ratings=scores,
                game=game,
            )
        ]

    def game_hint(self, heading: str | None, info_box: dict[str, list[str]]) -> RawGameHint | None:
        """The game the info box names, as match evidence for BGG resolution."""
        max_year = date.today().year + 2
        year = next(
            (
                int(y)
                for y in info_box.get("release_year", [])
                if y.isdigit() and 1900 <= int(y) <= max_year
            ),
            None,
        )
        name = _REVIEW_SUFFIX.sub("", heading).strip() if heading else ""
        designers = info_box.get("designers", [])
        publishers = info_box.get("publishers", [])
        artists = info_box.get("artists", [])
        mechanics = info_box.get("mechanisms", [])
        if not (name or designers or publishers or artists or mechanics or year):
            return None
        return RawGameHint(
            titles=[name] if name else [],
            designers=designers,
            publishers=publishers,
            artists=artists,
            mechanics=mechanics,
            year_published=year,
            source="meeple mountain info box",
        )

    def raw_metadata(
        self, rating: dict[str, str] | None, schema_rating: dict[str, Any] | None
    ) -> dict[str, Any]:
        # The raw parse, for cross-checking the two ratings the load step gets.
        if rating or schema_rating:
            return {"rating": {**(rating or {}), "schema_org": schema_rating}}
        return {}
