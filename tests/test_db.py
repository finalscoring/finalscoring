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
    from datetime import date

    from sqlmodel import Session, select

    from finalscoring.models.critic import Critic
    from finalscoring.models.game import Game
    from finalscoring.models.outlet import Outlet
    from finalscoring.models.review import Review

    engine = create_engine("sqlite:///:memory:")
    create_tables(engine)

    with Session(engine) as session:
        session.add(Game(bgg_id=174430, name="Gloomhaven"))
        outlet = Outlet(name="The Dice Tower", medium="youtube")
        critic = Critic(name="Tom Vasel", language="en")
        session.add(outlet)
        session.add(critic)
        session.commit()
        assert outlet.id is not None
        assert critic.id is not None
        outlet_id = outlet.id
        critic_id = critic.id

    with Session(engine) as session:
        session.add(
            Review(
                game_bgg_id=174430,
                outlet_id=outlet_id,
                critic_id=critic_id,
                declared_score=88.0,
                language="en",
                url="https://example.com/gloomhaven-review",
                review_date=date(2017, 3, 15),
            )
        )
        session.commit()

    with Session(engine) as session:
        result = session.exec(select(Review)).one()
        assert result.game_bgg_id == 174430
        assert result.outlet_id == outlet_id
        assert result.critic_id == critic_id
        assert result.declared_score == 88.0
        assert result.inferred_score is None
        assert result.score_is_inferred is False
        assert result.review_date == date(2017, 3, 15)


def test_review_without_critic():
    from sqlmodel import Session, select

    from finalscoring.models.game import Game
    from finalscoring.models.outlet import Outlet
    from finalscoring.models.review import Review

    engine = create_engine("sqlite:///:memory:")
    create_tables(engine)

    with Session(engine) as session:
        session.add(Game(bgg_id=174430, name="Gloomhaven"))
        outlet = Outlet(name="Shut Up & Sit Down", medium="blog")
        session.add(outlet)
        session.commit()
        assert outlet.id is not None
        outlet_id = outlet.id

    with Session(engine) as session:
        session.add(
            Review(
                game_bgg_id=174430,
                outlet_id=outlet_id,
                language="en",
                url="https://example.com/susd-gloomhaven",
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
        session.add(Critic(name="Tom Vasel", language="en"))
        session.commit()

    with Session(engine) as session:
        result = session.exec(select(Critic).where(Critic.name == "Tom Vasel")).one()
        assert result.language == "en"
        assert result.quality_weight == 1.0


def test_outlet_round_trip():
    from sqlmodel import Session, select

    from finalscoring.models.outlet import Outlet

    engine = create_engine("sqlite:///:memory:")
    create_tables(engine)

    with Session(engine) as session:
        session.add(Outlet(name="The Dice Tower", medium="youtube"))
        session.commit()

    with Session(engine) as session:
        result = session.exec(select(Outlet).where(Outlet.name == "The Dice Tower")).one()
        assert result.medium == "youtube"
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
