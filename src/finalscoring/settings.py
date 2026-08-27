"""Runtime configuration loaded from environment variables."""

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Settings:
    """Typed, immutable config for all runtime-configurable values."""

    llm_base_url: str
    llm_model: str
    llm_api_key: str
    llm_timeout: float
    llm_max_attempts: int
    llm_context: str  # "html" or "text" — see LLM_CONTEXT_MODES
    scraper_user_agent: str
    scraper_delay: float
    scraper_concurrency: int
    results_dir: Path
    jobs_dir: Path
    db_path: Path


DEFAULT_USER_AGENT = "FinalScoring/0.0.1 (+https://finalscoring.games/)"

# Whether the model reads the article's markup or its flattened text. Switchable
# so the two can be measured against each other on the same corpus; once that
# number exists this can collapse to whichever won.
LLM_CONTEXT_MODES = ("html", "text")


def load_settings() -> Settings:
    """Construct a Settings instance from the current environment.

    Raises ValueError if any of the numeric variables is set to a value that
    is not a number, or FS_LLM_CONTEXT to something other than html/text.
    """
    llm_context = os.environ.get("FS_LLM_CONTEXT", "html")
    if llm_context not in LLM_CONTEXT_MODES:
        raise ValueError(f"FS_LLM_CONTEXT must be one of {LLM_CONTEXT_MODES}, got {llm_context!r}")

    return Settings(
        llm_base_url=os.environ.get("FS_LLM_BASE_URL", "http://localhost:11434/v1"),
        llm_model=os.environ.get("FS_LLM_MODEL", "llama3.2"),
        # Local servers ignore the key but the OpenAI client requires one.
        llm_api_key=os.environ.get("FS_LLM_API_KEY", "not-needed"),
        llm_timeout=float(os.environ.get("FS_LLM_TIMEOUT", "120.0")),
        llm_max_attempts=int(os.environ.get("FS_LLM_MAX_ATTEMPTS", "3")),
        llm_context=llm_context,
        scraper_user_agent=os.environ.get("FS_SCRAPER_USER_AGENT", DEFAULT_USER_AGENT),
        scraper_delay=float(os.environ.get("FS_SCRAPER_DELAY", "1.0")),
        scraper_concurrency=int(os.environ.get("FS_SCRAPER_CONCURRENCY", "4")),
        results_dir=Path(os.environ.get("FS_RESULTS_DIR", "data/results")),
        jobs_dir=Path(os.environ.get("FS_JOBS_DIR", "data/jobs")),
        db_path=Path(os.environ.get("FS_DB_PATH", "data/finalscoring.db")),
    )
