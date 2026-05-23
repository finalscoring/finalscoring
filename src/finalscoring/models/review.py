"""Review record — one verdict on one game from one outlet."""

from datetime import datetime
from enum import StrEnum

from sqlmodel import Field, SQLModel


class Sentiment(StrEnum):
    negative = "negative"
    mixed_negative = "mixed_negative"
    neutral = "neutral"
    mixed_positive = "mixed_positive"
    positive = "positive"


class Review(SQLModel, table=True):
    __tablename__ = "reviews"

    id: int | None = Field(default=None, primary_key=True)
    game_bgg_id: int = Field(foreign_key="games.bgg_id", index=True)
    outlet_slug: str = Field(foreign_key="outlets.slug", index=True)
    critic_id: int | None = Field(default=None, foreign_key="critics.id", index=True)

    declared_score: float | None = None  # explicit numeric score, normalised 0-100
    inferred_score: float | None = None  # LLM-mapped verbal verdict, normalised 0-100
    sentiment: Sentiment | None = None

    @property
    def score_is_inferred(self) -> bool:
        return self.inferred_score is not None and self.declared_score is None

    quote: str | None = None  # verbatim attributed snippet
    language: str  # ISO 639-1, e.g. "en", "de"

    url: str = Field(unique=True)  # deduplication key
    published_at: datetime | None = None
    scraped_at: datetime
    updated_at: datetime | None = None
