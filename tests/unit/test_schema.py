"""Schema sanity tests.

These guard the most boring possible failure modes: the database can
be created, the tables exist, rows can be inserted and read back, and
the schema-level constraints (e.g. quote length) are enforced.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlmodel import Session, select

from final_scoring.schema import Critic, Game, Review
from final_scoring.schema.init_db import make_engine


def test_empty_db_has_expected_tables(empty_db: Path) -> None:
    """All tables exist and are empty after init."""

    engine = make_engine(empty_db)
    with Session(engine) as session:
        # If any of these tables is missing, the .exec() call raises.
        assert session.exec(select(Game)).all() == []
        assert session.exec(select(Critic)).all() == []
        assert session.exec(select(Review)).all() == []


def test_review_roundtrip(empty_db: Path) -> None:
    """Insert and read back the minimum-viable graph of records."""

    engine = make_engine(empty_db)
    with Session(engine) as session:
        game = Game(bgg_id=1, title="Catan", year=1995)
        critic = Critic(
            slug="test_critic",
            name="Test Critic",
            medium="text",
            language="en",
            score_format="numeric_10",
            source_tier=1.0,
        )
        session.add(game)
        session.add(critic)
        session.commit()
        session.refresh(critic)
        assert critic.id is not None

        review = Review(
            critic_id=critic.id,
            game_bgg_id=game.bgg_id,
            original_url="https://example.com/review",
            language="en",
            score_declared="8/10",
            rating_inferred=8,
            sentiment="positive",
            quote_verbatim="A genuinely clever auction game.",
            summary="The critic praises the auction mechanic.",
            extraction_model_version="test/v1",
        )
        session.add(review)
        session.commit()

        rows = session.exec(select(Review)).all()
        assert len(rows) == 1
        assert rows[0].quote_verbatim == "A genuinely clever auction game."


@pytest.mark.parametrize(
    "rating",
    [0, 11, -1, 100],
)
def test_rating_inferred_rejects_out_of_range(rating: int) -> None:
    """rating_inferred must be 1–10 (pydantic-level validation)."""

    with pytest.raises(Exception):  # noqa: B017 — pydantic raises ValidationError
        Review(
            critic_id=1,
            game_bgg_id=1,
            original_url="https://example.com/review",
            language="en",
            rating_inferred=rating,
            sentiment="positive",
            summary="x",
            extraction_model_version="test/v1",
        )
