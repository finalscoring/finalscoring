"""Shared pytest fixtures.

Convention: anything that touches the filesystem uses ``tmp_path`` so
tests are hermetic. The fixtures below are the common ones.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from final_scoring.schema.init_db import init_db


@pytest.fixture
def empty_db(tmp_path: Path) -> Path:
    """A freshly-materialized empty Final Scoring database."""

    path = tmp_path / "test.db"
    init_db(path, drop_existing=True)
    return path
