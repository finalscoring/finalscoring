"""Raw item — the record every spider produces, consumed by the LLM extraction step."""

import re
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

_ISO_639_1 = re.compile(r"^[a-z]{2}$")
_LOCALE = re.compile(r"^[a-z]{2}(-[A-Za-z0-9]{2,8})*$")


class RawItem(BaseModel):
    """Contract between a spider and the LLM extraction pipeline."""

    url: str
    spider_slug: str  # identifies the fetcher, not necessarily the outlet
    raw_text: str  # plain-text rendering; what gets fed to the LLM
    raw_html: str | None = (
        None  # source HTML, preserved for reprocessing; None for non-HTML sources
    )
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Page / article metadata
    title: str | None = None
    description: str | None = None
    published_at: datetime | None = None
    language: str | None = None  # ISO 639-1, if detectable at scrape time
    locale: str | None = None  # BCP 47, e.g. "de-AT" — regional variant matters
    image_url: str | None = None  # og:image / thumbnail
    tags: list[str] = Field(default_factory=list)
    duration_seconds: int | None = None  # audio / video content

    # Outlet hint — when identifiable at scrape time (e.g. from domain)
    outlet_slug: str | None = None

    # Structured metadata from web standards
    og_site_name: str | None = None  # og:site_name, often the outlet name
    oembed: dict[str, Any] | None = None
    schema_org: list[dict[str, Any]] = Field(default_factory=list)

    # Catch-all for any other structured data the spider wants to preserve
    extra: dict[str, Any] = Field(default_factory=dict)

    @field_validator("url", "spider_slug", "raw_text")
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

    @field_validator("locale")
    @classmethod
    def valid_locale(cls, v: str | None) -> str | None:
        # Sources spell it "de_DE" (Open Graph) or "de-DE" (html lang).
        if v is None:
            return None
        normalised = v.strip().replace("_", "-")
        if not normalised:
            return None
        language, _, region = normalised.partition("-")
        normalised = f"{language.lower()}-{region.upper()}" if region else language.lower()
        if not _LOCALE.match(normalised):
            raise ValueError("locale must be a BCP 47 tag, e.g. 'de-AT'")
        return normalised
