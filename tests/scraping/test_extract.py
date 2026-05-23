"""Tests for the LLM extraction schema."""

from typing import Any

import pytest
from pydantic import ValidationError

from finalscoring.models.review import Sentiment
from finalscoring.scraping.extract import PROMPT_V1, ExtractedReview, ExtractionResult


def _review(**kwargs: Any) -> ExtractedReview:
    return ExtractedReview.model_validate(
        {
            "game_title": "Catan",
            "reviewer_name": "Jane Doe",
            "rating": 8,
            "sentiment": "positive",
            "language": "en",
        }
        | kwargs
    )


def test_minimal_valid_review():
    r = _review()
    assert r.game_title == "Catan"
    assert r.reviewer_name == "Jane Doe"
    assert r.outlet_name is None
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
                    "game_title": "Catan",
                    "reviewer_name": "A",
                    "rating": 7,
                    "sentiment": "positive",
                    "language": "en",
                },
                {
                    "game_title": "Ticket to Ride",
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
        _review(game_title="   ")


def test_empty_reviewer_name_rejected():
    with pytest.raises(ValidationError):
        _review(reviewer_name="")


def test_prompt_v1_loads_and_is_non_empty():
    assert isinstance(PROMPT_V1, str)
    assert len(PROMPT_V1) > 0
