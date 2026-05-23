"""Review record — one verdict on one game from one outlet."""

from datetime import date

from sqlmodel import Field, SQLModel


class Review(SQLModel, table=True):
    __tablename__ = "reviews"

    id: int | None = Field(default=None, primary_key=True)
    game_bgg_id: int = Field(foreign_key="games.bgg_id", index=True)
    outlet_id: int = Field(foreign_key="outlets.id", index=True)
    critic_id: int | None = Field(default=None, foreign_key="critics.id", index=True)

    declared_score: float | None = None  # explicit numeric score, normalised 0-100
    inferred_score: float | None = None  # LLM-mapped verbal verdict, normalised 0-100

    @property
    def score_is_inferred(self) -> bool:
        return self.inferred_score is not None and self.declared_score is None

    quote: str | None = None  # verbatim attributed snippet
    language: str  # ISO 639-1, e.g. "en", "de"

    url: str = Field(unique=True)  # deduplication key
    review_date: date | None = None
