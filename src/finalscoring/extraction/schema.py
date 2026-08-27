"""LLM extraction schema — the structured output the model must produce per review."""

import logging
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator

from finalscoring.models import QUOTE_MAX_LENGTH, Medium, Sentiment

LOGGER = logging.getLogger(__name__)

PROMPT_V1 = (Path(__file__).parent / "prompts" / "extract_v1.txt").read_text()

_BGG_HOSTS = frozenset({"boardgamegeek.com", "www.boardgamegeek.com"})

_ISO_639_1 = re.compile(r"^[a-z]{2}$")


class ExtractedGame(BaseModel):
    """The game a review is about, as the text identifies it.

    Matching evidence for the BGG resolution step, not data to keep: `games` is
    keyed on `bgg_id` and takes its facts from BGG once resolved. Title alone
    does not resolve — a German edition called "Astrobienen" is BGG's "Apiary" —
    so the designer and publisher the text almost always names are what
    disambiguate.
    """

    title: str  # as named in the text, which beats the headline
    designers: list[str] = Field(default_factory=list)
    publishers: list[str] = Field(default_factory=list)  # co-editions are normal
    year_published: int | None = None
    bgg_url: str | None = None  # a link, where one exists, settles the match outright

    @field_validator("title")
    @classmethod
    def non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be empty")
        return v

    @field_validator("designers", "publishers", mode="before")
    @classmethod
    def drop_blanks(cls, v: Any) -> Any:
        # Models emit [""] and ["   "] as readily as [].
        if isinstance(v, list):
            return [name.strip() for name in v if isinstance(name, str) and name.strip()]
        return v

    @field_validator("year_published")
    @classmethod
    def plausible_year(cls, v: int | None) -> int | None:
        # Out of range means the model is confabulating, and a retry is worth it.
        if v is None:
            return None
        max_year = date.today().year + 2
        if not 1900 <= v <= max_year:
            raise ValueError(f"year_published must be between 1900 and {max_year}")
        return v

    @field_validator("bgg_url", mode="before")
    @classmethod
    def bgg_url_or_nothing(cls, v: Any) -> Any:
        # Coerced rather than rejected: a model that puts a shop link here will
        # do it again on every retry, costing the whole page over one optional
        # field. Logged because the id is parsed out of this downstream, so a
        # confabulated url would become a confident mismatch.
        if not isinstance(v, str):
            return v
        url = v.strip()
        if not url:
            return None
        if urlparse(url).hostname not in _BGG_HOSTS:
            LOGGER.warning("discarding non-BGG bgg_url: %s", url)
            return None
        return url


class ExtractedReview(BaseModel):
    """One (game, reviewer) pair extracted from a raw item by the LLM."""

    # Identity — resolved to DB records in the load step. The game belongs here
    # rather than on ExtractionResult because it is half of that pair: one page
    # can be many critics on one game, or one critic on ten games.
    game: ExtractedGame
    reviewer_name: str  # as named in the text; outlet name if no individual is identified
    outlet_name: str | None = None  # publication/outlet as named in the text

    # Provenance of the review itself, as stated in the text. For a meta-source
    # such as a roundup these differ from the scraped page's url and date, which
    # the spider supplies separately. A print review has no url and never will —
    # published_in carries the attribution the url cannot.
    medium: Medium | None = None  # how it was published, when the text says
    published_in: str | None = None  # e.g. "Spielbox 3/2024, S. 42"
    review_url: str | None = None  # the critic's own review, when cited
    published_at: datetime | None = None  # when that review appeared

    # Score -- raw LLM output; normalisation to 0-100 happens in the scoring step
    raw_score: str | None = None  # score verbatim (e.g. "4/5", "sehr gut")
    rating: int = Field(ge=1, le=10)  # 1-10 LLM interpretation

    sentiment: Sentiment
    quote: str | None = Field(default=None, max_length=QUOTE_MAX_LENGTH)  # verbatim
    language: str  # ISO 639-1 of the quoted text

    @field_validator("reviewer_name")
    @classmethod
    def non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be empty")
        return v

    @field_validator("medium", "published_in", "review_url", mode="before")
    @classmethod
    def blank_to_none(cls, v: Any) -> Any:
        # Models return "" or "   " as readily as they omit a nullable field.
        if isinstance(v, str):
            return v.strip() or None
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
