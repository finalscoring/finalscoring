"""Versioned prompt loading.

Prompts are stored as text files under ``prompts/<name>/<version>.md``
rather than as Python string constants. Two reasons:

1. The mantras commit Final Scoring to publishing its methodology in the
   open. Prompts are part of the methodology and should be reviewable as
   plain documents, not buried in source.
2. Versioning is a foundation for reproducibility. The ``Review`` table
   stores the prompt version used to extract it, so re-runs can be
   compared cleanly.

Conventionally each prompt directory contains a ``CHANGELOG.md``
explaining the diff between versions.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path


PROMPTS_DIR = Path(__file__).resolve().parents[3] / "prompts"


@lru_cache(maxsize=32)
def load_prompt(name: str, version: str) -> str:
    """Load a prompt by name and version.

    Raises:
        FileNotFoundError: if ``prompts/<name>/<version>.md`` does not
            exist. This is fatal — silent fallback to a different version
            would break reproducibility.
    """

    path = PROMPTS_DIR / name / f"{version}.md"
    if not path.is_file():
        raise FileNotFoundError(
            f"No prompt found at {path}. Available prompts: "
            f"{sorted(p.name for p in PROMPTS_DIR.iterdir() if p.is_dir())}"
        )
    return path.read_text(encoding="utf-8").strip()


def prompt_version_tag(name: str, version: str) -> str:
    """Return the canonical identifier stored alongside extracted reviews.

    Format: ``<name>@<version>``. Used for the
    ``Review.extraction_model_version`` field together with the model name.
    """

    return f"{name}@{version}"
