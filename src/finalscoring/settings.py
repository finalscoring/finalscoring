"""Runtime configuration loaded from environment variables."""

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Settings:
    """Typed, immutable config for all runtime-configurable values."""

    llm_base_url: str
    llm_model: str
    scraper_user_agent: str
    scraper_delay: float
    scraper_concurrency: int
    results_dir: Path
    jobs_dir: Path
    db_path: Path


DEFAULT_USER_AGENT = "FinalScoring/0.0.1 (+https://finalscoring.games/)"


def load_settings() -> Settings:
    """Construct a Settings instance from the current environment.

    Raises ValueError if FS_SCRAPER_DELAY or FS_SCRAPER_CONCURRENCY is set to a
    value that is not a number.
    """
    return Settings(
        llm_base_url=os.environ.get("FS_LLM_BASE_URL", "http://localhost:11434/v1"),
        llm_model=os.environ.get("FS_LLM_MODEL", "llama3.2"),
        scraper_user_agent=os.environ.get("FS_SCRAPER_USER_AGENT", DEFAULT_USER_AGENT),
        scraper_delay=float(os.environ.get("FS_SCRAPER_DELAY", "1.0")),
        scraper_concurrency=int(os.environ.get("FS_SCRAPER_CONCURRENCY", "4")),
        results_dir=Path(os.environ.get("FS_RESULTS_DIR", "data/results")),
        jobs_dir=Path(os.environ.get("FS_JOBS_DIR", "data/jobs")),
        db_path=Path(os.environ.get("FS_DB_PATH", "data/finalscoring.db")),
    )
