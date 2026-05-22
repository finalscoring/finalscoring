from pathlib import Path

import pytest

from finalscoring.settings import Settings, load_settings


def test_settings_reads_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FS_LLM_BASE_URL", "http://gpu-server:8000/v1")
    monkeypatch.setenv("FS_LLM_MODEL", "qwen2.5-7b")
    monkeypatch.setenv("FS_SCRAPER_DELAY", "2.5")
    monkeypatch.setenv("FS_DB_PATH", "/data/fs.db")

    s = load_settings()

    assert s.llm_base_url == "http://gpu-server:8000/v1"
    assert s.llm_model == "qwen2.5-7b"
    assert s.scraper_delay == 2.5
    assert s.db_path == Path("/data/fs.db")
    assert isinstance(s.db_path, Path)
    assert isinstance(s, Settings)


def test_settings_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in ("FS_LLM_BASE_URL", "FS_LLM_MODEL", "FS_SCRAPER_DELAY", "FS_DB_PATH"):
        monkeypatch.delenv(key, raising=False)

    s = load_settings()

    assert s.llm_base_url == "http://localhost:11434/v1"
    assert s.llm_model == "llama3.2"
    assert s.scraper_delay == 1.0
    assert s.db_path == Path("data/results/finalscoring.db")
