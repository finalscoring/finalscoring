"""Tests for the Spiel des Jahres roundup spider.

The HTML and REST payloads here are written for the test, not copied from the
site — they carry the shapes the spider depends on, nothing else.
"""

from datetime import UTC, datetime

from itemadapter import is_item
from scrapy.http import HtmlResponse, Request, Response, TextResponse
from scrapy.utils.spider import iterate_spider_output

from finalscoring.scraping.item import RawItem
from finalscoring.scraping.spiders import SpielDesJahresSpider
from finalscoring.scraping.spiders.spiel_des_jahres import language_from_locale

PAGE_URL = "https://www.spiel-des-jahres.de/kritikenrundschau-beispiel/"
WP_JSON_URL = "https://www.spiel-des-jahres.de/wp-json/wp/v2/posts/1"

PAGE_HTML = f"""
<html lang="de-DE">
  <head>
    <title>Kritikenrundschau: Beispiel</title>
    <meta name="description" content="Was die Jury las." />
    <meta property="article:published_time" content="2026-04-28T07:15:29+00:00" />
    <meta property="og:image" content="https://example.com/theme.jpg" />
    <meta property="og:site_name" content="Spiel des Jahres" />
    <link rel="alternate" type="application/json" href="{WP_JSON_URL}" />
  </head>
  <body>
    <article><p>Aus der Seite.</p></article>
  </body>
</html>
"""

WP_POST = {
    "date_gmt": "2026-04-28T07:15:29",
    "title": {"rendered": "Kritikenrundschau: Beispiel"},
    "content": {"rendered": "<p>Aus der Schnittstelle.</p>"},
    "yoast_head_json": {
        "og_site_name": "Spiel des Jahres",
        "og_locale": "de_DE",
        "og_image": [{"url": "https://example.com/post.jpg"}],
        "schema": {"@graph": [{"@type": "Article"}]},
    },
}


def _page_response(body: str = PAGE_HTML) -> HtmlResponse:
    return HtmlResponse(url=PAGE_URL, body=body, encoding="utf-8")


def _spider() -> SpielDesJahresSpider:
    return SpielDesJahresSpider()


def test_sitemap_rule_matches_roundups_only():
    (pattern, callback) = SpielDesJahresSpider.sitemap_rules[0]

    assert "kritikenrundschau" in pattern
    assert callback == "parse_roundup"


def test_outlet_slug_is_left_unset():
    """A roundup cites other outlets; which one published a review is decided later."""
    item = _spider().item_from_page(_page_response())

    assert item is not None
    assert item.outlet_slug is None
    assert item.spider_slug == "spiel-des-jahres"


def test_page_item_carries_the_article_text():
    item = _spider().item_from_page(_page_response())

    assert item is not None
    assert item.raw_text == "Aus der Seite."
    assert item.title == "Kritikenrundschau: Beispiel"
    assert item.description == "Was die Jury las."
    assert item.language == "de"
    assert item.language == "de"
    assert item.locale == "de-DE"
    assert item.published_at == datetime(2026, 4, 28, 7, 15, 29, tzinfo=UTC)


def test_a_page_without_an_article_yields_nothing():
    body = PAGE_HTML.replace("<article><p>Aus der Seite.</p></article>", "")

    assert _spider().item_from_page(_page_response(body)) is None


def test_rest_content_wins_over_the_page():
    """content.rendered has no theme wrapper, so it survives a theme change."""
    spider = _spider()
    page_item = spider.item_from_page(_page_response())
    assert page_item is not None

    merged = spider.merge_wp_json(page_item, WP_POST)

    assert merged.raw_text == "Aus der Schnittstelle."
    assert merged.raw_html == "<p>Aus der Schnittstelle.</p>"
    assert merged.image_url == "https://example.com/post.jpg"
    assert merged.schema_org == [{"@type": "Article"}]
    assert merged.locale == "de-DE"
    assert merged.published_at == datetime(2026, 4, 28, 7, 15, 29, tzinfo=UTC)


def test_full_rest_payload_is_kept_verbatim():
    """We don't know today what a later extraction pass will need from it."""
    spider = _spider()
    page_item = spider.item_from_page(_page_response())
    assert page_item is not None

    merged = spider.merge_wp_json(page_item, WP_POST)

    assert merged.extra == {"wp_json": WP_POST}


def test_naive_rest_timestamps_are_treated_as_utc():
    """date_gmt carries no offset but is UTC by definition."""
    spider = _spider()
    page_item = spider.item_from_page(_page_response())
    assert page_item is not None

    merged = spider.merge_wp_json(page_item, {"date_gmt": "2026-01-02T03:04:05"})

    assert merged.published_at == datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)


def test_empty_rest_content_keeps_the_page_text():
    """A protected or unpublished post returns no body; the page is better than none."""
    spider = _spider()
    page_item = spider.item_from_page(_page_response())
    assert page_item is not None

    merged = spider.merge_wp_json(page_item, {"content": {"rendered": ""}})

    assert merged.raw_text == "Aus der Seite."
    assert merged.extra == {"wp_json": {"content": {"rendered": ""}}}


def test_roundup_follows_the_rest_link():
    results = _spider().parse_roundup(_page_response())

    assert results is not None
    (request,) = results
    assert isinstance(request, Request)
    assert request.url == WP_JSON_URL
    assert request.cb_kwargs["item"].raw_text == "Aus der Seite."


PAGE_HTML_WITHOUT_REST_LINK = PAGE_HTML.replace(
    f'<link rel="alternate" type="application/json" href="{WP_JSON_URL}" />',
    "",
)


def test_roundup_without_a_rest_link_yields_the_page_item():
    results = _spider().parse_roundup(_page_response(PAGE_HTML_WITHOUT_REST_LINK))

    assert results is not None
    (item,) = results
    assert isinstance(item, RawItem)
    assert item.raw_text == "Aus der Seite."


def test_unparseable_rest_payload_falls_back_to_the_page():
    spider = _spider()
    page_item = spider.item_from_page(_page_response())
    assert page_item is not None
    broken = TextResponse(url=WP_JSON_URL, body=b"not json", encoding="utf-8")

    (result,) = spider.parse_wp_json(broken, item=page_item)

    assert result.raw_text == "Aus der Seite."


def test_non_text_rest_response_falls_back_to_the_page():
    """A PDF or an image where JSON was expected has no body we can decode."""
    spider = _spider()
    page_item = spider.item_from_page(_page_response())
    assert page_item is not None
    binary = Response(url=WP_JSON_URL, body=b"\x89PNG\r\n")

    (result,) = spider.parse_wp_json(binary, item=page_item)

    assert result.raw_text == "Aus der Seite."


def test_items_are_yielded_as_raw_items():
    """The declared contract is what actually flows, and Scrapy can export it."""
    results = _spider().parse_roundup(_page_response(PAGE_HTML_WITHOUT_REST_LINK))

    assert results is not None
    (item,) = results
    assert isinstance(item, RawItem)
    assert is_item(item)


def test_locale_parsing():
    assert language_from_locale("de_DE") == "de"
    assert language_from_locale("en-GB") == "en"
    assert language_from_locale("de") == "de"
    assert language_from_locale(None) is None
    assert language_from_locale("") is None
    assert language_from_locale("deu_DE") is None


def test_a_raw_item_is_never_returned_bare():
    """Pydantic models are iterable, so Scrapy shreds one into (name, value) pairs."""
    item = RawItem(url=PAGE_URL, spider_slug="spiel-des-jahres", raw_text="hi")

    assert len(list(iterate_spider_output(item))) > 1
    assert list(iterate_spider_output((item,))) == [item]
