"""Raw item — the record every spider produces, consumed by the LLM extraction step."""

import re
from datetime import UTC, date, datetime
from typing import Any
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator, model_validator

from finalscoring.models import Medium, RatingSystem

_ISO_639_1 = re.compile(r"^[a-z]{2}$")
_LOCALE = re.compile(r"^[a-z]{2}(-[A-Za-z0-9]{2,8})*$")


def language_from_locale(locale: str | None) -> str | None:
    """ "de_DE" / "de-DE" -> "de"; None for anything not a two-letter language."""
    if not locale:
        return None
    code = locale.replace("-", "_").split("_", 1)[0].strip().lower()
    return code if _ISO_639_1.match(code) else None


def _blank_to_none(v: Any) -> Any:
    # Models and scrapers alike return "" or "   " as readily as they omit a field.
    return v.strip() or None if isinstance(v, str) else v


def _drop_blank_strings(v: Any) -> Any:
    if isinstance(v, list):
        return [s.strip() for s in v if isinstance(s, str) and s.strip()]
    return v


class SourceRating(BaseModel):
    """One verdict a source states, verbatim and un-normalised.

    Faithful to the page: nothing is converted to the 0-100 scale — that is a
    load-step decision — and there is one entry per (system, critic, axis) the
    page actually shows. games-we-play states three at once; hall9000 states one
    per critic per axis.
    """

    system: RatingSystem
    critic_name: str | None = None  # set only where the page attributes the rating
    axis: str | None = None  # a sub-dimension; None is the overall verdict
    value: float | None = None  # a number; "4,5" is normalised to 4.5, verbatim keeps it
    scale_min: float | None = None  # 0.5 for half-star scales, schema.org worstRating
    scale_max: float | None = None
    label: str | None = None  # a verbal verdict: "solide", "Great - Would recommend"
    note: str | None = None  # the critic's own words tied to this rating (hall9000 notes)
    stated_at: date | None = None  # when this rating was given, if distinct from the page
    verbatim: str | None = None  # the exact source string, kept for audit

    @field_validator("critic_name", "axis", "label", "note", "verbatim", mode="before")
    @classmethod
    def blank_to_none(cls, v: Any) -> Any:
        return _blank_to_none(v)

    @field_validator("value", "scale_min", "scale_max", mode="before")
    @classmethod
    def german_decimal_comma(cls, v: Any) -> Any:
        # "4,5 H@LL9000" reaches here as "4,5"; the caller keeps the original in verbatim.
        return v.replace(",", ".") if isinstance(v, str) else v

    @model_validator(mode="after")
    def scale_bounds_ordered(self) -> SourceRating:
        low, high = self.scale_min, self.scale_max
        if low is not None and high is not None and low >= high:
            raise ValueError("scale_min must be below scale_max")
        return self


class RawGameHint(BaseModel):
    """What the spider already knows about the game, structured.

    Matching evidence for the BGG resolution step, not data to keep — `games` is
    keyed on `bgg_id` and takes its facts from BGG once resolved. The LLM also
    extracts the game from the prose; this is the higher-trust second signal,
    and luding's `bgg_id` settles a match outright.
    """

    title: str | None = None  # the source's own metadata title, if it differs from the page
    designers: list[str] = Field(default_factory=list)
    publishers: list[str] = Field(default_factory=list)  # co-editions are normal
    artists: list[str] = Field(default_factory=list)
    year_published: int | None = None
    bgg_id: int | None = None  # settles the match on its own
    bgg_url: str | None = None
    external_ids: dict[str, str] = Field(default_factory=dict)  # e.g. {"luding_id": "..."}
    player_count_min: int | None = None
    player_count_max: int | None = None
    playing_time_min: int | None = None  # minutes
    playing_time_max: int | None = None
    min_age: int | None = None
    categories: list[str] = Field(default_factory=list)  # genre / game type
    mechanics: list[str] = Field(default_factory=list)
    complexity_label: str | None = None  # "mittel", "sehr einfach" — an attribute, not a verdict
    source: str | None = None  # where the hint came from ("hall9000 info box", "luding row")

    @field_validator("title", "bgg_url", "complexity_label", "source", mode="before")
    @classmethod
    def blank_to_none(cls, v: Any) -> Any:
        return _blank_to_none(v)

    @field_validator("designers", "publishers", "artists", "categories", "mechanics", mode="before")
    @classmethod
    def drop_blanks(cls, v: Any) -> Any:
        return _drop_blank_strings(v)

    @field_validator("year_published")
    @classmethod
    def plausible_year(cls, v: int | None) -> int | None:
        # Out of range means the source string was misread; better to drop it.
        # Same rule as extraction's ExtractedGame.plausible_year — computed here
        # too rather than shared, to keep this module off the extraction import.
        if v is None:
            return None
        max_year = date.today().year + 2
        if not 1900 <= v <= max_year:
            raise ValueError(f"year_published must be between 1900 and {max_year}")
        return v


class RawItem(BaseModel):
    """Contract between a spider and the LLM extraction pipeline."""

    url: str
    canonical_url: str | None = None  # <link rel=canonical> / og:url, when it differs from url
    spider_slug: str  # identifies the fetcher, not necessarily the outlet
    source_host: str | None = None  # url's host; the key the load step resolves to an outlet
    raw_text: str  # plain-text rendering; what gets fed to the LLM
    raw_html: str | None = (
        None  # source HTML, preserved for reprocessing; None for non-HTML sources
    )
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Page / article metadata
    title: str | None = None
    description: str | None = None
    published_at: datetime | None = None
    modified_at: datetime | None = None  # article:modified_time — informs re-crawl
    language: str | None = None  # ISO 639-1, if detectable at scrape time
    locale: str | None = None  # BCP 47, e.g. "de-AT" — regional variant matters
    image_url: str | None = None  # og:image / thumbnail
    duration_seconds: int | None = None  # audio / video content

    # Editorial classification, as the source applied it
    tags: list[str] = Field(default_factory=list)  # free-form topic labels, nothing else
    categories: list[str] = Field(default_factory=list)  # the source's section taxonomy
    taxonomy: dict[str, list[str]] = Field(default_factory=dict)  # richer per-kind terms
    editorial_flags: list[str] = Field(default_factory=list)  # marks like "TOPspiel", verbatim

    # The verdict(s) the source states, structured and un-normalised
    ratings: list[SourceRating] = Field(default_factory=list)

    # What the spider knows about the game and who wrote the review
    game: RawGameHint | None = None
    bylines: list[str] = Field(default_factory=list)  # names credited on the page
    known_critic_name: str | None = None  # a single-critic source's sole reviewer

    # Review medium, when the spider is certain (a video host, a print roundup)
    medium: Medium | None = None

    # Outlet hint — when identifiable at scrape time (e.g. from domain)
    outlet_slug: str | None = None

    # Structured metadata from web standards
    og_site_name: str | None = None  # og:site_name, often the outlet name
    oembed: dict[str, Any] | None = None
    schema_org: list[dict[str, Any]] = Field(default_factory=list)

    # Upstream payloads kept only for reprocessing / debugging; nothing reads specific keys
    extra: dict[str, Any] = Field(default_factory=dict)

    @field_validator("url", "spider_slug", "raw_text")
    @classmethod
    def non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be empty")
        return v

    @field_validator(
        "canonical_url", "source_host", "known_critic_name", "og_site_name", mode="before"
    )
    @classmethod
    def blank_to_none(cls, v: Any) -> Any:
        return _blank_to_none(v)

    @field_validator("tags", "categories", "editorial_flags", "bylines", mode="before")
    @classmethod
    def drop_blanks(cls, v: Any) -> Any:
        return _drop_blank_strings(v)

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

    @model_validator(mode="after")
    def default_source_host(self) -> RawItem:
        # Left to the fetched url's host unless a spider set it, so it is always usable.
        if not self.source_host:
            self.source_host = urlparse(self.url).netloc or None
        return self
