"""Spider for H@LL9000, a German multi-critic review site.

Every other single-outlet source here is one critic per page. H@LL9000 is not:
one `/html/spiel/<slug>` page carries a full prose review by one critic *and*
a handful of short scored notes by others, each dated and signed. So, like the
Spiel des Jahres roundups, one page yields several reviews — the difference is
that the outlet is known (`hall9000`), only the critic varies. Splitting the
page into one review per critic is the extraction step's job; this spider hands
it the whole thing.

The page also carries reader ratings, under an `#leser_noten` heading. Those
are community opinion, which the project does not aggregate, so the item is
assembled from named parts (the prose blocks and the critics' notes) rather
than lifted whole, and the reader ratings are simply never picked up.

The verdict is images. Each score is a `wN_w.gif` / `wN_b.gif` whose filename
is the number, on a 1-to-6 scale across five axes (Aufmachung, Spielbarkeit,
Interaktion, Einfluss, Spielreiz); the site also shows a rounded overall out of
six. None of it is in the prose, so each critic's five axes are phrased into
`tags` and kept structured in `extra`. Nothing is reconciled or converted onto
the 0-100 scale — that is a load-step decision.

The site is a custom CMS: no sitemap, no feed, no REST. Discovery walks the
review list (`spielsucheliste.html?topic=1`, the "Rezension" filter, newest
first) page by page until a page holds no more reviews, and warns if it stops
short of the result count the list reports.
"""

import re
from collections.abc import AsyncIterator, Iterator
from datetime import datetime
from typing import Any

from parsel import Selector
from scrapy import Request, Spider
from scrapy.http.response import Response
from scrapy.http.response.text import TextResponse
from scrapy.settings import BaseSettings

from finalscoring.scraping.item import RawItem
from finalscoring.scraping.scrapy_settings import scrapy_settings
from finalscoring.scraping.text import html_to_text

BASE_URL = "https://www.hall9000.de/"
LIST_URL = f"{BASE_URL}html/spielsucheliste.html?topic=1&sort=7&dir=1&displaytype=2&page/{{page}}"

# A review permalink; the same game is also linked by numeric id, which this skips.
_REVIEW_HREF = re.compile(r"/html/spiel/(?![0-9]+(?:$|[?#]))[^/?#]+/?$")
# A JSON-LD block sits in the review area and embeds can sit in the prose;
# remove_tags keeps script bodies, so they are cut before the text is rendered.
_SCRIPT = re.compile(r"<script\b[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL)
# "/html/images/w5_w.gif" -> 5. The suffix (_w plain, _b emphasised) carries no score.
_SCORE_IMG = re.compile(r"/w(\d)_[a-z]\.gif")
_ONLINE_SINCE = re.compile(r"Online seit\s*(\d{2})\.(\d{2})\.(\d{4})")
# "5,5 H@LL9000" in the info box; the comma is the German decimal separator.
_OVERALL = re.compile(r"(\d+(?:,\d+)?)\s*H@LL9000")
_TREFFER = re.compile(r"Suchergebnis:\s*(\d+)\s*Treffer")

AXES = ("aufmachung", "spielbarkeit", "interaktion", "einfluss", "spielreiz")
# The info-box rows worth keeping; the rest is navigation (Ranking, Download).
INFO_LABELS = ("Autor", "Verlag", "Rezension", "Spieler", "Dauer", "Alter", "Jahr", "Bewertung")


def review_href(href: str | None) -> bool:
    return bool(href and _REVIEW_HREF.search(href))


def online_since(text: str | None) -> datetime | None:
    """The publication date from the "Online seit DD.MM.YYYY" line."""
    match = _ONLINE_SINCE.search(text or "")
    if not match:
        return None
    day, month, year = (int(part) for part in match.groups())
    try:
        return datetime(year, month, day)
    except ValueError:
        return None


def score_from_src(src: str | None) -> int | None:
    match = _SCORE_IMG.search(src or "")
    return int(match.group(1)) if match else None


class Hall9000Spider(Spider):
    name = "hall9000"
    allowed_domains = ("hall9000.de",)

    outlet_slug = "hall9000"
    language = "de"  # the site is German-only

    @classmethod
    def update_settings(cls, settings: BaseSettings) -> None:
        # Not custom_settings: that would read the environment at import time.
        super().update_settings(settings)
        settings.setdict(scrapy_settings(cls.name), priority="spider")

    async def start(self) -> AsyncIterator[Request]:
        yield self.list_request(0, found=0)

    def list_request(self, page: int, found: int) -> Request:
        # dont_filter for the same reason sitemaps are exempt from the dupefilter:
        # a list page is not content, and JOBDIR would otherwise make every run
        # after the first do nothing at all.
        return Request(
            LIST_URL.format(page=page),
            callback=self.parse_list,
            cb_kwargs={"page": page, "found": found},
            dont_filter=True,
        )

    def parse_list(self, response: Response, page: int, found: int) -> Iterator[Request]:
        if not isinstance(response, TextResponse):
            self.logger.error("Non-text list response from %s", response.url)
            return

        # Each game is linked twice per row (title and cover); dedupe within the page.
        seen: set[str] = set()
        for href in response.xpath("//a/@href").getall():
            url = response.urljoin(href)
            if review_href(href) and url not in seen:
                seen.add(url)
                yield response.follow(url, callback=self.parse_review)

        found += len(seen)
        expected = _TREFFER.search(response.text)
        self.logger.info("list page %d: %d reviews (%d so far)", page, len(seen), found)
        if seen:
            yield self.list_request(page + 1, found)
        elif expected and found < int(expected.group(1)):
            self.logger.warning(
                "review walk stopped at page %d with %d of %s reviews",
                page,
                found,
                expected.group(1),
            )

    # Wrapped, never bare: a pydantic model is iterable, so Scrapy would shred
    # a returned RawItem into (name, value) pairs.
    def parse_review(self, response: Response) -> tuple[RawItem] | None:
        if not isinstance(response, TextResponse):
            self.logger.error("Non-text response from %s", response.url)
            return None

        if not response.xpath("//div[@class='rezi']"):
            self.logger.debug("No review block, not a review page: %s", response.url)
            return None

        prose = response.xpath("//div[@class='rezi']//div[@class='textblock']")
        # Only the critics' notes, never the reader ratings that follow #leser_noten.
        notes = response.xpath(
            "//div[@class='rezi_noten'][preceding::h3[@id='hall_noten']]"
            "[not(preceding::h3[@id='leser_noten'])]"
        )
        if not prose and not notes:
            self.logger.warning("No review content at %s", response.url)
            return None

        online = response.xpath(
            "normalize-space(//div[@class='rezi']//p[contains(., 'Online seit')])"
        ).get()
        title = response.xpath("//div[@class='rezi']//h2/text()").get("").strip() or None
        info = self.info_box(response)
        ratings = [self.critic_rating(block) for block in notes]

        # Assembled from named parts rather than lifted whole: the review block is
        # also full of nav links, an affiliate panel and the reader ratings.
        review_html = _SCRIPT.sub(
            "",
            "\n".join(
                part
                for part in (
                    f"<p>{online}</p>" if online else "",
                    f"<h2>{title}</h2>" if title else "",
                    self.info_line(info),
                    *prose.getall(),
                    "<h3>H@LL9000-Bewertungen</h3>" if notes else "",
                    *notes.getall(),
                )
                if part
            ),
        )

        return (
            RawItem(
                url=response.url,
                spider_slug=self.name,
                raw_text=html_to_text(review_html),
                raw_html=review_html,
                title=title,
                published_at=online_since(online),
                language=self.language,
                image_url=self.cover_image(response),
                tags=self.game_tags(response) + self.rating_tags(info, ratings),
                outlet_slug=self.outlet_slug,
                og_site_name="H@LL9000",
                extra=self.extra(info, ratings),
            ),
        )

    def info_box(self, response: TextResponse) -> dict[str, str | list[str]]:
        """The labelled rows of the `spiel_info` table.

        The unlabelled continuation row holds the reader score, so dropping
        unlabelled rows also keeps community opinion out of the item.
        """
        collected: dict[str, str | list[str]] = {}
        for row in response.xpath("//div[@class='spiel_info']//tr"):
            label = row.xpath("normalize-space(td[@class='label'])").get("").rstrip(":")
            values = [
                " ".join(text.split())
                for text in row.xpath("td[not(@class='label')]//text()").getall()
                if text.split()
            ]
            if label in INFO_LABELS and values:
                collected[label] = values if len(values) > 1 else values[0]
        return collected

    def critic_rating(self, block: Selector) -> dict[str, Any]:
        """One critic's scored note: five axes, a signature and a short comment."""
        scores = {
            axis: score
            for img in block.xpath(".//img[starts-with(@class, 'icon_')]")
            if (axis := img.attrib.get("class", "").removeprefix("icon_")) in AXES
            and (score := score_from_src(img.attrib.get("src"))) is not None
        }
        comment_cell = block.xpath(".//td[@class='comment']")
        critic = comment_cell.xpath(".//a/text()").get()
        date = comment_cell.xpath(".//span[@class='date']/text()").get()
        # The cell reads "<date> von <critic> - <comment>"; keep only the comment.
        text = html_to_text(comment_cell.get() or "")
        if critic and critic in text:
            text = text.partition(critic)[2]
        return {
            "critic": critic,
            "date": date,
            "scores": scores,
            "comment": text.strip().lstrip("-").strip() or None,
        }

    def info_line(self, info: dict[str, str | list[str]]) -> str:
        """The identifying facts from the info box, as one line for the model."""
        parts = [
            f"{label}: {', '.join(_as_list(info[label]))}"
            for label in ("Autor", "Verlag", "Jahr")
            if info.get(label)
        ]
        return f"<p>{'. '.join(parts)}.</p>" if parts else ""

    def cover_image(self, response: TextResponse) -> str | None:
        src = response.xpath("//img[contains(@src, '_cover')]/@src").get()
        return response.urljoin(src) if src else None

    def game_tags(self, response: TextResponse) -> list[str]:
        tags = response.xpath(
            "//div[@class='spiele_tags']//span[@class='spiele_tag']/text()"
        ).getall()
        return [tag.strip() for tag in tags if tag.strip() and tag.strip() != "Tags:"]

    def rating_tags(
        self, info: dict[str, str | list[str]], ratings: list[dict[str, Any]]
    ) -> list[str]:
        """The verdicts phrased so they survive into the model's context.

        The scores are image filenames; without this the reviews reach
        extraction carrying no verdict at all.
        """
        tags = []
        overall = _OVERALL.search(" ".join(_as_list(info.get("Bewertung"))))
        if overall:
            tags.append(f"H@LL9000-Gesamtwertung: {overall.group(1)} von 6")
        for rating in ratings:
            axes = ", ".join(
                f"{axis.capitalize()} {rating['scores'][axis]}"
                for axis in AXES
                if axis in rating["scores"]
            )
            if axes and rating["critic"]:
                tags.append(f"{rating['critic']} (H@LL9000, je 1-6): {axes}")
        return tags

    def extra(
        self, info: dict[str, str | list[str]], ratings: list[dict[str, Any]]
    ) -> dict[str, Any]:
        collected: dict[str, Any] = {"info": info} if info else {}
        if ratings:
            collected["critic_ratings"] = ratings
        return collected


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    return [str(v) for v in value] if isinstance(value, list) else [str(value)]
