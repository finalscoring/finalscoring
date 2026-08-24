"""Review record — one verdict on one game from one outlet."""

from datetime import datetime

from pydantic import field_validator
from sqlmodel import Field, SQLModel

from finalscoring.models.enums import Sentiment

# See docs/QUOTATION_POLICY.md
QUOTE_MAX_LENGTH = 300


class Review(SQLModel, table=True):
    __tablename__ = "reviews"

    id: int | None = Field(default=None, primary_key=True)
    game_bgg_id: int = Field(foreign_key="games.bgg_id", index=True)
    outlet_slug: str = Field(foreign_key="outlets.slug", index=True)
    critic_id: int | None = Field(default=None, foreign_key="critics.id", index=True)

    declared_score: float | None = Field(default=None, ge=0.0, le=100.0)  # normalised 0-100
    inferred_score: float | None = Field(default=None, ge=0.0, le=100.0)  # normalised 0-100
    sentiment: Sentiment | None = None

    @field_validator("declared_score", "inferred_score")
    @classmethod
    def score_in_range(cls, v: float | None) -> float | None:
        if v is not None and not (0.0 <= v <= 100.0):
            raise ValueError("must be between 0 and 100")
        return v

    @property
    def score_is_inferred(self) -> bool:
        return self.inferred_score is not None and self.declared_score is None

    quote: str | None = Field(default=None, max_length=QUOTE_MAX_LENGTH)  # verbatim snippet
    language: str  # ISO 639-1, e.g. "en", "de"

    url: str = Field(unique=True)  # deduplication key
    published_at: datetime | None = None
    scraped_at: datetime
    updated_at: datetime | None = None

    @field_validator("quote")
    @classmethod
    def quote_within_cap(cls, v: str | None) -> str | None:
        if v is not None and len(v) > QUOTE_MAX_LENGTH:
            raise ValueError(f"must be at most {QUOTE_MAX_LENGTH} characters")
        return v
