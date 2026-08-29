"""Tests for the H@LL9000 spider.

The HTML here is written for the test, not copied from the site — it carries
the shapes the spider depends on, nothing else.
"""

from datetime import datetime

from itemadapter import is_item
from scrapy.http import HtmlResponse, Request
from scrapy.utils.spider import iterate_spider_output

from finalscoring.scraping.item import RawItem
from finalscoring.scraping.spiders import Hall9000Spider
from finalscoring.scraping.spiders.hall9000 import (
    online_since,
    review_href,
    score_from_src,
)

BASE_URL = "https://www.hall9000.de/"
REVIEW_URL = f"{BASE_URL}html/spiel/the_royal_society_of_archeology"
LIST_URL = f"{BASE_URL}html/spielsucheliste.html?topic=1&sort=7&dir=1&displaytype=2&page/0"


def _noten(critic: str, date: str, a: int, s: int, i: int, e: int, sr: int, comment: str) -> str:
    return f"""
    <div class="rezi_noten"><table>
      <tr><td class="rating"><img class="icon_aufmachung" src="/html/images/w{a}_w.gif"></td>
      <td class="rating"><img class="icon_spielbarkeit" src="/html/images/w{s}_w.gif"></td>
      <td class="rating"><img class="icon_interaktion" src="/html/images/w{i}_w.gif"></td>
      <td class="rating"><img class="icon_einfluss" src="/html/images/w{e}_w.gif"></td>
      <td class="rating"><img class="icon_spielreiz" src="/html/images/w{sr}_b.gif"></td>
      <td class="comment"><span class="date">{date}</span> von
        <a href="{BASE_URL}html/wertung/{critic.replace(" ", "+")}">{critic}</a> - {comment}</td></tr>
    </table></div>"""


REVIEW_HTML = f"""
<html><head><title>H@LL9000 - Rezension/Kritik Spiel: The Royal Society of Archeology (21568)</title>
<meta name="description" content="Rezension/Kritik Spiel: The Royal Society of Archeology." />
</head><body>
<div class="rezi"><div class="single_page"><div class="inner">
  <script type="application/ld+json">{{"@type":"Game","name":"The Royal Society of Archeology"}}</script>
  <p><b>Rezension/Kritik</b> - Online seit 28.04.2026. Dieser Artikel wurde 3203 mal aufgerufen.</p>
  <h2>The Royal Society of Archeology
    <table class="rezi_head"><tr><td>links</td></tr></table>
  </h2>
  <div class="spiel_info"><table class="no_border">
    <tr><td class="label">Autor:</td><td class="data"><a href="#">Eric Jumel</a></td></tr>
    <tr><td class="label">Verlag:</td><td class="data"><a href="#">HUCH!</a><br>Atalia<br></td></tr>
    <tr><td class="label">Rezension:</td><td class="data"><a href="{BASE_URL}html/spiel/21568">Michael Andersch</a></td></tr>
    <tr><td class="label">Jahr:</td><td class="data">2025</td></tr>
    <tr><td class="label">Bewertung:</td><td class="data"><img alt="5,5"><span>5,5 H@LL9000</span></td></tr>
    <tr><td class="label"></td><td class="data"><img alt="6,0"><span>6,0 Leser</span></td></tr>
  </table></div>
  <div class="spiele_tags"><span class="spiele_tag" style="font-weight:bold;">Tags:</span>
    <a href="#"><span class="spiele_tag">Arbeitereinsatz</span></a>
    <a href="#"><span class="spiele_tag">Erforschung</span></a></div>
  <img src="/html/thumb/220/220/rubriken/spiele/rezensionen/kritiken/the_royal_society_of_archeology_cover.jpg" alt="The Royal Society of Archeology">
  <div id="20034" class="textblock"><h3>Spielziel</h3><p>Wir erforschen die Welt.</p></div>
  <div id="20035" class="textblock"><h3>Ablauf</h3><p>Drei Forscher einsetzen.</p>
    <script>var embed = "a video embed inside the prose";</script></div>
  <div id="20036" class="textblock"><h3>Fazit</h3><p>Thematisch top, Anleitung mies.</p></div>
  <h3 id="hall_noten">H@LL9000-Bewertungen</h3>
  <p>H@LL9000 Wertung: 5,5, 4 Bewertung(en)</p>
  {_noten("Michael Andersch", "11.04.26", 5, 4, 4, 5, 5, "Grauselig korrekturgelesene Regel.")}
  {_noten("Andrea Poganiuch", "02.08.26", 6, 5, 4, 5, 6, "Sehr schoen.")}
  <h3 id="leser_noten">Leserbewertungen</h3>
  {_noten("Leser Lieschen", "01.01.26", 1, 1, 1, 1, 1, "Reader opinion, must not leak.")}
</div></div></div>
<div class="footer">nav</div>
</body></html>
"""

LIST_HTML = f"""
<html><body>
<p><b>Suchergebnis: 4091 Treffer</b></p>
<div class="inner">
  <h5 class="entry_title"><span class="date">27.08.26</span>
    <a href="{BASE_URL}html/spiel/four_planets" title="Four Planets">Four Planets</a></h5>
  <div class="detail"><div class="spiel_info"><table><tr>
    <td class="label">Rezension:</td>
    <td class="data"><a href="{BASE_URL}html/spiel/21450">Günter Berberich</a></td></tr></table></div>
    <div class="image"><a href="{BASE_URL}html/spiel/four_planets"><img src="x.jpg"></a></div>
  </div>
  <h5 class="entry_title"><span class="date">26.08.26</span>
    <a href="{BASE_URL}html/spiel/noch_x_mal" title="Noch X Mal">Noch X Mal</a></h5>
</div>
<div class="navigation_bar">
  <a class="button" href="{LIST_URL}">Start</a>
  <a class="button" href="{BASE_URL}html/spielsucheliste.html?topic=1&sort=7&dir=1&displaytype=2&page/1">2</a>
</div>
</body></html>
"""

EMPTY_LIST_HTML = """
<html><body><p><b>Suchergebnis: 4091 Treffer</b></p>
<div class="inner"></div></body></html>
"""


def _response(html: str, url: str = REVIEW_URL) -> HtmlResponse:
    return HtmlResponse(url=url, body=html.encode(), encoding="utf-8", request=Request(url))


def _spider() -> Hall9000Spider:
    return Hall9000Spider()


def _item(html: str = REVIEW_HTML, url: str = REVIEW_URL):
    out = _spider().parse_review(_response(html, url))
    return out[0] if out else None


def test_review_href_matches_slug_permalinks_only():
    assert review_href("https://www.hall9000.de/html/spiel/four_planets")
    assert review_href("/html/spiel/noch_x_mal")
    assert not review_href("https://www.hall9000.de/html/spiel/21450")  # the numeric alias
    assert not review_href("https://www.hall9000.de/html/spielsucheliste.html?autor=X")
    assert not review_href(None)


def test_online_since_parses_the_german_date():
    assert online_since("Online seit 28.04.2026. Aufgerufen: 5") == datetime(2026, 4, 28)
    assert online_since("no date here") is None
    assert online_since(None) is None


def test_score_from_src_reads_the_number_from_the_filename():
    assert score_from_src("/html/images/w5_w.gif") == 5
    assert score_from_src("/html/images/w6_b.gif") == 6
    assert score_from_src("/html/images/meeple.gif") is None
    assert score_from_src(None) is None


def test_a_review_becomes_an_item():
    item = _item()

    assert item is not None
    assert item.url == REVIEW_URL
    assert item.spider_slug == "hall9000"
    assert item.title == "The Royal Society of Archeology"
    assert item.published_at == datetime(2026, 4, 28)
    assert item.outlet_slug == "hall9000"
    assert item.language == "de"
    assert item.image_url.endswith("the_royal_society_of_archeology_cover.jpg")


def test_the_prose_review_reaches_the_model():
    item = _item()

    assert "Wir erforschen die Welt." in item.raw_text
    assert "Thematisch top" in item.raw_text
    assert "Eric Jumel" in item.raw_text  # the info line


def test_script_bodies_never_reach_the_text():
    """A JSON-LD block sits beside the prose; embeds can sit inside it."""
    item = _item()

    assert "@type" not in item.raw_text
    assert "a video embed inside the prose" not in item.raw_text


def test_reader_ratings_never_reach_the_item():
    """Mantra #1: critic opinion only, never community ratings."""
    item = _item()

    assert "Reader opinion, must not leak" not in item.raw_text
    assert "Leser Lieschen" not in item.raw_text
    assert all(r["critic"] != "Leser Lieschen" for r in item.extra["critic_ratings"])
    assert "6,0 Leser" not in str(item.extra["info"])


def test_each_critic_note_is_kept_structured():
    item = _item()

    ratings = item.extra["critic_ratings"]
    assert [r["critic"] for r in ratings] == ["Michael Andersch", "Andrea Poganiuch"]
    andersch = ratings[0]
    assert andersch["date"] == "11.04.26"
    assert andersch["scores"] == {
        "aufmachung": 5,
        "spielbarkeit": 4,
        "interaktion": 4,
        "einfluss": 5,
        "spielreiz": 5,
    }
    assert andersch["comment"] == "Grauselig korrekturgelesene Regel."


def test_the_verdicts_reach_the_model_through_tags():
    """The scores are image filenames; the tags are the only place they survive."""
    item = _item()

    assert "H@LL9000-Gesamtwertung: 5,5 von 6" in item.tags
    assert (
        "Michael Andersch (H@LL9000, je 1-6): Aufmachung 5, Spielbarkeit 4, "
        "Interaktion 4, Einfluss 5, Spielreiz 5"
    ) in item.tags
    assert "Arbeitereinsatz" in item.tags
    assert "Erforschung" in item.tags
    assert "Tags:" not in item.tags


def test_a_page_with_no_review_block_is_skipped():
    assert _item("<html><body><p>Nichts</p></body></html>") is None


def test_the_list_yields_one_request_per_review_and_follows_the_next_page():
    results = list(_spider().parse_list(_response(LIST_HTML, LIST_URL), page=0, found=0))

    review_urls = [r.url for r in results if "/html/spiel/" in r.url]
    assert review_urls == [
        f"{BASE_URL}html/spiel/four_planets",
        f"{BASE_URL}html/spiel/noch_x_mal",
    ]
    next_pages = [r for r in results if "spielsucheliste" in r.url]
    assert len(next_pages) == 1
    assert next_pages[0].url.endswith("page/1")
    assert next_pages[0].cb_kwargs == {"page": 1, "found": 2}
    assert next_pages[0].dont_filter is True


def test_the_walk_stops_when_a_list_page_has_no_reviews():
    results = list(_spider().parse_list(_response(EMPTY_LIST_HTML, LIST_URL), page=137, found=4091))

    assert results == []


def test_a_short_walk_warns_instead_of_looking_like_success(caplog):
    """One blank response must not silently truncate a 137-page walk."""
    list(_spider().parse_list(_response(EMPTY_LIST_HTML, LIST_URL), page=50, found=1500))

    assert "stopped at page 50 with 1500 of 4091" in caplog.text


def test_items_are_yielded_as_raw_items():
    """The declared contract is what actually flows, and Scrapy can export it."""
    item = _item()

    assert isinstance(item, RawItem)
    assert is_item(item)


def test_a_raw_item_is_never_returned_bare():
    """Pydantic models are iterable, so Scrapy shreds one into (name, value) pairs."""
    item = RawItem(url=REVIEW_URL, spider_slug="hall9000", raw_text="hi")

    assert len(list(iterate_spider_output(item))) > 1
    assert list(iterate_spider_output((item,))) == [item]
