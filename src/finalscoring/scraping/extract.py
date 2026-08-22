"""LLM extraction schema — the structured output the model must produce per review."""

import re
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

from finalscoring.models.review import QUOTE_MAX_LENGTH, Sentiment

PROMPT_V1 = (Path(__file__).parent / "prompts" / "extract_v1.txt").read_text()

_ISO_639_1 = re.compile(r"^[a-z]{2}$")


class ExtractedReview(BaseModel):
    """One (game, reviewer) pair extracted from a raw item by the LLM."""

    # Identity — resolved to DB records in the load step
    game_title: str  # as named in the text
    reviewer_name: str  # as named in the text; outlet name if no individual is identified
    outlet_name: str | None = None  # publication/outlet as named in the text

    # Score -- raw LLM output; normalisation to 0-100 happens in the scoring step
    raw_score: str | None = None  # score verbatim (e.g. "4/5", "sehr gut")
    rating: int = Field(ge=1, le=10)  # 1-10 LLM interpretation

    sentiment: Sentiment
    quote: str | None = Field(default=None, max_length=QUOTE_MAX_LENGTH)  # verbatim
    language: str  # ISO 639-1

    @field_validator("game_title", "reviewer_name")
    @classmethod
    def non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be empty")
        return v

    @field_validator("language")
    @classmethod
    def valid_language_code(cls, v: str) -> str:
        if not _ISO_639_1.match(v):
            raise ValueError("language must be an ISO 639-1 two-letter code, e.g. 'en'")
        return v


class ExtractionResult(BaseModel):
    """Container for all reviews extracted from a single raw item."""

    reviews: list[ExtractedReview]
