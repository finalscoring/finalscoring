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
