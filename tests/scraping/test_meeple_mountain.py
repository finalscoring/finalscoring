"""Tests for the Meeple Mountain spider.

The HTML here is written for the test, not copied from the site — it carries
the shapes the spider depends on, nothing else.
"""

import re
from datetime import datetime

from itemadapter import is_item
from scrapy.http import HtmlResponse, Request
from scrapy.utils.spider import iterate_spider_output

from finalscoring.scraping.item import RawItem
from finalscoring.scraping.spiders import MeepleMountainSpider
from finalscoring.scraping.spiders.meeple_mountain import (
    published_at,
    schema_org_rating,
    star_rating,
)

REVIEW_URL = "https://www.meeplemountain.com/reviews/tales-of-the-arabian-nights/"

REVIEW_HTML = """
<html lang="en-US"><head>
  <title>Tales of the Arabian Nights Game Review &ndash; Meeple Mountain</title>
  <meta name="description" content="Our review reveals why." />
  <meta name="author" content="Mark Iradian" />
  <meta property="og:title" content="Tales of the Arabian Nights Game Review" />
  <meta property="og:locale" content="en_US" />
  <meta property="og:site_name" content="Meeple Mountain" />
  <meta property="og:image" content="https://www.meeplemountain.com/wp-content/uploads/2026/08/header.jpg" />
  <meta property="article:published_time" content="2026-08-27T13:00:20+00:00" />
  <script type="application/ld+json">
  {"@context":"https://schema.org","@graph":[
    {"@type":"Review","reviewRating":{"@type":"Rating","ratingValue":"4.0","worstRating":"0.5","bestRating":"5.0"}},
    {"@type":"Organization","name":"Meeple Mountain"}
  ]}
  </script>
</head><body>
  <article id="post-333906" class="herald-single post-333906 reviews type-reviews
      category-adventure-board-games category-fantasy-board-games
      designers-eric-goldberg mechanisms-dice-rolling publishers-devir release_year-1247">
    <h1 class="entry-title h1">Tales of the Arabian Nights Game Review</h1>
    <div class="entry-content herald-entry-content">
      <p>This beautiful mess still doesn't make a lick of sense.</p>
      <div class="board-game-meta herald-mod-wrap">
        <div class="rating-container standalone">
          <h5>AUTHOR RATING</h5>
          <ul>
            <li class="rating" title="4.0 / 5 stars &mdash; Great - Would recommend.">
              <span class="fa fa-star"></span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </article>
</body></html>
"""


def _response(html: str, url: str = REVIEW_URL) -> HtmlResponse:
    return HtmlResponse(url=url, body=html, encoding="utf-8", request=Request(url))


def _spider() -> MeepleMountainSpider:
    return MeepleMountainSpider()


def _item(html: str = REVIEW_HTML, url: str = REVIEW_URL):
    out = _spider().parse_review(_response(html, url))
    return out[0] if out else None


def test_star_rating_splits_value_scale_and_tier():
    assert star_rating("4.0 / 5 stars — Great - Would recommend.") == {
        "value": "4.0",
        "best": "5",
        "tier": "Great - Would recommend",
    }
    assert star_rating("2.5 / 5 stars — Fair.") == {"value": "2.5", "best": "5", "tier": "Fair"}
    assert star_rating("no dash here") is None
    assert star_rating(None) is None


def test_published_at_parses_the_offset_timestamp():
    assert published_at("2026-08-27T13:00:20+00:00") == datetime.fromisoformat(
        "2026-08-27T13:00:20+00:00"
    )
    assert published_at(None) is None
    assert published_at("not a date") is None


def test_schema_org_rating_walks_the_json_ld_graph():
    rating = schema_org_rating(_response(REVIEW_HTML))

    assert rating is not None
    assert rating["ratingValue"] == "4.0"
    assert rating["bestRating"] == "5.0"


def test_schema_org_rating_is_none_without_a_review_node():
    html = REVIEW_HTML.replace('"@type":"Review"', '"@type":"NotAReview"')

    assert schema_org_rating(_response(html)) is None


def test_sitemap_rule_matches_review_permalinks_only():
    (pattern, callback) = MeepleMountainSpider.sitemap_rules[0]

    assert re.search(pattern, f"{REVIEW_URL}")
    assert not re.search(pattern, "https://www.meeplemountain.com/reviews/")
    assert callback == "parse_review"


def test_a_review_becomes_an_item():
    item = _item()

    assert item is not None
    assert item.url == REVIEW_URL
    assert item.spider_slug == "meeple-mountain"
    assert item.title == "Tales of the Arabian Nights Game Review"
    assert "beautiful mess" in item.raw_text
    assert item.published_at == datetime.fromisoformat("2026-08-27T13:00:20+00:00")
    assert item.image_url == "https://www.meeplemountain.com/wp-content/uploads/2026/08/header.jpg"


def test_the_outlet_and_language_are_known_at_scrape_time():
    item = _item()

    assert item.outlet_slug == "meeple-mountain"
    assert item.language == "en"
    assert item.locale == "en-US"
    assert item.og_site_name == "Meeple Mountain"


def test_the_verdict_reaches_the_model_through_tags():
    """The score is theme markup; without the tags the review carries no verdict."""
    item = _item()

    assert "Meeple Mountain rating: 4.0 / 5" in item.tags
    assert "Great - Would recommend" in item.tags


def test_the_rating_is_kept_structured_in_extra():
    item = _item()

    assert item.extra["rating"] == {
        "value": "4.0",
        "best": "5",
        "tier": "Great - Would recommend",
        "schema_org": {
            "@type": "Rating",
            "ratingValue": "4.0",
            "worstRating": "0.5",
            "bestRating": "5.0",
        },
    }
    assert item.extra["author"] == "Mark Iradian"


def test_the_title_string_wins_when_the_json_ld_number_disagrees():
    """On older video reviews the JSON-LD ratingValue is 0.0 and the title is right."""
    html = REVIEW_HTML.replace('"ratingValue":"4.0"', '"ratingValue":"0.0"')

    item = _item(html)

    assert "Meeple Mountain rating: 4.0 / 5" in item.tags
    assert item.extra["rating"]["value"] == "4.0"
    assert item.extra["rating"]["schema_org"]["ratingValue"] == "0.0"


def test_the_post_taxonomy_is_read_off_the_article_class():
    item = _item()

    assert "adventure-board-games" in item.tags
    assert "fantasy-board-games" in item.tags
    assert item.extra["taxonomy"]["designers"] == ["eric-goldberg"]
    assert item.extra["taxonomy"]["publishers"] == ["devir"]


def test_a_review_without_a_rating_still_produces_an_item():
    """A broad crawl keeps the review; the missing score is the load step's problem."""
    html = re.sub(
        r"<script type=\"application/ld\+json\">.*?</script>", "", REVIEW_HTML, flags=re.S
    )
    html = html.replace('title="4.0 / 5 stars &mdash; Great - Would recommend."', "")

    item = _item(html)

    assert item is not None
    assert not any(t.startswith("Meeple Mountain rating") for t in item.tags)
    assert "rating" not in item.extra


def test_a_page_with_no_entry_content_is_skipped():
    html = REVIEW_HTML.replace("entry-content herald-entry-content", "something-else")

    assert _item(html) is None


def test_items_are_yielded_as_raw_items():
    """The declared contract is what actually flows, and Scrapy can export it."""
    item = _item()

    assert isinstance(item, RawItem)
    assert is_item(item)


def test_a_raw_item_is_never_returned_bare():
    """Pydantic models are iterable, so Scrapy shreds one into (name, value) pairs."""
    item = RawItem(url=REVIEW_URL, spider_slug="meeple-mountain", raw_text="hi")

    assert len(list(iterate_spider_output(item))) > 1
    assert list(iterate_spider_output((item,))) == [item]
