from pathlib import Path

import pytest

from finalscoring.settings import DEFAULT_USER_AGENT, Settings, load_settings

ENV_KEYS = (
    "FS_LLM_BASE_URL",
    "FS_LLM_MODEL",
    "FS_LLM_API_KEY",
    "FS_LLM_TIMEOUT",
    "FS_LLM_MAX_ATTEMPTS",
    "FS_LLM_CONTEXT",
    "FS_SCRAPER_USER_AGENT",
    "FS_SCRAPER_DELAY",
    "FS_SCRAPER_CONCURRENCY",
    "FS_RESULTS_DIR",
    "FS_JOBS_DIR",
    "FS_DB_PATH",
)


def test_settings_reads_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FS_LLM_BASE_URL", "http://gpu-server:8000/v1")
    monkeypatch.setenv("FS_LLM_MODEL", "qwen2.5-7b")
    monkeypatch.setenv("FS_LLM_API_KEY", "sk-test")
    monkeypatch.setenv("FS_LLM_TIMEOUT", "30.5")
    monkeypatch.setenv("FS_LLM_MAX_ATTEMPTS", "5")
    monkeypatch.setenv("FS_LLM_CONTEXT", "text")
    monkeypatch.setenv("FS_SCRAPER_USER_AGENT", "TestBot/1.0")
    monkeypatch.setenv("FS_SCRAPER_DELAY", "2.5")
    monkeypatch.setenv("FS_SCRAPER_CONCURRENCY", "8")
    monkeypatch.setenv("FS_RESULTS_DIR", "/data/out")
    monkeypatch.setenv("FS_JOBS_DIR", "/data/state")
    monkeypatch.setenv("FS_DB_PATH", "/data/fs.db")

    s = load_settings()

    assert s.llm_base_url == "http://gpu-server:8000/v1"
    assert s.llm_model == "qwen2.5-7b"
    assert s.llm_api_key == "sk-test"  # pragma: allowlist secret
    assert s.llm_timeout == 30.5
    assert s.llm_max_attempts == 5
    assert s.llm_context == "text"
    assert s.scraper_user_agent == "TestBot/1.0"
    assert s.scraper_delay == 2.5
    assert s.scraper_concurrency == 8
    assert s.results_dir == Path("/data/out")
    assert s.jobs_dir == Path("/data/state")
    assert s.db_path == Path("/data/fs.db")
    assert isinstance(s.db_path, Path)
    assert isinstance(s, Settings)


def test_settings_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in ENV_KEYS:
        monkeypatch.delenv(key, raising=False)

    s = load_settings()

    assert s.llm_base_url == "http://localhost:11434/v1"
    assert s.llm_model == "llama3.2"
    assert s.llm_api_key == "not-needed"  # pragma: allowlist secret
    assert s.llm_timeout == 120.0
    assert s.llm_max_attempts == 3
    assert s.llm_context == "html"
    assert s.scraper_user_agent == DEFAULT_USER_AGENT
    assert s.scraper_delay == 1.0
    assert s.scraper_concurrency == 4
    assert s.results_dir == Path("data/results")
    assert s.jobs_dir == Path("data/jobs")
    assert s.db_path == Path("data/finalscoring.db")


def test_database_is_not_written_into_the_results_directory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Results holds regenerable intermediates; the database is the build's product."""
    for key in ENV_KEYS:
        monkeypatch.delenv(key, raising=False)

    s = load_settings()

    assert s.results_dir not in s.db_path.parents


def test_default_user_agent_names_the_project_and_a_contact(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An operator seeing this in their logs should know who to contact."""
    monkeypatch.delenv("FS_SCRAPER_USER_AGENT", raising=False)

    agent = load_settings().scraper_user_agent

    assert "FinalScoring" in agent
    assert "finalscoring.games" in agent


def test_an_unknown_context_mode_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    """A typo must not silently fall back and invalidate an A/B run."""
    monkeypatch.setenv("FS_LLM_CONTEXT", "markdown")

    with pytest.raises(ValueError, match="FS_LLM_CONTEXT"):
        load_settings()
