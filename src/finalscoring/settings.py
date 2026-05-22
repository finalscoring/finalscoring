"""Runtime configuration loaded from environment variables."""

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Settings:
    """Typed, immutable config for all runtime-configurable values."""

    llm_base_url: str
    llm_model: str
    scraper_delay: float
    db_path: Path


def load_settings() -> Settings:
    """Construct a Settings instance from the current environment.

    Raises ValueError if FS_SCRAPER_DELAY is set to a non-numeric value.
    """
    return Settings(
        llm_base_url=os.environ.get("FS_LLM_BASE_URL", "http://localhost:11434/v1"),
        llm_model=os.environ.get("FS_LLM_MODEL", "llama3.2"),
        scraper_delay=float(os.environ.get("FS_SCRAPER_DELAY", "1.0")),
        db_path=Path(os.environ.get("FS_DB_PATH", "data/results/finalscoring.db")),
    )
