"""Spiel-des-Jahres Kritikenrundschau spider.

Ingests the Spiel-des-Jahres jury's editorial roundup pages
(``kritikenrundschau-*``). Each page typically cites several critics on
one or more games, so the LLM extraction stage may produce multiple
:class:`ExtractedReview` records per scraped item.

Treat SdJ here as a *meta-source*: the resulting ``Review`` rows carry
the cited critic as ``critic_id`` and SdJ as ``source_critic_id``, so
provenance is honest. The original-source URL is extracted by the LLM
where it appears in the roundup text.

Ported from the proof-of-concept SdJ scraper used in Recommend.Games.
"""

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup
from scrapy import Request
from scrapy.http.response import Response
from scrapy.http.response.text import TextResponse
from scrapy.spiders.sitemap import SitemapSpider

from final_scoring.scraping.base import RawReviewItem, base_settings


class SpielDesJahresSpider(SitemapSpider):
    """Sitemap-driven spider for spiel-des-jahres.de."""

    name = "sdj"
    critic_slug = "spiel_des_jahres"
    language = "de"

    allowed_domains = ("spiel-des-jahres.de",)
    sitemap_urls = ("https://www.spiel-des-jahres.de/sitemap_index.xml",)
    sitemap_rules = ((r"/kritikenrundschau-", "parse_review"),)

    custom_settings = base_settings()

    def parse_review(
        self,
        response: Response,
    ) -> RawReviewItem | Request | None:
        article_html = response.xpath("//article").get()
        if not article_html:
            self.logger.error("No article HTML at %s", response.url)
            return None

        article_text = BeautifulSoup(article_html, "html.parser").get_text()

        item: RawReviewItem = {
            "url": response.url,
            "critic_slug": self.critic_slug,
            "language": self.language,
            "title": response.xpath("//title/text()").get(),
            "description": response.xpath(
                "//meta[@name='description']/@content"
            ).get(),
            "date_published": response.xpath(
                "//meta[@property='article:published_time']/@content"
            ).get(),
            "image": response.xpath("//meta[@property='og:image']/@content").get(),
            "wp_json_url": response.xpath(
                "//link[@rel='alternate' and @type='application/json' "
                "and @title='JSON']/@href"
            ).get(),
            "oembed_json_url": response.xpath(
                "//link[@rel='alternate' and "
                "@type='application/json+oembed']/@href"
            ).get(),
            "raw_text": article_text,
        }

        if item.get("wp_json_url"):
            return Request(
                item["wp_json_url"],
                callback=self.parse_wp_json,
                cb_kwargs={"item": item},
            )

        if item.get("oembed_json_url"):
            return Request(
                item["oembed_json_url"],
                callback=self.parse_oembed_json,
                cb_kwargs={"item": item},
            )

        return item

    def parse_wp_json(
        self,
        response: Response,
        item: RawReviewItem,
    ) -> RawReviewItem | Request:
        if not isinstance(response, TextResponse):
            self.logger.error("Expected TextResponse for wp_json, got %s", type(response))
            return item

        try:
            item["wp_json"] = response.json()
        except Exception:  # pragma: no cover — network/JSON edge
            self.logger.exception("Failed to parse wp_json")
            item["wp_json"] = None

        if item.get("oembed_json_url"):
            return Request(
                item["oembed_json_url"],
                callback=self.parse_oembed_json,
                cb_kwargs={"item": item},
            )

        return item

    def parse_oembed_json(
        self,
        response: Response,
        item: RawReviewItem,
    ) -> RawReviewItem:
        if not isinstance(response, TextResponse):
            self.logger.error("Expected TextResponse for oembed_json, got %s", type(response))
            return item

        try:
            item["oembed_json"] = response.json()
        except Exception:  # pragma: no cover
            self.logger.exception("Failed to parse oembed_json")
            item["oembed_json"] = None

        return item


# Convenience alias matching the slug used in the critic registry.
SpielDesJahres = SpielDesJahresSpider
