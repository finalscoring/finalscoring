"""Tests for the generic review-links spider.

The HTML here is written for the test - it carries the shapes the spider and
trafilatura depend on (an article body, a comment block, a locale, some head
metadata), nothing else.
"""

import asyncio
import json

import pytest
from itemadapter import is_item
from scrapy.http import HtmlResponse, Request

from finalscoring.scraping.item import RawItem
from finalscoring.scraping.spiders import ReviewLinksSpider
from finalscoring.scraping.spiders.review_links import (
    covered_domains,
    has_dedicated_spider,
    iter_rows,
    iter_urls,
)

REVIEW_URL = "https://www.spieletest.at/artikel/catan"

REVIEW_HTML = """
<html lang="de-AT"><head>
  <title>Catan im Test - spieletest.at</title>
  <meta property="og:site_name" content="spieletest.at" />
  <meta property="og:locale" content="de_AT" />
  <meta property="article:published_time" content="2011-03-14T09:00:00+00:00" />
</head><body>
  <header><nav>Startseite | Neuheiten | Impressum</nav></header>
  <article>
    <h1>Catan - der Klassiker im Test</h1>
    <p>Die Siedler von Catan gehoert zu den Titeln, die das moderne Brettspiel
       gepraegt haben, und auch nach vielen Jahren zieht die Mischung aus Aufbau
       und Handel noch immer.</p>
    <p>Das Spielmaterial ist funktional, die Regeln sind in wenigen Minuten
       erklaert, und trotzdem entsteht am Tisch jedes Mal eine andere Partie.</p>
    <h2>Fazit</h2>
    <p>Ein verdienter Dauerbrenner, der in keiner Sammlung fehlen sollte. Von uns
       gibt es fuenf von sechs Punkten.</p>
  </article>
  <footer>(c) 2011 spieletest.at</footer>
  <section id="comments">
    <h3>Leserkommentare</h3>
    <p>Bestes Spiel aller Zeiten, ganz klar sechs Sterne! - Hans</p>
  </section>
</body></html>
"""


def _response(html: str = REVIEW_HTML, url: str = REVIEW_URL) -> HtmlResponse:
    return HtmlResponse(url=url, body=html, encoding="utf-8", request=Request(url))


def _spider(**attrs: object) -> ReviewLinksSpider:
    spider = ReviewLinksSpider()
    for key, value in attrs.items():
        setattr(spider, key, value)
    return spider


def _item(rows: list[dict[str, object]] | None = None, html: str = REVIEW_HTML):
    out = _spider().parse_review(_response(html), rows=rows or [{}])
    return out[0] if out else None


def _drain_start(spider: ReviewLinksSpider) -> list[Request]:
    async def go() -> list[Request]:
        return [request async for request in spider.start()]

    return asyncio.run(go())


# --- helpers -----------------------------------------------------------------


def test_has_dedicated_spider_matches_host_and_subdomains_only():
    assert has_dedicated_spider("hall9000.de")
    assert has_dedicated_spider("www.hall9000.de")
    assert has_dedicated_spider("WWW.Hall9000.de:443")
    assert not has_dedicated_spider("nothall9000.de")
    assert not has_dedicated_spider("spieletest.at")


def test_covered_domains_is_derived_from_the_registered_spiders():
    """Adding a spider must not require also editing a hand-kept list here."""
    from finalscoring.scraping import spiders

    expected = {
        domain
        for name in spiders.__all__
        for domain in (getattr(getattr(spiders, name), "allowed_domains", None) or ())
    }

    assert covered_domains() == expected
    assert "hall9000.de" in covered_domains()
    assert "review-links" not in covered_domains()  # the meta-sources contribute nothing


def test_iter_urls_keeps_http_links_and_drops_the_fragment():
    assert list(iter_urls("https://a.test/x#top")) == ["https://a.test/x"]
    assert list(iter_urls(["https://a.test/1", "http://b.test/2"])) == [
        "https://a.test/1",
        "http://b.test/2",
    ]
    assert list(iter_urls("  https://a.test/y  ")) == ["https://a.test/y"]
    assert list(iter_urls(None)) == []
    assert list(iter_urls("mailto:someone@a.test")) == []
    assert list(iter_urls("/relative/path")) == []


def test_iter_rows_reads_jsonl_and_csv(tmp_path):
    jl = tmp_path / "data.jl"
    jl.write_text('{"review_url": "https://a.test/1"}\n\n{"review_url": "https://a.test/2"}\n')
    assert [r["review_url"] for r in iter_rows(jl)] == ["https://a.test/1", "https://a.test/2"]

    csv_path = tmp_path / "data.csv"
    csv_path.write_text("review_url,name\nhttps://a.test/3,Catan\n")
    assert list(iter_rows(csv_path)) == [{"review_url": "https://a.test/3", "name": "Catan"}]


def test_iter_rows_rejects_an_unknown_file_type(tmp_path):
    bad = tmp_path / "data.txt"
    bad.write_text("whatever")
    with pytest.raises(ValueError, match="unsupported file type"):
        list(iter_rows(bad))


# --- start(): reading the file, deduping, skipping covered hosts -------------


def test_start_dedupes_urls_and_accumulates_the_rows_that_point_at_each(tmp_path):
    src = tmp_path / "luding.jl"
    src.write_text(
        "\n".join(
            json.dumps(row)
            for row in (
                {"review_url": "https://rev.test/a", "name": "Catan"},
                {"review_url": "https://rev.test/a", "name": "Catan: Seafarers"},
                {"review_url": ["https://rev.test/b", "https://rev.test/a#c"], "name": "Elfenland"},
            )
        )
    )
    requests = _drain_start(_spider(files=str(src)))

    by_url = {r.url: r.cb_kwargs["rows"] for r in requests}
    assert set(by_url) == {"https://rev.test/a", "https://rev.test/b"}
    assert [row["name"] for row in by_url["https://rev.test/a"]] == [
        "Catan",
        "Catan: Seafarers",
        "Elfenland",
    ]


def test_start_skips_urls_on_domains_with_a_dedicated_spider(tmp_path):
    src = tmp_path / "luding.jl"
    src.write_text(
        "\n".join(
            json.dumps({"review_url": u})
            for u in (
                "https://www.hall9000.de/html/spiel/catan.html",
                "https://shutupandsitdown.com/reviews/catan/",
                "https://spieletest.at/artikel/catan",
            )
        )
    )
    spider = _spider(files=str(src))
    requests = _drain_start(spider)

    assert [r.url for r in requests] == ["https://spieletest.at/artikel/catan"]
    assert len(spider._covered) == 2


def test_start_accepts_a_comma_separated_file_list_and_globs(tmp_path):
    (tmp_path / "one.jl").write_text('{"review_url": "https://rev.test/1"}\n')
    (tmp_path / "two.jl").write_text('{"review_url": "https://rev.test/2"}\n')
    spider = _spider(files=f"{tmp_path}/one.jl,{tmp_path}/*.jl")
    urls = sorted(r.url for r in _drain_start(spider))

    assert urls == ["https://rev.test/1", "https://rev.test/2"]


def test_start_with_no_files_yields_nothing():
    assert _drain_start(_spider()) == []


# --- parse_review() --------------------------------------------------------


def test_a_page_becomes_a_raw_item():
    item = _item()

    assert isinstance(item, RawItem)
    assert is_item(item)
    assert item.url == REVIEW_URL
    assert item.spider_slug == "review-links"
    assert "Dauerbrenner" in item.raw_text


def test_raw_html_is_the_article_not_the_page():
    item = _item()

    assert "<p>" in item.raw_html
    assert "Dauerbrenner" in item.raw_html
    # nav, footer and the reader-comment section are boilerplate, gone.
    assert "Impressum" not in item.raw_html
    assert "Leserkommentare" not in item.raw_html
    assert len(item.raw_html) < len(REVIEW_HTML)


def test_the_outlet_is_left_for_the_load_step_but_the_host_is_recorded():
    item = _item()

    assert item.outlet_slug is None
    assert item.extra["host"] == "www.spieletest.at"
    assert item.og_site_name == "spieletest.at"


def test_the_pointing_rows_are_carried_and_the_game_name_reaches_tags():
    spider = _spider()
    spider.tag_fields = ("name",)
    rows = [{"name": "Catan", "year": 1995}, {"name": "Catan: Seafarers"}]

    out = spider.parse_review(_response(), rows=rows)
    assert out is not None
    item = out[0]

    assert item.extra["source_rows"] == rows
    assert item.tags == ["Catan", "Catan: Seafarers"]


def test_metadata_comes_off_the_page():
    from datetime import UTC, datetime

    item = _item()

    assert item.language == "de"
    assert item.locale == "de-AT"
    # htmldate resolves to the day; the meta's time-of-day is dropped.
    assert item.published_at == datetime(2011, 3, 14, tzinfo=UTC)


def test_reader_comments_never_reach_the_text():
    item = _item()

    assert "Sterne" not in item.raw_text
    assert "Hans" not in item.raw_text


def test_headings_survive_as_markdown_so_a_verdict_section_stays_findable():
    item = _item()

    assert "## Fazit" in item.raw_text


def test_a_non_text_response_is_skipped():
    from scrapy.http import Response

    response = Response(url=REVIEW_URL, request=Request(REVIEW_URL))
    assert _spider().parse_review(response, rows=[{}]) is None


def test_a_page_with_nothing_to_extract_is_skipped():
    html = "<html lang='de'><head><title>t</title></head><body></body></html>"
    assert _item(html=html) is None


def test_thin_content_still_becomes_an_item_for_the_llm_to_judge():
    """Deciding a blurb is not a review is the extraction step's call, not the spider's."""
    html = "<html lang='de'><body><article><p>Nettes Spiel.</p></article></body></html>"
    assert _item(html=html) is not None


# --- subclassing -----------------------------------------------------------


def test_a_subclass_restricts_the_carried_fields_but_keeps_tag_fields():
    class Narrow(ReviewLinksSpider):
        name = "narrow-links"
        url_column = "link"
        context_fields = ("year",)
        tag_fields = ("game",)

    spider = Narrow()
    row = {"link": "https://x.test", "game": "Catan", "year": 1995, "junk": "drop me"}

    context = spider._context(row)

    assert context == {"year": 1995, "game": "Catan"}


def test_the_class_declares_no_allowed_domains():
    """OffsiteMiddleware would otherwise drop every request the spider makes."""
    assert not getattr(ReviewLinksSpider, "allowed_domains", None)
