"""Raw item — the record every spider produces, consumed by the LLM extraction step."""

import re
from datetime import UTC, datetime

from pydantic import BaseModel, Field, field_validator

_ISO_639_1 = re.compile(r"^[a-z]{2}$")


class RawItem(BaseModel):
    """Contract between a spider and the LLM extraction pipeline."""

    url: str
    source_id: str  # slug identifying the spider, e.g. "spiel_des_jahres"
    raw_text: str
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    title: str | None = None  # page/article title — LLM context
    description: str | None = None  # meta description — LLM context
    published_at: datetime | None = None
    language: str | None = None  # ISO 639-1, if detectable at scrape time

    @field_validator("url", "source_id", "raw_text")
    @classmethod
    def non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be empty")
        return v

    @field_validator("language")
    @classmethod
    def valid_language_code(cls, v: str | None) -> str | None:
        if v is not None and not _ISO_639_1.match(v):
            raise ValueError("language must be an ISO 639-1 two-letter code, e.g. 'en'")
        return v
