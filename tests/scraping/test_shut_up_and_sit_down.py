"""Tests for the Shut Up & Sit Down spider.

The HTML here is written for the test, not copied from the site — it carries
the shapes the spider depends on, nothing else.
"""

from datetime import datetime

from itemadapter import is_item
from scrapy.http import HtmlResponse, Request

from finalscoring.scraping.item import RawItem
from finalscoring.scraping.spiders import ShutUpAndSitDownSpider
from finalscoring.scraping.spiders.shut_up_and_sit_down import (
    category_slug,
    page_number,
    published_at,
)

BASE_URL = "https://www.shutupandsitdown.com/"
REVIEWS_URL = f"{BASE_URL}category/reviews/"
REVIEW_URL = f"{BASE_URL}review-elysium/"

REVIEW_HTML = f"""
<html><head>
  <title>Review: Elysium - Shut Up &amp; Sit Down</title>
  <meta name="description" content="Quinns walks into a shop." />
  <meta property="og:title" content="Review: Elysium - Shut Up &amp; Sit Down" />
  <meta property="og:site_name" content="Shut Up &amp; Sit Down" />
  <meta property="og:locale" content="en_US" />
  <meta property="og:image" content="{BASE_URL}wp-content/uploads/2019/06/elysium.jpg" />
</head><body>
  <header class="entry-header">
    <h1 class="entry-title" itemprop="headline">Review: Elysium</h1>
    <div class="fun-tags"> poseidon the god of jerks, apollo the god of extra bits</div>
  </header>
  <div class="entry-content" itemprop="text">
    <span class="entry-date">April 23, 2015</span>
    <span class="author">webdeveloper</span>
    <span class="meta-category"> <a href="{BASE_URL}category/reviews/" rel="tag">Reviews</a></span>
    <span class="comment-counts"><a href="{REVIEW_URL}#comments">92 comment(s)</a></span>
    <div class="meta-tags"> <a href="{BASE_URL}tag/elysium/" rel="tag">Elysium</a>
      <a href="{BASE_URL}tag/heavy-games/" rel="tag">Heavy Games</a></div>
    <p><strong>Quinns:</strong> So you walk into your local board game shop.</p>
    <p>You scan the shelves. THE END</p>
  </div>
</body></html>
"""

PODCAST_HTML = REVIEW_HTML.replace(
    f'<span class="meta-category"> <a href="{BASE_URL}category/reviews/" rel="tag">Reviews</a></span>',
    f'<span class="meta-category"> <a href="{BASE_URL}category/podcast/" rel="tag">Podcast</a></span>',
)


def _entry(url: str, title: str) -> str:
    return f'<article><h2 class="entry-title"><a href="{url}" rel="bookmark">{title}</a></h2></article>'


LIST_HTML = f"""
<html><body>
  {_entry(f"{BASE_URL}miniatures-game-review-gaslands-refueled/", "Miniatures Game Review")}
  {_entry(REVIEW_URL, "Review: Elysium")}
  <div class="nav-links">
    <span class="page-numbers current">1</span>
    <a class="page-numbers" href="{REVIEWS_URL}page/2/">2</a>
    <span class="page-numbers dots">&hellip;</span>
    <a class="page-numbers" href="{REVIEWS_URL}page/22/">22</a>
    <a class="next page-numbers" href="{REVIEWS_URL}page/2/">Next</a>
  </div>
</body></html>
"""

LAST_LIST_HTML = f"""
<html><body>
  {_entry(f"{BASE_URL}review-dixit/", "Review: Dixit")}
  <div class="nav-links">
    <a class="prev page-numbers" href="{REVIEWS_URL}page/21/">Previous</a>
    <a class="page-numbers" href="{REVIEWS_URL}page/21/">21</a>
    <span class="page-numbers current">22</span>
  </div>
</body></html>
"""

TRUNCATED_LIST_HTML = f"""
<html><body>
  {_entry(f"{BASE_URL}review-catan/", "Review: Catan")}
  <div class="nav-links">
    <span class="page-numbers current">5</span>
    <a class="page-numbers" href="{REVIEWS_URL}page/22/">22</a>
  </div>
</body></html>
"""


def _response(html: str, url: str = REVIEW_URL) -> HtmlResponse:
    return HtmlResponse(url=url, body=html.encode(), encoding="utf-8", request=Request(url))


def _spider() -> ShutUpAndSitDownSpider:
    return ShutUpAndSitDownSpider()


def _item(html: str = REVIEW_HTML, url: str = REVIEW_URL):
    out = _spider().parse_review(_response(html, url))
    return out[0] if out else None


def test_category_slug_reads_the_trailing_path_segment():
    assert category_slug(f"{BASE_URL}category/reviews/") == "reviews"
    assert category_slug(f"{BASE_URL}category/our-favourites") == "our-favourites"
    assert category_slug(None) is None


def test_page_number_reads_the_pagination_segment():
    assert page_number(f"{REVIEWS_URL}page/22/") == 22
    assert page_number(REVIEWS_URL) is None
    assert page_number(None) is None


def test_published_at_parses_the_month_name_without_the_locale():
    assert published_at("April 23, 2015") == datetime(2015, 4, 23)
    assert published_at("Posted March 1, 2020 by someone") == datetime(2020, 3, 1)
    assert published_at("Not a date") is None
    assert published_at("Foobuary 3, 2020") is None
    assert published_at(None) is None


def test_a_review_becomes_an_item():
    item = _item()

    assert item is not None
    assert item.url == REVIEW_URL
    assert item.spider_slug == "shut-up-and-sit-down"
    assert item.title == "Review: Elysium"
    assert item.published_at == datetime(2015, 4, 23)
    assert item.image_url == f"{BASE_URL}wp-content/uploads/2019/06/elysium.jpg"


def test_the_outlet_and_language_are_known_at_scrape_time():
    item = _item()

    assert item.outlet_slug == "shut-up-and-sit-down"
    assert item.language == "en"
    assert item.locale == "en-US"
    assert item.og_site_name == "Shut Up & Sit Down"


def test_the_theme_meta_strip_never_reaches_the_text():
    """entry-date / author / category / comment spans sit at the top of the body."""
    item = _item()

    assert item.raw_text.startswith("Quinns:")
    assert "webdeveloper" not in item.raw_text
    assert "comment(s)" not in item.raw_text
    assert "April 23, 2015" not in item.raw_text


def test_tags_carry_the_post_tags_the_categories_and_the_joke_subtitle():
    item = _item()

    assert "Elysium" in item.tags
    assert "Heavy Games" in item.tags
    assert "Reviews" in item.tags
    assert "poseidon the god of jerks, apollo the god of extra bits" in item.tags


def test_a_migrated_byline_is_dropped_but_a_real_one_is_kept():
    assert "author" not in _item().extra

    html = REVIEW_HTML.replace(">webdeveloper<", ">Quintin Smith<")
    assert _item(html).extra["author"] == "Quintin Smith"


def test_a_post_outside_the_reviews_category_is_skipped():
    assert _item(PODCAST_HTML) is None


def test_the_category_filter_can_be_turned_off():
    spider = _spider()
    spider.reviews_only = False

    assert spider.parse_review(_response(PODCAST_HTML)) is not None


def test_a_page_with_no_entry_content_is_skipped():
    assert _item("<html><body><p>nothing</p></body></html>") is None


def test_the_list_yields_one_request_per_review_and_follows_next():
    results = list(_spider().parse_list(_response(LIST_HTML, REVIEWS_URL)))

    review_urls = [r.url for r in results if "/category/" not in r.url]
    assert review_urls == [
        f"{BASE_URL}miniatures-game-review-gaslands-refueled/",
        REVIEW_URL,
    ]
    next_pages = [r for r in results if "/category/" in r.url]
    assert [r.url for r in next_pages] == [f"{REVIEWS_URL}page/2/"]
    assert next_pages[0].dont_filter is True


def test_the_last_list_page_has_no_next_and_does_not_warn(caplog):
    url = f"{REVIEWS_URL}page/22/"
    results = list(_spider().parse_list(_response(LAST_LIST_HTML, url)))

    assert all("/category/" not in r.url for r in results)
    assert "stopped" not in caplog.text


def test_a_walk_that_stops_early_warns(caplog):
    url = f"{REVIEWS_URL}page/5/"
    list(_spider().parse_list(_response(TRUNCATED_LIST_HTML, url)))

    assert "review walk stopped at page 5 of 22" in caplog.text


def test_an_extra_class_on_the_title_still_yields_the_review():
    """A theme tweak to `entry-title x` must not silently drop a page's links."""
    html = LIST_HTML.replace('class="entry-title"', 'class="entry-title has-extra"')

    results = list(_spider().parse_list(_response(html, REVIEWS_URL)))

    assert any(r.url == REVIEW_URL for r in results)


def test_a_list_page_with_no_reviews_warns(caplog):
    html = '<html><body><div class="nav-links"></div></body></html>'

    list(_spider().parse_list(_response(html, REVIEWS_URL)))

    assert "yielded no reviews" in caplog.text


def test_items_are_yielded_as_raw_items():
    """The declared contract is what actually flows, and Scrapy can export it."""
    item = _item()

    assert isinstance(item, RawItem)
    assert is_item(item)
