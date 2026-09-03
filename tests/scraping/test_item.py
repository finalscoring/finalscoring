"""Tests for RawItem — the spider-to-extraction contract."""

from datetime import UTC, datetime
from typing import Any

import pytest
from pydantic import ValidationError
from scrapy.utils.spider import iterate_spider_output

from finalscoring.models import Medium, RatingDirection, RatingSystem
from finalscoring.scraping.item import (
    RawGameHint,
    RawItem,
    RawReviewHint,
    SourceRating,
    language_from_locale,
)


def _item(**kwargs: Any) -> RawItem:
    return RawItem.model_validate(
        {"url": "https://example.com/review", "spider_slug": "acme", "raw_text": "Great game."}
        | kwargs
    )


def test_minimal_valid_item():
    item = _item()
    assert item.url == "https://example.com/review"
    assert item.spider_slug == "acme"
    assert item.raw_text == "Great game."
    assert item.raw_html is None
    assert item.title is None
    assert item.description is None
    assert item.published_at is None
    assert item.language is None
    assert item.image_url is None
    assert item.tags == []
    assert item.duration_seconds is None
    assert item.outlet_slug is None
    assert item.og_site_name is None
    assert item.oembed is None
    assert item.schema_org == []
    assert item.extra == {}
    assert item.canonical_url is None
    assert item.modified_at is None
    assert item.categories == []
    assert item.taxonomy == {}
    assert item.reviews == []
    assert item.bylines == []
    assert item.known_critic_name is None
    assert item.medium is None


def test_source_host_defaults_to_the_url_host():
    assert _item().source_host == "example.com"
    assert _item(url="https://spielbox.de/rezensionen/catan").source_host == "spielbox.de"


def test_source_host_is_kept_when_the_spider_sets_it():
    item = _item(url="https://aggregator.example/link/123", source_host="fairplay.de")
    assert item.source_host == "fairplay.de"


def test_full_item():
    item = _item(
        spider_slug="spiel_des_jahres",
        raw_text="Catan is excellent.",
        raw_html="<article>Catan is excellent.</article>",
        title="Review of Catan",
        description="A deep dive into Catan.",
        published_at=datetime(2025, 6, 1, tzinfo=UTC),
        language="de",
        image_url="https://example.com/image.jpg",
        tags=["strategy", "family"],
        duration_seconds=480,
        outlet_slug="spielbox",
        og_site_name="Spielbox",
        oembed={"type": "rich", "title": "Review of Catan"},
        schema_org=[{"@type": "Review", "name": "Catan"}],
        extra={"wp_json": {"id": 42}},
        canonical_url="https://example.com/catan",
        modified_at=datetime(2025, 7, 1, tzinfo=UTC),
        categories=["reviews"],
        taxonomy={"mechanics": ["trading", "dice-rolling"]},
        reviews=[
            {
                "game": {"titles": ["Catan"], "designers": ["Klaus Teuber"], "bgg_id": 13},
                "critic_names": ["Tom Werneck"],
                "editorial_flags": ["TOPspiel"],
                "ratings": [{"system": "editorial", "value": 5, "scale_max": 6}],
            }
        ],
        bylines=["Tom Werneck"],
        known_critic_name="Tom Werneck",
        medium="text",
    )
    assert item.raw_html == "<article>Catan is excellent.</article>"
    assert item.language == "de"
    assert item.tags == ["strategy", "family"]
    assert item.duration_seconds == 480
    assert item.outlet_slug == "spielbox"
    assert item.oembed == {"type": "rich", "title": "Review of Catan"}
    assert item.schema_org == [{"@type": "Review", "name": "Catan"}]
    assert item.extra == {"wp_json": {"id": 42}}
    assert item.canonical_url == "https://example.com/catan"
    assert item.categories == ["reviews"]
    assert item.taxonomy == {"mechanics": ["trading", "dice-rolling"]}
    review = item.reviews[0]
    assert review.game == RawGameHint(titles=["Catan"], designers=["Klaus Teuber"], bgg_id=13)
    assert review.critic_names == ["Tom Werneck"]
    assert review.editorial_flags == ["TOPspiel"]
    assert review.ratings[0].system is RatingSystem.editorial
    assert review.ratings[0].value == 5.0  # the int 5 is coerced to float
    assert isinstance(review.ratings[0].value, float)
    assert item.bylines == ["Tom Werneck"]
    assert item.known_critic_name == "Tom Werneck"
    assert item.medium is Medium.text


def test_scraped_at_defaults_to_utc_now():
    assert _item().scraped_at.tzinfo == UTC


def test_empty_url_rejected():
    with pytest.raises(ValidationError):
        _item(url="   ")


def test_empty_spider_slug_rejected():
    with pytest.raises(ValidationError):
        _item(spider_slug="")


def test_empty_raw_text_rejected():
    with pytest.raises(ValidationError):
        _item(raw_text="  ")


def test_invalid_language_rejected():
    with pytest.raises(ValidationError):
        _item(language="english")


def test_uppercase_language_rejected():
    with pytest.raises(ValidationError):
        _item(language="EN")


@pytest.mark.parametrize(
    ("given", "expected"),
    [
        ("de_DE", "de-DE"),
        ("de-DE", "de-DE"),
        ("DE_de", "de-DE"),
        ("de", "de"),
        ("  en_GB  ", "en-GB"),
    ],
)
def test_locale_is_normalised_to_bcp_47(given: str, expected: str):
    """Open Graph writes de_DE, html lang writes de-DE; both mean the same thing."""
    assert _item(locale=given).locale == expected


def test_locale_keeps_the_region_language_discards():
    """de-AT and de-CH are different outlets, so the region has to survive."""
    item = _item(language="de", locale="de-AT")

    assert item.language == "de"
    assert item.locale == "de-AT"


def test_invalid_locale_rejected():
    with pytest.raises(ValidationError):
        _item(locale="Deutschland")


@pytest.mark.parametrize(
    ("locale", "expected"),
    [
        ("de-AT", "de"),
        ("de_DE", "de"),
        ("en-GB", "en"),
        ("en", "en"),
        ("de", "de"),
        ("EN-us", "en"),
        (None, None),
        ("", None),
        ("x-default", None),
        ("deu_DE", None),
    ],
)
def test_language_from_locale(locale: str | None, expected: str | None):
    assert language_from_locale(locale) == expected


def test_a_raw_item_is_never_returned_bare():
    """A pydantic model is iterable: a bare return gets shredded into (name, value) pairs,
    so every spider callback wraps a RawItem in a one-tuple. This is the invariant."""
    item = _item()

    assert len(list(iterate_spider_output(item))) > 1
    assert list(iterate_spider_output((item,))) == [item]


def test_string_lists_drop_blank_entries():
    item = _item(
        tags=["strategy", "  ", ""],
        categories=[" reviews ", None],
        bylines=["  Tom Werneck  "],
    )
    assert item.tags == ["strategy"]
    assert item.categories == ["reviews"]
    assert item.bylines == ["Tom Werneck"]


def test_blank_known_critic_name_becomes_none():
    assert _item(known_critic_name="   ").known_critic_name is None


def test_invalid_medium_rejected():
    with pytest.raises(ValidationError):
        _item(medium="tweet")


# --- SourceRating -----------------------------------------------------------


def test_source_rating_requires_a_system():
    with pytest.raises(ValidationError):
        SourceRating.model_validate({"value": 5})


def test_source_rating_rejects_an_unknown_system():
    with pytest.raises(ValidationError):
        SourceRating.model_validate({"system": "vibes"})


def test_source_rating_normalises_the_german_decimal_comma():
    """The overall score reads "4,5 H@LL9000"; verbatim keeps the original string."""
    rating = SourceRating.model_validate(
        {"system": "overall", "value": "4,5", "verbatim": "4,5 H@LL9000"}
    )
    assert rating.value == 4.5
    assert rating.verbatim == "4,5 H@LL9000"


def test_source_rating_blank_strings_become_none():
    rating = SourceRating.model_validate({"system": "axis", "axis": "Spielreiz", "label": "  "})
    assert rating.axis == "Spielreiz"
    assert rating.label is None


def test_source_rating_defaults_to_higher_is_better():
    assert (
        SourceRating.model_validate({"system": "editorial"}).direction
        is RatingDirection.higher_is_better
    )


def test_source_rating_direction_inverts_for_a_rank():
    rating = SourceRating.model_validate(
        {"system": "rank", "value": 1, "direction": "lower_is_better"}
    )
    assert rating.direction is RatingDirection.lower_is_better


def test_source_rating_rejects_reversed_scale_bounds():
    with pytest.raises(ValidationError):
        SourceRating.model_validate({"system": "star_label", "scale_min": 5, "scale_max": 1})


@pytest.mark.parametrize("bad", ["inf", "-inf", "nan"])
def test_source_rating_rejects_non_finite_values(bad: str):
    """A malformed scrape must fail here, not in a formatter or the scoring maths."""
    with pytest.raises(ValidationError):
        SourceRating.model_validate({"system": "editorial", "value": bad})


# --- RawReviewHint -------------------------------------------------------------


def test_review_hint_carries_the_cited_reviews_own_provenance():
    """For a roundup the outlet, url and date are the critic's, not the page's."""
    hint = RawReviewHint.model_validate(
        {
            "critic_names": ["Udo Bartsch"],
            "outlet_name": "Rezensionen für Millionen",
            "medium": "text",
            "published_in": "Spielbox 3/2024, S. 42",
            "review_url": "https://example.com/critic/review",
            "published_at": datetime(2024, 3, 1, tzinfo=UTC),
            "language": "de",
            "ratings": [{"system": "star_label", "value": 4, "label": "solide"}],
            "editorial_flags": ["", "TOPspiel"],
        }
    )
    assert hint.outlet_name == "Rezensionen für Millionen"
    assert hint.medium is Medium.text
    assert hint.published_in == "Spielbox 3/2024, S. 42"
    assert hint.editorial_flags == ["TOPspiel"]
    assert hint.ratings[0].label == "solide"


def test_review_hint_defaults_to_an_empty_shell():
    hint = RawReviewHint()
    assert hint.game is None
    assert hint.critic_names == []
    assert hint.ratings == []
    assert hint.editorial_flags == []


def test_review_hint_keeps_both_names_of_a_co_written_review():
    """One verdict by two people — "Nico Wagner und Stephan Kessler" is in the corpus."""
    hint = RawReviewHint.model_validate({"critic_names": ["Nico Wagner", "Stephan Kessler", "  "]})
    assert hint.critic_names == ["Nico Wagner", "Stephan Kessler"]


def test_review_hint_rejects_a_bad_language_code():
    with pytest.raises(ValidationError):
        RawReviewHint.model_validate({"language": "deutsch"})


def test_a_listicle_is_one_item_with_several_review_hints():
    """One post, two games, one reviewer — RFM's two-star posts already do this."""
    item = _item(
        known_critic_name="Udo Bartsch",
        reviews=[
            {"game": {"titles": ["Azul"]}, "ratings": [{"system": "star_label", "value": 5}]},
            {"game": {"titles": ["Sagrada"]}, "ratings": [{"system": "star_label", "value": 4}]},
        ],
    )
    games = [r.game for r in item.reviews]
    assert all(g is not None for g in games)
    assert [g.titles for g in games if g] == [["Azul"], ["Sagrada"]]
    assert [r.ratings[0].value for r in item.reviews] == [5.0, 4.0]


# --- RawGameHint -----------------------------------------------------------


def test_game_hint_drops_blank_names():
    hint = RawGameHint.model_validate(
        {"designers": ["Klaus Teuber", "  ", ""], "publishers": ["Kosmos", None]}
    )
    assert hint.designers == ["Klaus Teuber"]
    assert hint.publishers == ["Kosmos"]


def test_game_hint_keeps_every_title_the_source_names():
    """A German review names both the local edition and the original."""
    hint = RawGameHint.model_validate({"titles": ["Astrobienen", "Apiary", "  "]})
    assert hint.titles == ["Astrobienen", "Apiary"]


@pytest.mark.parametrize("year", [1899, 3000])
def test_game_hint_rejects_an_implausible_year(year: int):
    with pytest.raises(ValidationError):
        RawGameHint.model_validate({"year_published": year})


def test_game_hint_keeps_a_plausible_year_and_bgg_id():
    hint = RawGameHint.model_validate({"year_published": 1995, "bgg_id": 13})
    assert hint.year_published == 1995
    assert hint.bgg_id == 13
