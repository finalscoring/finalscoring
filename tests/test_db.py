"""Tests for DB bootstrap (B1) — engine creation and empty schema."""

from sqlalchemy import text
from sqlmodel import create_engine

from finalscoring.db import create_tables, make_engine


def test_make_engine_creates_parent_dirs(tmp_path):
    nested = tmp_path / "a" / "b" / "test.db"
    engine = make_engine(nested)
    assert nested.parent.exists()
    engine.dispose()


def test_create_tables_empty_schema():
    engine = create_engine("sqlite:///:memory:")
    create_tables(engine)
    with engine.connect() as conn:
        assert conn.execute(text("SELECT 1")).scalar() == 1


def test_review_round_trip():
    from datetime import datetime

    from sqlmodel import Session, select

    from finalscoring.models import Critic, Game, Medium, Outlet, Review

    engine = create_engine("sqlite:///:memory:")
    create_tables(engine)

    with Session(engine) as session:
        session.add(Game(bgg_id=174430, name="Gloomhaven"))
        session.add(Outlet(slug="dice-tower", name="The Dice Tower", medium=Medium.video))
        critic = Critic(name="Tom Vasel")
        session.add(critic)
        session.commit()
        assert critic.id is not None
        critic_id = critic.id

    scraped = datetime(2026, 5, 23, 12, 0, 0)
    with Session(engine) as session:
        session.add(
            Review(
                game_bgg_id=174430,
                outlet_slug="dice-tower",
                critic_id=critic_id,
                declared_score=88.0,
                language="en",
                url="https://example.com/gloomhaven-review",
                published_at=datetime(2017, 3, 15, 0, 0, 0),
                scraped_at=scraped,
            )
        )
        session.commit()

    with Session(engine) as session:
        result = session.exec(select(Review)).one()
        assert result.game_bgg_id == 174430
        assert result.outlet_slug == "dice-tower"
        assert result.critic_id == critic_id
        assert result.declared_score == 88.0
        assert result.inferred_score is None
        assert result.score_is_inferred is False
        assert result.published_at == datetime(2017, 3, 15, 0, 0, 0)
        assert result.scraped_at == scraped
        assert result.updated_at is None


def test_review_without_critic():
    from sqlmodel import Session, select

    from finalscoring.models import Game, Medium, Outlet, Review

    engine = create_engine("sqlite:///:memory:")
    create_tables(engine)

    with Session(engine) as session:
        session.add(Game(bgg_id=174430, name="Gloomhaven"))
        session.add(Outlet(slug="susd", name="Shut Up & Sit Down", medium=Medium.text))
        session.commit()

    with Session(engine) as session:
        from datetime import datetime

        session.add(
            Review(
                game_bgg_id=174430,
                outlet_slug="susd",
                language="en",
                url="https://example.com/susd-gloomhaven",
                scraped_at=datetime(2026, 5, 23, 12, 0, 0),
            )
        )
        session.commit()

    with Session(engine) as session:
        result = session.exec(select(Review)).one()
        assert result.critic_id is None


def test_critic_round_trip():
    from sqlmodel import Session, select

    from finalscoring.models.critic import Critic

    engine = create_engine("sqlite:///:memory:")
    create_tables(engine)

    with Session(engine) as session:
        session.add(Critic(name="Tom Vasel"))
        session.commit()

    with Session(engine) as session:
        result = session.exec(select(Critic).where(Critic.name == "Tom Vasel")).one()
        assert result.quality_weight == 1.0


def test_outlet_round_trip():
    from sqlmodel import Session, select

    from finalscoring.models import Medium, Outlet

    engine = create_engine("sqlite:///:memory:")
    create_tables(engine)

    with Session(engine) as session:
        session.add(Outlet(slug="dice-tower", name="The Dice Tower", medium=Medium.video))
        session.commit()

    with Session(engine) as session:
        result = session.exec(select(Outlet).where(Outlet.slug == "dice-tower")).one()
        assert result.name == "The Dice Tower"
        assert result.medium == Medium.video
        assert result.quality_weight == 1.0
        assert result.url is None


def test_game_round_trip():
    from sqlmodel import Session, select

    from finalscoring.models.game import Game

    engine = create_engine("sqlite:///:memory:")
    create_tables(engine)

    with Session(engine) as session:
        session.add(Game(bgg_id=174430, name="Gloomhaven", year_published=2017))
        session.commit()

    with Session(engine) as session:
        result = session.exec(select(Game).where(Game.bgg_id == 174430)).one()
        assert result.name == "Gloomhaven"
        assert result.year_published == 2017
        assert result.thumbnail_url is None


def test_game_aggregate_round_trip():
    from datetime import datetime

    from sqlmodel import Session, select

    from finalscoring.models.game import Game
    from finalscoring.models.game_aggregate import GameAggregate

    engine = create_engine("sqlite:///:memory:")
    create_tables(engine)

    scored = datetime(2026, 5, 23, 12, 0, 0)

    with Session(engine) as session:
        session.add(Game(bgg_id=174430, name="Gloomhaven"))
        session.add(
            GameAggregate(
                game_bgg_id=174430,
                score=82.5,
                ci_lower=79.0,
                ci_upper=86.0,
                review_count=12,
                scoring_version="v1",
                scored_at=scored,
            )
        )
        session.commit()

    with Session(engine) as session:
        result = session.exec(
            select(GameAggregate).where(GameAggregate.game_bgg_id == 174430)
        ).one()
        assert result.score == 82.5
        assert result.ci_lower == 79.0
        assert result.ci_upper == 86.0
        assert result.review_count == 12
        assert result.scoring_version == "v1"
        assert result.scored_at == scored
