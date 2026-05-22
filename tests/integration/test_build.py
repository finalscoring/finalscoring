"""End-to-end build test.

Verifies that ``run_build`` succeeds against an empty workspace and
produces a usable (if empty) SQLite file. As individual build steps
get real implementations, this test grows to assert on their outputs.
"""

from __future__ import annotations

from pathlib import Path

from sqlmodel import Session, select

from final_scoring.build import run_build
from final_scoring.schema import Aggregate, Critic, Game, Review
from final_scoring.schema.init_db import make_engine


def test_build_against_empty_workspace(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """A build against no inputs still produces a valid empty DB."""

    monkeypatch.chdir(tmp_path)
    # Build steps look for data/overrides/ and data/results/ — both
    # missing here, so the build should warn but succeed.
    db_path = tmp_path / "out.db"

    report = run_build(db_path=db_path, strict=False)

    assert db_path.is_file()
    assert report.aggregates_written == 0

    # The schema should be queryable.
    engine = make_engine(db_path)
    with Session(engine) as session:
        assert session.exec(select(Game)).all() == []
        assert session.exec(select(Critic)).all() == []
        assert session.exec(select(Review)).all() == []
        assert session.exec(select(Aggregate)).all() == []
