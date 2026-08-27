"""Turning raw items into extracted reviews.

The stage between scraping and loading: a spider produces `RawItem`, this
package reads one and asks a model what reviews it contains, and the load
step consumes the `ExtractionRecord` that comes out.
"""

from finalscoring.extraction.llm import ExtractionFailed, ReviewExtractor
from finalscoring.extraction.record import ExtractionRecord, prompt_sha
from finalscoring.extraction.schema import (
    PROMPT_V1,
    ExtractedGame,
    ExtractedReview,
    ExtractionResult,
)

__all__ = [
    "PROMPT_V1",
    "ExtractedGame",
    "ExtractedReview",
    "ExtractionFailed",
    "ExtractionRecord",
    "ExtractionResult",
    "ReviewExtractor",
    "prompt_sha",
]
