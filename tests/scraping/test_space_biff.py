"""Tests for the SPACE-BIFF! spider.

The HTML here is written for the test, not copied from the site — it carries
the shapes the spider depends on, nothing else.
"""

import asyncio
import re
from datetime import UTC, datetime

from itemadapter import is_item
from scrapy.http import HtmlResponse, Request
from scrapy.utils.spider import iterate_spider_output

from finalscoring.scraping.item import RawItem
from finalscoring.scraping.spiders import SpaceBiffSpider
from finalscoring.scraping.spiders.space_biff import category_slug, is_review, published_at

BASE_URL = "https://spacebiff.com/"
REVIEW_URL = "https://spacebiff.com/2026/08/26/thunder-road-ignition/"

INDEX_HTML = f"""
<html><body>
<div id="content">
  <div class="post-wrapper">
    <h2 class="post-title"><a href="{REVIEW_URL}" rel="bookmark">More Thunder! Thunderer!</a></h2>
  </div>
  <div class="post-wrapper">
    <h2 class="post-title"><a href="{BASE_URL}2026/08/25/hench/" rel="bookmark">Mooks</a></h2>
  </div>
  <div class="post-navigation">
    <div class="nav-previous"><a href="{BASE_URL}page/2/">&larr; Older Posts</a></div>
    <div class="nav-next"></div>
  </div>
</div>
</body></html>
"""

LAST_INDEX_HTML = f"""
<html><body>
<div id="content">
  <div class="post-wrapper">
    <h2 class="post-title"><a href="{BASE_URL}2011/09/20/rps-ascension-setup/" rel="bookmark">Setup</a></h2>
  </div>
  <div class="post-navigation">
    <div class="nav-previous"></div>
    <div class="nav-next"><a href="{BASE_URL}page/184/">Newer Posts &rarr;</a></div>
  </div>
</div>
</body></html>
"""

REVIEW_HTML = """
<html lang="en"><head>
  <title>More Thunder! Thunderer! | SPACE-BIFF!</title>
  <meta property="article:published_time" content="2026-08-27T00:11:51+00:00" />
  <meta property="og:image" content="https://spacebiff.com/wp-content/uploads/2026/08/header.jpg" />
  <meta property="og:site_name" content="SPACE-BIFF!" />
</head><body>
  <div class="post-wrapper">
    <h1 class="single-title">More Thunder! Thunderer!</h1>
    <div class="entry clear-block">
      <p>Thunder Road: Ignition is lean and muscular.</p>
    </div>
  </div>
  <div class="post-utility">
    <p class="details">
      Posted on August 26, 2026, in <a href="https://spacebiff.com/category/board-game/" rel="category tag">Board Game</a>
      and tagged <a href="https://spacebiff.com/tag/board-games/" rel="tag">Board Games</a>,
      <a href="https://spacebiff.com/tag/restoration-games/" rel="tag">Restoration Games</a>. Bookmark.
    </p>
  </div>
</body></html>
"""

PODCAST_HTML = """
<html lang="en"><head><title>Space-Cast! #58 | SPACE-BIFF!</title></head><body>
  <div class="post-wrapper">
    <h1 class="single-title">Space-Cast! #58. Postmarks</h1>
    <div class="entry clear-block"><p>This week on the show.</p></div>
  </div>
  <div class="post-utility">
    <p class="details">
      Posted on August 20, 2026, in <a href="https://spacebiff.com/category/board-game/" rel="category tag">Board Game</a>,
      <a href="https://spacebiff.com/category/podcast/" rel="category tag">Podcast</a>
      and tagged <a href="https://spacebiff.com/tag/board-games/" rel="tag">Board Games</a>. Bookmark.
    </p>
  </div>
</body></html>
"""


def _response(html: str, url: str = REVIEW_URL) -> HtmlResponse:
    return HtmlResponse(url=url, body=html, encoding="utf-8", request=Request(url))


def _spider() -> SpaceBiffSpider:
    return SpaceBiffSpider()


def _item(html: str, url: str = REVIEW_URL):
    out = _spider().parse_review(_response(html, url))
    return out[0] if out else None


def test_category_slug_reads_the_trailing_path_segment():
    assert category_slug("https://spacebiff.com/category/board-game/") == "board-game"
    assert category_slug("https://spacebiff.com/category/board-game") == "board-game"
    assert category_slug(None) is None
    assert category_slug("") is None


def test_is_review_requires_board_game_and_excludes_columns():
    assert is_review({"board-game"})
    assert is_review({"board-game", "retrospective"}) is False
    assert is_review({"podcast"}) is False


def test_published_at_parses_the_offset_timestamp():
    assert published_at("2026-08-27T00:11:51+00:00") == datetime(2026, 8, 27, 0, 11, 51, tzinfo=UTC)
    assert published_at(None) is None
    assert published_at("not a date") is None


def test_index_yields_a_request_per_post_and_follows_older_posts():
    results = list(_spider().parse_index(_response(INDEX_HTML, BASE_URL)))

    urls = [r.url for r in results]
    assert REVIEW_URL in urls
    assert f"{BASE_URL}2026/08/25/hench/" in urls
    assert f"{BASE_URL}page/2/" in urls


def test_index_requests_are_not_deduplicated():
    """An index page is not content; JOBDIR would otherwise stall every later run."""
    results = list(_spider().parse_index(_response(INDEX_HTML, BASE_URL)))

    older = next(r for r in results if r.url == f"{BASE_URL}page/2/")
    assert older.dont_filter is True


def test_the_last_index_page_has_no_older_posts_link():
    results = list(_spider().parse_index(_response(LAST_INDEX_HTML, BASE_URL)))

    assert all("page/" not in r.url for r in results)


def test_start_seeds_both_the_sitemap_and_the_archive():
    """The sitemap stops at mid-2019; the archive seed is what reaches the rest."""

    async def drain() -> list[str]:
        return [request.url async for request in _spider().start()]

    urls = asyncio.run(drain())

    assert f"{BASE_URL}sitemap.xml" in urls
    assert BASE_URL in urls


def test_sitemap_rule_matches_dated_posts_only():
    """The sitemap also lists the front page and a few standalone pages."""
    (pattern, callback) = SpaceBiffSpider.sitemap_rules[0]

    assert re.search(pattern, f"{BASE_URL}2015/10/06/samurai/")
    assert not re.search(pattern, f"{BASE_URL}about/")
    assert callback == "parse_review"


def test_a_review_becomes_an_item():
    item = _item(REVIEW_HTML)

    assert item is not None
    assert item.url == REVIEW_URL
    assert item.spider_slug == "space-biff"
    assert item.title == "More Thunder! Thunderer!"
    assert "lean and muscular" in item.raw_text
    assert item.published_at == datetime(2026, 8, 27, 0, 11, 51, tzinfo=UTC)
    assert item.image_url == "https://spacebiff.com/wp-content/uploads/2026/08/header.jpg"


def test_the_outlet_and_language_are_known_at_scrape_time():
    item = _item(REVIEW_HTML)

    assert item.outlet_slug == "space-biff"
    assert item.language == "en"
    assert item.og_site_name == "SPACE-BIFF!"


def test_categories_and_tags_reach_the_model_through_tags():
    item = _item(REVIEW_HTML)

    assert "Board Game" in item.tags
    assert "Board Games" in item.tags
    assert "Restoration Games" in item.tags
    assert item.extra == {"categories": ["board-game"]}


def test_a_podcast_episode_is_not_a_review():
    """Board Game is on every podcast post too; Podcast is what excludes it."""
    assert _item(PODCAST_HTML) is None


def test_the_filter_can_be_turned_off():
    spider = _spider()
    spider.reviews_only = False

    out = spider.parse_review(_response(PODCAST_HTML))

    assert out is not None


def test_a_page_with_no_entry_content_is_skipped():
    html = REVIEW_HTML.replace(
        '<div class="entry clear-block">\n      <p>Thunder Road: Ignition is lean and muscular.</p>\n    </div>',
        "",
    )

    assert _item(html) is None


def test_items_are_yielded_as_raw_items():
    """The declared contract is what actually flows, and Scrapy can export it."""
    item = _item(REVIEW_HTML)

    assert isinstance(item, RawItem)
    assert is_item(item)


def test_a_raw_item_is_never_returned_bare():
    """Pydantic models are iterable, so Scrapy shreds one into (name, value) pairs."""
    item = RawItem(url=REVIEW_URL, spider_slug="space-biff", raw_text="hi")

    assert len(list(iterate_spider_output(item))) > 1
    assert list(iterate_spider_output((item,))) == [item]
