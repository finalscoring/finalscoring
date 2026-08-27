"""Turning raw items into extracted reviews.

The stage between scraping and loading: a spider produces `RawItem`, this
package reads one and asks a model what reviews it contains, and the load
step consumes the `ExtractionRecord` that comes out.
"""

from finalscoring.extraction.context import build_context, clean_html
from finalscoring.extraction.llm import ExtractionFailed, ReviewExtractor
from finalscoring.extraction.record import ExtractionRecord, prompt_sha
from finalscoring.extraction.schema import (
    PROMPT,
    PROMPT_VERSION,
    ExtractedGame,
    ExtractedReview,
    ExtractionResult,
)

__all__ = [
    "PROMPT",
    "PROMPT_VERSION",
    "ExtractedGame",
    "ExtractedReview",
    "ExtractionFailed",
    "ExtractionRecord",
    "ExtractionResult",
    "ReviewExtractor",
    "build_context",
    "clean_html",
    "prompt_sha",
]
