"""The envelope around one extraction call's output.

ExtractedReview/ExtractionResult are what the model produces; nothing there
should describe the run itself, or the model could report its own version
and get it wrong — the same trap as an LLM-invented reviewer_id
(SDJ_PIPELINE_NOTES.md gap #4). This holds what the *caller* knows instead:
which source, which model, which prompt. One JSONL line per record is the
extraction output stream.
"""

import hashlib
from datetime import UTC, datetime

from pydantic import BaseModel, Field

from finalscoring.scraping.extract import ExtractionResult


def prompt_sha(prompt_text: str) -> str:
    """A short, deterministic fingerprint of a prompt's actual contents.

    A filename like "extract_v1" only proves nobody renamed the file — not
    that nobody edited it. This proves the bytes.
    """
    return hashlib.sha256(prompt_text.encode()).hexdigest()[:12]


class ExtractionRecord(BaseModel):
    """One extraction call: which source, which model and prompt, what came back."""

    source_url: str  # joins back to the RawItem this came from
    model: str
    prompt_version: str
    prompt_sha: str
    extracted_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    result: ExtractionResult
