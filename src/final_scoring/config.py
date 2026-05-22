"""Project configuration.

All settings load from environment variables (or a ``.env`` file in the
project root). See ``.env.example`` for the canonical list. Settings are
exposed as a Pydantic model so they validate on access rather than
silently defaulting halfway through a build.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


def _env(key: str, default: str | None = None) -> str | None:
    value = os.getenv(key)
    if value is None or value == "":
        return default
    return value


def _env_float(key: str, default: float | None = None) -> float | None:
    raw = _env(key)
    return float(raw) if raw is not None else default


def _env_int(key: str, default: int | None = None) -> int | None:
    raw = _env(key)
    return int(raw) if raw is not None else default


class LLMSettings(BaseModel):
    """Configuration for the LLM extraction stage.

    The OpenAI-compatible client points at a local model server by default
    (vLLM, Ollama, llama.cpp). To run against a hosted provider, set
    ``LLM_API_BASE_URL`` and ``LLM_API_KEY`` accordingly.
    """

    api_base_url: str | None = Field(default=None)
    api_key: str = Field(default="local")
    model: str = Field(default="Qwen/Qwen2.5-14B-Instruct")
    temperature: float | None = Field(default=0.1)
    max_output_tokens: int | None = Field(default=4096)


class ScraperSettings(BaseModel):
    user_agent: str = Field(default="FinalScoringBot/0.1")
    download_delay: float = Field(default=1.0)
    concurrent_requests: int = Field(default=4)
    jobdir: Path = Field(default=Path("data/jobs"))
    feed_uri: str = Field(
        default="data/results/%(name)s-%(time)s-%(batch_id)05d.jl",
    )
    export_batch_item_count: int = Field(default=10_000)


class BuildSettings(BaseModel):
    db_path: Path = Field(default=Path("data/final_scoring.db"))
    recommend_games_import: Path | None = Field(default=None)


class Settings(BaseModel):
    llm: LLMSettings
    scraper: ScraperSettings
    build: BuildSettings


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the loaded settings.

    Cached so repeated access in the same process doesn't re-parse env.
    Use :func:`reload_settings` from tests if needed.
    """

    rg_import = _env("RECOMMEND_GAMES_IMPORT")
    return Settings(
        llm=LLMSettings(
            api_base_url=_env("LLM_API_BASE_URL"),
            api_key=_env("LLM_API_KEY", "local") or "local",
            model=_env("LLM_MODEL", "Qwen/Qwen2.5-14B-Instruct")
            or "Qwen/Qwen2.5-14B-Instruct",
            temperature=_env_float("LLM_TEMPERATURE", 0.1),
            max_output_tokens=_env_int("LLM_MAX_OUTPUT_TOKENS", 4096),
        ),
        scraper=ScraperSettings(
            user_agent=_env("SCRAPER_USER_AGENT", "FinalScoringBot/0.1")
            or "FinalScoringBot/0.1",
            download_delay=_env_float("SCRAPER_DOWNLOAD_DELAY", 1.0) or 1.0,
            concurrent_requests=_env_int("SCRAPER_CONCURRENT_REQUESTS", 4) or 4,
            jobdir=Path(_env("SCRAPER_JOBDIR", "data/jobs") or "data/jobs"),
            feed_uri=_env(
                "SCRAPER_FEED_URI",
                "data/results/%(name)s-%(time)s-%(batch_id)05d.jl",
            )
            or "data/results/%(name)s-%(time)s-%(batch_id)05d.jl",
            export_batch_item_count=_env_int(
                "SCRAPER_EXPORT_BATCH_ITEM_COUNT", 10_000
            )
            or 10_000,
        ),
        build=BuildSettings(
            db_path=Path(_env("FS_DB_PATH", "data/final_scoring.db")
                         or "data/final_scoring.db"),
            recommend_games_import=Path(rg_import) if rg_import else None,
        ),
    )


def reload_settings() -> Settings:
    """Clear the cache and reload. Intended for tests."""

    get_settings.cache_clear()
    return get_settings()
