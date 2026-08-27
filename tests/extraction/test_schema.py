"""Tests for the LLM extraction schema."""

import logging
from typing import Any

import pytest
from pydantic import ValidationError

from finalscoring.extraction.schema import (
    PROMPT_V1,
    ExtractedGame,
    ExtractedReview,
    ExtractionResult,
)
from finalscoring.models import Medium, Sentiment


def _review(**kwargs: Any) -> ExtractedReview:
    return ExtractedReview.model_validate(
        {
            "game": {"title": "Catan"},
            "reviewer_name": "Jane Doe",
            "rating": 8,
            "sentiment": "positive",
            "language": "en",
        }
        | kwargs
    )


def _game(**kwargs: Any) -> ExtractedGame:
    return ExtractedGame.model_validate({"title": "Catan"} | kwargs)


def test_minimal_valid_review():
    r = _review()
    assert r.game.title == "Catan"
    assert r.reviewer_name == "Jane Doe"
    assert r.outlet_name is None
    assert r.medium is None
    assert r.published_in is None
    assert r.review_url is None
    assert r.published_at is None
    assert r.raw_score is None
    assert r.rating == 8
    assert r.sentiment == Sentiment.positive
    assert r.quote is None
    assert r.language == "en"


def test_full_valid_review():
    r = _review(
        outlet_name="Spielbox",
        raw_score="4/5",
        rating=8,
        sentiment="mixed_positive",
        quote="Ein wirklich gelungenes Spiel mit kleinen Schwächen.",
        language="de",
    )
    assert r.outlet_name == "Spielbox"
    assert r.raw_score == "4/5"
    assert r.sentiment == Sentiment.mixed_positive
    assert r.quote == "Ein wirklich gelungenes Spiel mit kleinen Schwächen."


def test_extraction_result_multiple_reviews():
    result = ExtractionResult.model_validate(
        {
            "reviews": [
                {
                    "game": {"title": "Catan"},
                    "reviewer_name": "A",
                    "rating": 7,
                    "sentiment": "positive",
                    "language": "en",
                },
                {
                    "game": {"title": "Ticket to Ride"},
                    "reviewer_name": "B",
                    "rating": 5,
                    "sentiment": "neutral",
                    "language": "de",
                },
            ]
        }
    )
    assert len(result.reviews) == 2


def test_extraction_result_empty_list():
    result = ExtractionResult.model_validate({"reviews": []})
    assert result.reviews == []


def test_rating_below_range_rejected():
    with pytest.raises(ValidationError):
        _review(rating=0)


def test_rating_above_range_rejected():
    with pytest.raises(ValidationError):
        _review(rating=11)


def test_quote_over_300_chars_rejected():
    with pytest.raises(ValidationError):
        _review(quote="x" * 301)


def test_quote_at_300_chars_accepted():
    r = _review(quote="x" * 300)
    assert r.quote is not None
    assert len(r.quote) == 300


def test_review_provenance_is_kept():
    r = _review(
        medium="text",
        published_in="Spielbox online",
        review_url="https://spielbox.de/catan-rezension",
        published_at="2026-03-15",
    )
    assert r.medium == Medium.text
    assert r.published_in == "Spielbox online"
    assert r.review_url == "https://spielbox.de/catan-rezension"
    assert r.published_at is not None
    assert (r.published_at.year, r.published_at.month, r.published_at.day) == (2026, 3, 15)


def test_print_review_is_attributable_without_a_url():
    """A print review has no address and never will — published_in carries it."""
    r = _review(medium="print", published_in="Spielbox 3/2026, S. 42")
    assert r.medium == Medium.print_
    assert r.published_in == "Spielbox 3/2026, S. 42"
    assert r.review_url is None
    assert r.published_at is None


@pytest.mark.parametrize("field", ["review_url", "published_in", "medium"])
@pytest.mark.parametrize("value", ["", "   "])
def test_blank_provenance_becomes_none(field: str, value: str):
    assert getattr(_review(**{field: value}), field) is None


def test_review_url_is_stripped():
    assert _review(review_url="  https://example.com/r  ").review_url == "https://example.com/r"


def test_invalid_medium_rejected():
    with pytest.raises(ValidationError):
        _review(medium="newsletter")


def test_unparseable_published_at_rejected():
    with pytest.raises(ValidationError):
        _review(published_at="März 2026")


def test_invalid_sentiment_rejected():
    with pytest.raises(ValidationError):
        _review(sentiment="excellent")


def test_invalid_language_rejected():
    with pytest.raises(ValidationError):
        _review(language="english")


def test_uppercase_language_rejected():
    with pytest.raises(ValidationError):
        _review(language="DE")


def test_empty_game_title_rejected():
    with pytest.raises(ValidationError):
        _game(title="   ")


def test_a_review_without_a_game_is_rejected():
    """Game identity is half the (game, reviewer) pair, not an optional extra."""
    with pytest.raises(ValidationError):
        ExtractedReview.model_validate(
            {"reviewer_name": "A", "rating": 7, "sentiment": "positive", "language": "en"}
        )


def test_minimal_game_defaults_to_no_evidence():
    g = _game()
    assert g.title == "Catan"
    assert g.designers == []
    assert g.publishers == []
    assert g.year_published is None
    assert g.bgg_url is None


def test_designers_and_publishers_are_lists():
    """Co-designed and co-published editions are the norm, not the exception."""
    g = _game(
        designers=["Johannes Goupy", "Yoann Levet"],
        publishers=["Frosted Games", "Board Game Circus"],
    )
    assert g.designers == ["Johannes Goupy", "Yoann Levet"]
    assert g.publishers == ["Frosted Games", "Board Game Circus"]


@pytest.mark.parametrize("field", ["designers", "publishers"])
def test_blank_names_are_dropped(field: str):
    assert getattr(_game(**{field: ["", "  ", "Kosmos"]}), field) == ["Kosmos"]


@pytest.mark.parametrize("field", ["designers", "publishers"])
def test_names_are_stripped(field: str):
    assert getattr(_game(**{field: ["  Kosmos  "]}), field) == ["Kosmos"]


def test_a_plausible_year_is_kept():
    assert _game(year_published=2024).year_published == 2024


@pytest.mark.parametrize("year", [1899, 1, 3000])
def test_an_implausible_year_is_rejected(year: int):
    """Out of range means the model is confabulating, so a retry is worth it."""
    with pytest.raises(ValidationError):
        _game(year_published=year)


def test_a_bgg_url_is_kept():
    url = "https://boardgamegeek.com/boardgame/167791/terraforming-mars"
    assert _game(bgg_url=url).bgg_url == url


def test_a_bgg_url_is_stripped():
    assert _game(bgg_url="  https://boardgamegeek.com/boardgame/13  ").bgg_url == (
        "https://boardgamegeek.com/boardgame/13"
    )


def test_a_www_bgg_url_is_kept():
    url = "https://www.boardgamegeek.com/boardgame/13"
    assert _game(bgg_url=url).bgg_url == url


@pytest.mark.parametrize("url", ["", "   "])
def test_a_blank_bgg_url_becomes_none(url: str):
    assert _game(bgg_url=url).bgg_url is None


@pytest.mark.parametrize(
    "url",
    [
        "https://kosmos.de/catan",
        "not a url",
        "https://boardgamegeek.com.evil.example/boardgame/13",
        "https://evil.example/?x=boardgamegeek.com",
    ],
)
def test_a_url_on_another_host_becomes_none(url: str):
    """Matched on hostname, not substring — the id is parsed out of this later."""
    assert _game(bgg_url=url).bgg_url is None


def test_a_discarded_bgg_url_is_logged(caplog):
    """An invisible coercion looks exactly like the model correctly saying null."""
    with caplog.at_level(logging.WARNING):
        _game(bgg_url="https://kosmos.de/catan")

    assert "https://kosmos.de/catan" in caplog.text


def test_empty_reviewer_name_rejected():
    with pytest.raises(ValidationError):
        _review(reviewer_name="")


def test_prompt_v1_loads_and_is_non_empty():
    assert isinstance(PROMPT_V1, str)
    assert len(PROMPT_V1) > 0


def _prompt_fields() -> list[str]:
    """The names the prompt must mention: the game's own, not the container's."""
    review = [name for name in ExtractedReview.model_fields if name != "game"]
    return review + list(ExtractedGame.model_fields)


@pytest.mark.xfail(
    strict=True,
    reason="extract_v1 still asks for a flat game_title; the prompt is its own chunk",
)
def test_prompt_v1_asks_for_every_extracted_field():
    """A field the prompt never mentions is a field the model never fills."""
    for name in _prompt_fields():
        assert name in PROMPT_V1, f"prompt does not ask for {name}"
