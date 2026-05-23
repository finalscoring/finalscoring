"""Database engine factory and schema bootstrap."""

from pathlib import Path

from sqlalchemy import Engine, event
from sqlmodel import SQLModel, create_engine

import finalscoring.models.critic  # registers Critic in SQLModel.metadata
import finalscoring.models.game  # registers Game in SQLModel.metadata
import finalscoring.models.outlet  # registers Outlet in SQLModel.metadata
import finalscoring.models.review  # noqa: F401 - registers Review in SQLModel.metadata


def make_engine(db_path: Path) -> Engine:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{db_path}")
    event.listen(engine, "connect", _set_sqlite_pragmas)
    return engine


def _set_sqlite_pragmas(dbapi_conn, _record) -> None:
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def create_tables(engine: Engine) -> None:
    SQLModel.metadata.create_all(engine)
