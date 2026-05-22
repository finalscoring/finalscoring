"""Database materialization.

The Final Scoring database is fully derivable from sources: import the
``Game`` table from Recommend.Games, replay scraped JSONL into the
``Review`` table, regenerate ``Aggregate`` from ``Review``, and bake.
There is no migration system; the schema is whatever ``models.py`` says
it is, at the version pinned in this repository.
"""

from __future__ import annotations

from pathlib import Path

from sqlmodel import SQLModel, create_engine

from final_scoring.schema import models  # noqa: F401  # register tables


def make_engine(db_path: Path, echo: bool = False):  # type: ignore[no-untyped-def]
    """Create a SQLAlchemy engine for a SQLite file.

    Uses ``check_same_thread=False`` so the same engine can be used
    across threads in a build (Scrapy may dispatch work concurrently).
    """

    db_path.parent.mkdir(parents=True, exist_ok=True)
    url = f"sqlite:///{db_path}"
    return create_engine(
        url,
        echo=echo,
        connect_args={"check_same_thread": False},
    )


def init_db(db_path: Path, *, drop_existing: bool = False) -> None:
    """Create the schema. If ``drop_existing``, wipe the file first.

    A full build always passes ``drop_existing=True``; development and
    test workflows may not.
    """

    if drop_existing and db_path.exists():
        db_path.unlink()
    engine = make_engine(db_path)
    SQLModel.metadata.create_all(engine)
