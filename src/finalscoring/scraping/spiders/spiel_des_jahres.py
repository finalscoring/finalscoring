"""Spider for the Spiel des Jahres jury's "Kritikenrundschau" roundups.

A meta-source: one page reports many critics' verdicts on one game, so the
outlet of a review is whichever publication the roundup cites, never Spiel des
Jahres itself. The spider therefore leaves `outlet_slug` unset — resolving who
published what is the extraction and load steps' work.

The site runs WordPress, so each post is also available through the REST API,
which is preferred over the rendered page: `content.rendered` is the post body
without the theme's wrapper, and it does not move when the theme changes.
"""

from typing import Any

from scrapy.http import Request
from scrapy.http.response import Response
from scrapy.http.response.text import TextResponse
from twisted.python.failure import Failure

from finalscoring.scraping.item import RawItem, language_from_locale
from finalscoring.scraping.spider import ReviewSitemapSpider
from finalscoring.scraping.text import html_to_text
from finalscoring.scraping.timestamps import as_utc

WP_JSON_LINK = "//link[@rel='alternate' and @type='application/json']/@href"


class SpielDesJahresSpider(ReviewSitemapSpider):
    name = "spiel-des-jahres"
    allowed_domains = ("spiel-des-jahres.de",)

    sitemap_urls = ("https://www.spiel-des-jahres.de/sitemap_index.xml",)
    sitemap_rules = ((r"/kritikenrundschau-", "parse_roundup"),)

    def parse_roundup(
        self,
        response: TextResponse,
    ) -> tuple[RawItem | Request] | None:
        """Smoke-test that a live roundup still parses and finds its REST link.

        @url https://www.spiel-des-jahres.de/kritikenrundschau-harry-potter-kampf-um-hogwarts-lumos-oder-cruciatus/
        @returns requests 1 1
        """
        item = self.item_from_page(response)
        if item is None:
            self.logger.warning("No article content at %s", response.url)
            return None

        wp_json_url = response.xpath(WP_JSON_LINK).get()
        if not wp_json_url:
            return (item,)

        # Carried along so a REST failure downgrades to the page, not to nothing.
        return (
            response.follow(
                wp_json_url,
                callback=self.parse_wp_json,
                errback=self.wp_json_unavailable,
                cb_kwargs={"item": item},
            ),
        )

    def item_from_page(self, response: TextResponse) -> RawItem | None:
        """Build an item from the rendered page — the fallback path."""
        article_html = response.xpath("//article").get() or ""
        raw_text = html_to_text(article_html)
        if not raw_text:
            return None

        page_locale = (
            response.xpath("//html/@lang").get()
            or response.xpath(
                "//meta[@property='og:locale']/@content",
            ).get()
        )

        return RawItem(
            url=response.url,
            spider_slug=self.name,
            raw_text=raw_text,
            raw_html=article_html,
            title=response.xpath("//title/text()").get(),
            description=response.xpath("//meta[@name='description']/@content").get(),
            published_at=as_utc(
                response.xpath("//meta[@property='article:published_time']/@content").get(),
            ),
            language=language_from_locale(page_locale),
            locale=page_locale,
            image_url=response.xpath("//meta[@property='og:image']/@content").get(),
            og_site_name=response.xpath("//meta[@property='og:site_name']/@content").get(),
        )

    def parse_wp_json(
        self,
        response: Response,
        item: RawItem,
    ) -> tuple[RawItem]:
        """Smoke-test that the live WordPress REST post still fetches and parses.

        Post 11440 is the roundup `parse_roundup`'s `@url` points at. The
        injected `item` is synthetic, so this only checks the REST call is
        reachable and the parse does not raise — not that the merge found text.

        @url https://www.spiel-des-jahres.de/wp-json/wp/v2/posts/11440
        @raw_item item
        @returns items 1 1
        """
        # Response, not TextResponse: that is what Scrapy promises a callback.
        if not isinstance(response, TextResponse):
            self.logger.error("Non-text REST response from %s", response.url)
            return (item,)

        try:
            post = response.json()
        except ValueError:
            self.logger.exception("Unparseable REST payload at %s", response.url)
            return (item,)

        return (self.merge_wp_json(item, post),)

    def merge_wp_json(self, item: RawItem, post: dict[str, Any]) -> RawItem:
        """Prefer REST values over the scraped page wherever the REST call gave one."""
        content_html = (post.get("content") or {}).get("rendered") or ""
        raw_text = html_to_text(content_html)
        yoast = post.get("yoast_head_json") or {}
        og_image = yoast.get("og_image") or []

        updates: dict[str, Any] = {
            "title": (post.get("title") or {}).get("rendered"),
            # date_gmt has no offset; it is UTC by definition.
            "published_at": as_utc(post.get("date_gmt")),
            "og_site_name": yoast.get("og_site_name"),
            "language": language_from_locale(yoast.get("og_locale")),
            "locale": yoast.get("og_locale"),
            "image_url": og_image[0].get("url") if og_image else None,
            "schema_org": (yoast.get("schema") or {}).get("@graph"),
            "extra": {"wp_json": post},
        }
        if raw_text:
            updates["raw_text"] = raw_text
            updates["raw_html"] = content_html
        else:
            # A protected or unpublished post; the page text beats nothing.
            self.logger.warning("Empty REST content for %s", item.url)

        # Revalidated, not model_copy: these values come from a third party.
        merged = item.model_dump()
        merged.update({k: v for k, v in updates.items() if v})
        return RawItem.model_validate(merged)

    def wp_json_unavailable(self, failure: Failure) -> tuple[RawItem]:
        """Fall back to the page when the REST API is missing or refuses us."""
        # Scrapy attaches this; Twisted's Failure does not declare it.
        request = failure.request  # ty: ignore[unresolved-attribute]
        item: RawItem = request.cb_kwargs["item"]
        self.logger.warning(
            "REST call failed for %s (%s); using the rendered page",
            item.url,
            failure.value,
        )
        return (item,)
