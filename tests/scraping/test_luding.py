"""Tests for the luding.org review-links spider.

Rows here match the shape of Recommend.Games' `luding_GameItem.jl`: list-valued
`designer`/`publisher`/`review_url`, an `int` or missing `bgg_id`.
"""

import asyncio
import json

from scrapy import Request
from scrapy.http import HtmlResponse

from finalscoring.scraping.spiders import LudingSpider

_PAGE = (
    "<html lang='de'><head><title>Drachenfels</title></head><body><article>"
    "<p>Ein alter Klassiker, der auch heute noch am Tisch funktioniert und "
    "immer wieder gern hervorgeholt wird.</p></article></body></html>"
)

ROW = {
    "name": "Drachenfels",
    "year": 1986,
    "designer": ["Leo Colovini", "Alex Randolph"],
    "publisher": ["Schmidt"],
    "artist": None,
    "game_type": ["Board"],
    "bgg_id": None,
    "luding_id": 6,
    "url": "https://www.luding.org/cgi-bin/GameData.py/ENgameid/6",
    "external_link": None,
    "description": "Ein langer Regeltext den wir nicht mitschleppen wollen.",
    "review_url": [
        "http://www.superfred.de/drachenfels.html",
        "http://sunsite.informatik.rwth-aachen.de/keirat/txt/D/Drachenf.html",
    ],
}


def _spider() -> LudingSpider:
    return LudingSpider()


def _drain_start(spider: LudingSpider) -> list[Request]:
    async def go() -> list[Request]:
        return [request async for request in spider.start()]

    return asyncio.run(go())


def test_the_review_url_column_is_read():
    assert LudingSpider.url_column == "review_url"


def test_the_carried_context_is_the_matching_fields_not_the_rules_text():
    context = _spider()._context(ROW)

    assert context == {
        "name": "Drachenfels",
        "year": 1986,
        "designer": ["Leo Colovini", "Alex Randolph"],
        "publisher": ["Schmidt"],
        "artist": None,
        "game_type": ["Board"],
        "bgg_id": None,
        "luding_id": 6,
        "url": "https://www.luding.org/cgi-bin/GameData.py/ENgameid/6",
    }
    assert "description" not in context
    assert "review_url" not in context


def test_a_row_becomes_a_game_hint():
    game = _spider().row_game(ROW)

    assert game is not None
    assert game.titles == ["Drachenfels"]
    assert game.designers == ["Leo Colovini", "Alex Randolph"]
    assert game.publishers == ["Schmidt"]
    assert game.categories == ["Board"]
    assert game.year_published == 1986
    assert game.bgg_id is None
    assert game.external_ids == {
        "luding_id": "6",
        "luding_url": "https://www.luding.org/cgi-bin/GameData.py/ENgameid/6",
    }
    assert game.source == "luding row"


def test_a_bgg_id_in_the_row_is_carried_through():
    game = _spider().row_game({**ROW, "bgg_id": 1339})

    assert game is not None
    assert game.bgg_id == 1339


def test_an_implausible_row_year_is_dropped():
    game = _spider().row_game({**ROW, "year": 12})  # does not raise

    assert game is not None
    assert game.year_published is None


def test_a_row_with_nothing_to_identify_the_game_is_none():
    assert _spider().row_game({"luding_id": 6, "url": "https://luding.org/x"}) is None


def test_the_fetched_page_becomes_an_item_with_a_game_hint_per_row():
    url = "http://www.superfred.de/drachenfels.html"
    response = HtmlResponse(url=url, body=_PAGE.encode(), encoding="utf-8", request=Request(url))
    expansion = {**ROW, "name": "Drachenfels: Neue Abenteuer", "bgg_id": 4242}

    out = _spider().parse_review(response, rows=[_spider()._context(ROW), expansion])
    assert out is not None
    (item,) = out

    assert item.source_host == "www.superfred.de"
    assert item.outlet_slug is None
    games = [hint.game for hint in item.reviews]
    assert all(g is not None for g in games)
    assert [g.titles[0] for g in games if g] == ["Drachenfels", "Drachenfels: Neue Abenteuer"]
    assert [g.bgg_id for g in games if g] == [None, 4242]


def test_start_reads_the_file_and_fans_out_over_review_url(tmp_path):
    src = tmp_path / "luding_GameItem.jl"
    src.write_text(json.dumps(ROW) + "\n")
    spider = _spider()
    spider.files = str(src)

    requests = _drain_start(spider)

    assert {r.url for r in requests} == {
        "http://www.superfred.de/drachenfels.html",
        "http://sunsite.informatik.rwth-aachen.de/keirat/txt/D/Drachenf.html",
    }
    rows = requests[0].cb_kwargs["rows"]
    assert rows == [
        {
            "name": "Drachenfels",
            "year": 1986,
            "designer": ["Leo Colovini", "Alex Randolph"],
            "publisher": ["Schmidt"],
            "artist": None,
            "game_type": ["Board"],
            "bgg_id": None,
            "luding_id": 6,
            "url": "https://www.luding.org/cgi-bin/GameData.py/ENgameid/6",
        }
    ]


def test_a_shared_review_url_carries_every_game_that_points_at_it(tmp_path):
    base = dict(ROW)
    base["review_url"] = ["http://sunsite.informatik.rwth-aachen.de/keirat/txt/D/Drachenf.html"]
    expansion = dict(base)
    expansion["name"] = "Drachenfels: Neue Abenteuer"
    expansion["luding_id"] = 9999

    src = tmp_path / "luding_GameItem.jl"
    src.write_text(json.dumps(base) + "\n" + json.dumps(expansion) + "\n")
    spider = _spider()
    spider.files = str(src)

    (request,) = _drain_start(spider)

    assert [row["name"] for row in request.cb_kwargs["rows"]] == [
        "Drachenfels",
        "Drachenfels: Neue Abenteuer",
    ]


def test_the_luding_scrape_path_is_not_hardcoded():
    """Where the R.G. scrape lives is an unsettled integration question."""
    assert not getattr(LudingSpider, "files", None)
