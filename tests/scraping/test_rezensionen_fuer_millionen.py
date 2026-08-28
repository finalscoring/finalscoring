"""Tests for the Rezensionen für Millionen spider, against canned feed pages."""

import json
from typing import Any

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from finalscoring.scraping.item import RawItem
from finalscoring.scraping.spiders import RezensionenFuerMillionenSpider

FEED_URL = "https://rezensionen-fuer-millionen.blogspot.com/feeds/posts/default?alt=json"
POST_URL = "https://rezensionen-fuer-millionen.blogspot.com/2016/11/costa-rica.html"

BODY = (
    "<div><p>COSTA RICA ist ein hübsches Spiel mit einem Haken.</p>"
    "<p>**** solide COSTA RICA von Matthew Dunstan und Brett J. Gilbert "
    'für zwei bis fünf Spieler, <a href="https://lookout-spiele.de/">Lookout Spiele</a>.</p></div>'
)


def _entry(**kwargs: Any) -> dict[str, Any]:
    return {
        "title": {"$t": "Costa Rica"},
        "content": {"$t": BODY},
        "published": {"$t": "2016-11-14T08:30:00.000+01:00"},
        "author": [{"name": {"$t": "Udo Bartsch"}}],
        "category": [{"term": "**** solide"}],
        "media$thumbnail": {"url": "https://example.com/thumb.jpg"},
        "link": [
            {"rel": "replies", "href": "https://example.com/replies"},
            {"rel": "alternate", "href": POST_URL},
        ],
    } | kwargs


def _feed(*entries: dict[str, Any], start: int = 1, total: int | None = None) -> dict[str, Any]:
    return {
        "feed": {
            "title": {"$t": "Rezensionen für Millionen"},
            "openSearch$startIndex": {"$t": str(start)},
            "openSearch$totalResults": {"$t": str(total if total is not None else len(entries))},
            "entry": list(entries),
        }
    }


def _response(payload: dict[str, Any] | str, url: str = FEED_URL) -> TextResponse:
    body = payload if isinstance(payload, str) else json.dumps(payload)
    return TextResponse(url=url, body=body.encode(), encoding="utf-8", request=Request(url))


def _spider() -> RezensionenFuerMillionenSpider:
    return RezensionenFuerMillionenSpider()


def _items(output) -> list[RawItem]:
    return [x for x in output if isinstance(x, RawItem)]


def _requests(output) -> list[Request]:
    return [x for x in output if isinstance(x, Request)]


def test_a_starred_post_becomes_an_item():
    out = list(_spider().parse_feed(_response(_feed(_entry()))))

    (item,) = _items(out)
    assert item.url == POST_URL
    assert item.spider_slug == "rezensionen-fuer-millionen"
    assert item.title == "Costa Rica"
    assert "COSTA RICA ist ein hübsches Spiel" in item.raw_text


def test_the_outlet_is_known_at_scrape_time():
    """Unlike a roundup: one blog, one critic, so the outlet is not in doubt."""
    (item,) = _items(_spider().parse_feed(_response(_feed(_entry()))))

    assert item.outlet_slug == "rezensionen-fuer-millionen"
    assert item.og_site_name == "Rezensionen für Millionen"


def test_the_star_label_is_carried_as_a_tag():
    """The label is his rating, and it reaches the model through the tags."""
    (item,) = _items(_spider().parse_feed(_response(_feed(_entry()))))

    assert item.tags == ["**** solide"]


def test_the_thumbnail_is_read_from_its_attribute():
    """Media RSS uses `url`, not the `$t` every other Blogger scalar uses."""
    (item,) = _items(_spider().parse_feed(_response(_feed(_entry()))))

    assert item.image_url == "https://example.com/thumb.jpg"


def test_a_post_covering_two_games_keeps_both_ratings():
    """Four of his posts carry two stars because they review two games."""
    entry = _entry(category=[{"term": "**** solide"}, {"term": "***** reizvoll"}])

    (item,) = _items(_spider().parse_feed(_response(_feed(entry))))

    assert item.tags == ["**** solide", "***** reizvoll"]


def test_the_post_body_is_kept_as_html():
    (item,) = _items(_spider().parse_feed(_response(_feed(_entry()))))

    assert item.raw_html is not None
    assert '<a href="https://lookout-spiele.de/">' in item.raw_html


def test_the_published_date_keeps_its_offset():
    (item,) = _items(_spider().parse_feed(_response(_feed(_entry()))))

    assert item.published_at is not None
    assert item.published_at.utcoffset() is not None
    assert (item.published_at.year, item.published_at.month) == (2016, 11)


def test_the_whole_entry_is_preserved():
    """Same bargain as wp_json: keep the source payload, decide later."""
    (item,) = _items(_spider().parse_feed(_response(_feed(_entry()))))

    assert item.extra["blogger_entry"]["author"][0]["name"]["$t"] == "Udo Bartsch"


@pytest.mark.parametrize("label", ["Gern gespielt", "Vor 20 Jahren"])
def test_a_post_without_a_star_label_is_not_a_review(label: str):
    """His recurring columns carry no verdict; extracting them wastes a minute each."""
    out = list(_spider().parse_feed(_response(_feed(_entry(category=[{"term": label}])))))

    assert _items(out) == []


def test_an_unlabelled_post_is_not_a_review():
    out = list(_spider().parse_feed(_response(_feed(_entry(category=[])))))

    assert _items(out) == []


def test_the_filter_can_be_turned_off():
    """Whether a column counts as a review is a judgement, not a fact."""
    spider = _spider()
    spider.reviews_only = False

    out = list(spider.parse_feed(_response(_feed(_entry(category=[{"term": "Gern gespielt"}])))))

    assert len(_items(out)) == 1


def test_an_entry_without_a_post_url_is_skipped():
    entry = _entry(link=[{"rel": "replies", "href": "https://example.com/r"}])

    assert _items(_spider().parse_feed(_response(_feed(entry)))) == []


def test_an_entry_with_an_empty_body_is_skipped():
    assert _items(_spider().parse_feed(_response(_feed(_entry(content={"$t": ""}))))) == []


def test_the_next_page_is_followed():
    out = list(_spider().parse_feed(_response(_feed(_entry(), start=1, total=300))))

    (request,) = _requests(out)
    assert "start-index=2" in request.url


def test_the_last_page_ends_the_crawl():
    out = list(_spider().parse_feed(_response(_feed(_entry(), start=1, total=1))))

    assert _requests(out) == []


def test_an_empty_page_ends_the_crawl():
    out = list(_spider().parse_feed(_response(_feed(start=1, total=900))))

    assert _requests(out) == []


def test_feed_pages_bypass_the_dupefilter():
    """JOBDIR would otherwise make every run after the first do nothing."""
    assert _spider().feed_request(1).dont_filter is True


def test_an_unparseable_feed_is_logged_not_raised():
    assert list(_spider().parse_feed(_response("<html>nope</html>"))) == []


def test_a_feed_without_the_feed_key_is_logged_not_raised():
    assert list(_spider().parse_feed(_response({"error": "nope"}))) == []
