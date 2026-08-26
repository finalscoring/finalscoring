"""Tests for field-level validators.

SQLModel table models bypass Pydantic's __init__, so validators only fire via
model_validate() — the path ingestion code uses when constructing from scraped data.
"""

import pytest
from pydantic import ValidationError


def test_review_declared_score_below_zero():
    from finalscoring.models.review import Review

    with pytest.raises(ValidationError):
        Review.model_validate(
            {
                "game_bgg_id": 1,
                "outlet_slug": "x",
                "language": "en",
                "source_url": "https://example.com/a",
                "scraped_at": "2026-01-01T00:00:00",
                "declared_score": -1.0,
            }
        )


def test_review_declared_score_above_100():
    from finalscoring.models.review import Review

    with pytest.raises(ValidationError):
        Review.model_validate(
            {
                "game_bgg_id": 1,
                "outlet_slug": "x",
                "language": "en",
                "source_url": "https://example.com/b",
                "scraped_at": "2026-01-01T00:00:00",
                "declared_score": 100.1,
            }
        )


def test_review_inferred_score_out_of_range():
    from finalscoring.models.review import Review

    with pytest.raises(ValidationError):
        Review.model_validate(
            {
                "game_bgg_id": 1,
                "outlet_slug": "x",
                "language": "en",
                "source_url": "https://example.com/c",
                "scraped_at": "2026-01-01T00:00:00",
                "inferred_score": 101.0,
            }
        )


def test_game_aggregate_score_out_of_range():
    from finalscoring.models.game_aggregate import GameAggregate

    with pytest.raises(ValidationError):
        GameAggregate.model_validate(
            {
                "game_bgg_id": 1,
                "score": 105.0,
                "ci_lower": 90.0,
                "ci_upper": 100.0,
                "review_count": 5,
                "scoring_version": "v1",
                "scored_at": "2026-01-01T00:00:00",
            }
        )


def test_game_aggregate_ci_out_of_range():
    from finalscoring.models.game_aggregate import GameAggregate

    with pytest.raises(ValidationError):
        GameAggregate.model_validate(
            {
                "game_bgg_id": 1,
                "score": 80.0,
                "ci_lower": -1.0,
                "ci_upper": 90.0,
                "review_count": 5,
                "scoring_version": "v1",
                "scored_at": "2026-01-01T00:00:00",
            }
        )


def test_game_aggregate_review_count_zero():
    from finalscoring.models.game_aggregate import GameAggregate

    with pytest.raises(ValidationError):
        GameAggregate.model_validate(
            {
                "game_bgg_id": 1,
                "score": 80.0,
                "ci_lower": 75.0,
                "ci_upper": 85.0,
                "review_count": 0,
                "scoring_version": "v1",
                "scored_at": "2026-01-01T00:00:00",
            }
        )


def test_review_quote_over_cap():
    from finalscoring.models.review import QUOTE_MAX_LENGTH, Review

    with pytest.raises(ValidationError):
        Review.model_validate(
            {
                "game_bgg_id": 1,
                "outlet_slug": "x",
                "language": "en",
                "source_url": "https://example.com/d",
                "scraped_at": "2026-01-01T00:00:00",
                "quote": "x" * (QUOTE_MAX_LENGTH + 1),
            }
        )


def test_review_quote_at_cap_is_accepted():
    from finalscoring.models.review import QUOTE_MAX_LENGTH, Review

    review = Review.model_validate(
        {
            "game_bgg_id": 1,
            "outlet_slug": "x",
            "language": "en",
            "source_url": "https://example.com/e",
            "scraped_at": "2026-01-01T00:00:00",
            "quote": "x" * QUOTE_MAX_LENGTH,
        }
    )
    assert review.quote is not None
    assert len(review.quote) == QUOTE_MAX_LENGTH


def test_extracted_review_shares_the_review_cap():
    """The two layers must not drift — extraction imports the model's constant."""
    from finalscoring.extraction.schema import ExtractedReview
    from finalscoring.models.review import QUOTE_MAX_LENGTH

    field = ExtractedReview.model_fields["quote"]
    caps = [m.max_length for m in field.metadata if hasattr(m, "max_length")]
    assert caps == [QUOTE_MAX_LENGTH]


def test_outlet_quality_weight_zero():
    from finalscoring.models.outlet import Outlet

    with pytest.raises(ValidationError):
        Outlet.model_validate({"slug": "x", "name": "X", "medium": "text", "quality_weight": 0.0})


def test_outlet_quality_weight_negative():
    from finalscoring.models.outlet import Outlet

    with pytest.raises(ValidationError):
        Outlet.model_validate({"slug": "x", "name": "X", "medium": "text", "quality_weight": -0.5})


def test_critic_quality_weight_zero():
    from finalscoring.models.critic import Critic

    with pytest.raises(ValidationError):
        Critic.model_validate({"name": "X", "quality_weight": 0.0})


def test_critic_quality_weight_negative():
    from finalscoring.models.critic import Critic

    with pytest.raises(ValidationError):
        Critic.model_validate({"name": "X", "quality_weight": -1.0})
