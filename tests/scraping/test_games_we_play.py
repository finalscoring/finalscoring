"""Tests for the games we play spider, against canned pages in both site eras."""

from typing import Any

import pytest
from scrapy import Request
from scrapy.http import HtmlResponse

from finalscoring.scraping.spiders.games_we_play import (
    GamesWePlaySpider,
    rating_from_image,
)

URL = "https://gamesweplay.de/dewan.html"

# The current markup: schema.org microdata alongside the rating graphic.
MODERN = """<html lang="de"><head>
<title>Das Brettspiel: Dewan | Spielekritik</title>
<meta name="Author" content="Harald Schrapers" />
<meta property="og:image" content="dewani.jpg" />
</head><body><center><div class="besprechung">
<a href="index.html"><img src="nrgamesk.gif" alt="games we play" /></a>
<div itemscope itemtype="https://schema.org/Product">
<p class="head" itemprop="name"><strong>Dewan</strong></p>
<div itemprop="review" itemscope itemtype="https://schema.org/Review">
<p><span itemprop="reviewRating" itemscope itemtype="https://schema.org/Rating">
<meta itemprop="ratingValue" content="8" />
<meta itemprop="bestRating" content="10" />
<img src="fuenf.png" alt="5 von 6" />
<img src="topspiel.png" alt="games we play Tip: Das TOPspiel"></span>
von Johannes Goupy und Yoann Levet</p>
<p>Schwierigkeit <span class="schwierigkeit">&#9724;&#9724;&#9723;&#9723;</span></p>
<p>Verpackung ++</p>
<p class="illustration">Rating: 8/10 &#9860; &neArr;</p>
<p><i><a href="https://www.spacecowboys-games.com/">Space Cowboys</a></i></p>
<p>Strategisch wichtig ist zudem, dass das Spiel abrupt enden kann.</p>
<p>&copy; <span itemprop="author">Harald Schrapers</span></p>
</div></div></div></center></body></html>"""

# Twenty years of pages that predate the microdata: the graphic is all there is.
LEGACY = """<html lang="de"><head><title>Das Brettspiel: Attika</title></head>
<body><center><div class="besprechung">
<img class="top" src="nrgamesk.gif" alt="games we play">
<p class="head"><b>Attika</b>
<p><img src="fuenf.png" alt="sch&ouml;n: 5 Punkte">von Marcel-Andr&eacute; Casasola Merkle
<p>Schwierigkeit <img src="einfach.gif" alt="einfach (ab ca. 10 Jahre)">
<p>Verpackung -
<p>Jetzt hat er sein erstes gro&szlig;es Brettspiel entworfen.
</div></center></body></html>"""

INDEX = """<html lang="de"><head><title>Deutscher Spiele Preis</title></head>
<body><center><p class="head"><b>Preise</b>
<p><a href="attika.html">Attika</a></p></center></body></html>"""


def _response(html: str, url: str = URL) -> HtmlResponse:
    return HtmlResponse(
        url=url, body=html.encode("iso-8859-1"), encoding="iso-8859-1", request=Request(url)
    )


def _spider() -> GamesWePlaySpider:
    return GamesWePlaySpider()


def _item(html: str, url: str = URL) -> Any:
    out = _spider().parse_review(_response(html, url))
    return out[0] if out else None


@pytest.mark.parametrize(
    ("src", "expected"),
    [
        ("fuenf.png", 5),
        ("vier.gif", 4),
        ("sechs.png", 6),
        ("null.png", 0),
        ("https://gamesweplay.de/drei.png", 3),
        ("  zwei.png  ", 2),
        ("FUENF.PNG", 5),
    ],
)
def test_the_filename_is_the_score(src: str, expected: int):
    """Twenty years of drifting alt text; the filename never drifted."""
    assert rating_from_image(src) == expected


@pytest.mark.parametrize("src", ["nrgamesk.gif", "dewan.jpg", "fuenfte.png", "", None])
def test_other_images_are_not_ratings(src: str | None):
    assert rating_from_image(src) is None


def test_a_modern_review_becomes_an_item():
    item = _item(MODERN)

    assert item is not None
    assert item.url == URL
    assert item.spider_slug == "games-we-play"
    assert item.title == "Das Brettspiel: Dewan | Spielekritik"
    assert "Strategisch wichtig" in item.raw_text


def test_a_legacy_review_becomes_an_item():
    """The site predates its own microdata by about fifteen years."""
    item = _item(LEGACY, "https://gamesweplay.de/attika.html")

    assert item is not None
    assert "Brettspiel entworfen" in item.raw_text


def test_an_index_page_is_not_a_review():
    """No rating graphic, no verdict — the sitemap lists these alongside reviews."""
    assert _item(INDEX, "https://gamesweplay.de/dsp20.html") is None


def test_the_filter_can_be_turned_off():
    spider = _spider()
    spider.reviews_only = False

    out = spider.parse_review(_response(INDEX, "https://gamesweplay.de/dsp20.html"))

    assert out is not None


def test_the_score_reaches_the_model_through_the_tags():
    """The verdict is a picture, so without this the review carries no score."""
    item = _item(MODERN)

    assert "Wertung: 5 von 6 Punkten" in item.tags


def test_every_verdict_on_the_page_is_captured():
    """He rates six ways at once and the prose states none of them."""
    ratings = _item(MODERN).extra["ratings"]

    assert ratings["graphic"] == {"points": 5, "max": 6, "alt": "5 von 6"}
    assert ratings["microdata"] == {"value": 8, "max": 10}
    assert ratings["signature"].startswith("Rating: 8/10")
    assert ratings["difficulty"] == {"filled": 2, "max": 4}
    assert ratings["packaging"] == "++"
    assert ratings["badge"] == "games we play Tip: Das TOPspiel"


def test_every_verdict_reaches_the_model():
    """extra is for the load step; tags are what the extractor actually sees."""
    tags = _item(MODERN).tags

    assert tags[:2] == ["Wertung: 5 von 6 Punkten", "Rating: 8/10"]
    assert any(t.startswith("Rating: 8/10") and len(t) > 12 for t in tags)
    assert "Schwierigkeit: 2 von 4" in tags
    assert "Verpackung: ++" in tags
    assert "games we play Tip: Das TOPspiel" in tags


def test_the_signature_keeps_its_die_and_arrow_verbatim():
    """They mean something to him; guessing would be worse than passing them on."""
    signature = _item(MODERN).extra["ratings"]["signature"]

    assert "\u2684" in signature
    assert "\u21d7" in signature


def test_a_legacy_review_states_its_difficulty_only_in_alt_text():
    """No microdata and no signature line; the grade is a picture's alt."""
    item = _item(LEGACY, "https://gamesweplay.de/attika.html")

    assert item.extra["ratings"]["difficulty"] == {"label": "einfach (ab ca. 10 Jahre)"}
    assert "microdata" not in item.extra["ratings"]
    assert "signature" not in item.extra["ratings"]
    assert "Schwierigkeit: einfach (ab ca. 10 Jahre)" in item.tags


def test_the_outlet_is_known_at_scrape_time():
    item = _item(MODERN)

    assert item.outlet_slug == "games-we-play"
    assert item.og_site_name == "games we play"


def test_a_relative_og_image_is_made_absolute():
    """This site writes "dewani.jpg", which is not an address."""
    assert _item(MODERN).image_url == "https://gamesweplay.de/dewani.jpg"


def test_a_page_without_an_og_image_has_none():
    assert _item(LEGACY, "https://gamesweplay.de/attika.html").image_url is None


def test_latin1_text_survives_decoding():
    """The site is ISO-8859-1 and says so; the umlauts must come out intact."""
    item = _item(LEGACY, "https://gamesweplay.de/attika.html")

    assert "großes" in item.raw_text


def test_the_masthead_is_not_mistaken_for_a_rating():
    """Every page opens with the logo image before any rating graphic."""
    assert _item(MODERN).extra["ratings"]["graphic"]["points"] == 5


# Six images, four with alt — the shape that dropped 27 reviews when src and
# alt were read as two parallel lists.
SPARSE_ALT = """<html lang="de"><head><title>Das Brettspiel: Tikal</title></head>
<body><div class="besprechung">
<img src="nrgamesk.gif" alt="games we play">
<img src="spjahr.gif">
<img src="dsp.gif" alt="Deutscher Spiele Preis">
<img src="mittel.gif" alt="mittel (ab ca. 12 Jahre)">
<img src="fuenf.png" alt="sch&ouml;n: 5 Punkte">
<img src="tikal.jpg">
<p>Ein Klassiker.</p>
</div></body></html>"""


def test_a_rating_graphic_after_an_image_without_alt_is_still_found():
    """Zipping //img/@src with //img/@alt truncated at the shorter list."""
    item = _item(SPARSE_ALT, "https://gamesweplay.de/tikal.html")

    assert item is not None
    assert item.extra["ratings"]["graphic"]["points"] == 5
    assert item.extra["ratings"]["difficulty"] == {"label": "mittel (ab ca. 12 Jahre)"}


def test_a_page_with_no_body_content_is_skipped():
    html = '<html><body><img src="fuenf.png" alt="x"></body></html>'

    assert _item(html) is None
