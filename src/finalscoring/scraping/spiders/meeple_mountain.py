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
one string — and a JSON-LD `Review` node repeats the number. They disagree on
the older video reviews, where the JSON-LD number is 0.0 and the title string
is right, so the title string is the one trusted; the JSON-LD value is kept
alongside it for cross-checking. Nothing is converted to the 0-100 scale — that
is a load-step decision.
"""

import json
import re
from typing import Any

from scrapy.http.response import Response
from scrapy.http.response.text import TextResponse

from finalscoring.scraping.item import RawItem
from finalscoring.scraping.spider import ReviewSitemapSpider
from finalscoring.scraping.text import html_to_text
from finalscoring.scraping.timestamps import parse_iso

BASE_URL = "https://www.meeplemountain.com/"

# "4.0 / 5 stars — Great - Would recommend." — value, scale, then tier.
_STAR_TITLE = re.compile(r"^\s*([\d.]+)\s*/\s*([\d.]+)\s*stars?\s*—\s*(.+?)\.?\s*$")
# The theme prefixes every taxonomy term onto the <article> class with its kind.
_TAXONOMY = re.compile(r"^(category|mechanisms|designers|publishers|artists|release_year)-(.+)$")


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
        @populated url spider_slug raw_text outlet_slug language title tags
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
                tags=self.rating_tags(rating) + taxonomy.get("category", []),
                outlet_slug=self.outlet_slug,
                og_site_name=response.xpath("//meta[@property='og:site_name']/@content").get(),
                extra=self.extra(response, rating, schema_rating, taxonomy),
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

    def rating_tags(self, rating: dict[str, str] | None) -> list[str]:
        """The verdict phrased so it survives into the model's context.

        The score is theme markup, not prose — without this the review reaches
        extraction carrying no verdict at all.
        """
        if not rating:
            return []
        return [
            f"Meeple Mountain rating: {rating['value']} / {rating['best']}",
            rating["tier"],
        ]

    def extra(
        self,
        response: TextResponse,
        rating: dict[str, str] | None,
        schema_rating: dict[str, Any] | None,
        taxonomy: dict[str, list[str]],
    ) -> dict[str, Any]:
        collected: dict[str, Any] = {}
        author = response.xpath("//meta[@name='author']/@content").get()
        if author:
            collected["author"] = author
        if rating or schema_rating:
            collected["rating"] = {**(rating or {}), "schema_org": schema_rating}
        if taxonomy:
            collected["taxonomy"] = taxonomy
        return collected
