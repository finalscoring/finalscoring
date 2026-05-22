"""Tests for the versioned prompt loader.

These exist to catch the case where someone removes a prompt version
that production data was extracted under — the prompt loader should
fail loudly and immediately, not silently fall back.
"""

from __future__ import annotations

import pytest

from final_scoring.pipeline.prompts import load_prompt, prompt_version_tag


def test_load_existing_prompt() -> None:
    text = load_prompt("review_extraction", "v1")
    assert text  # non-empty
    assert "review" in text.lower()


def test_load_missing_prompt_raises() -> None:
    with pytest.raises(FileNotFoundError):
        load_prompt("review_extraction", "v99")


def test_load_missing_prompt_name_raises() -> None:
    with pytest.raises(FileNotFoundError):
        load_prompt("not_a_real_prompt", "v1")


def test_prompt_version_tag_format() -> None:
    assert prompt_version_tag("review_extraction", "v1") == "review_extraction@v1"
