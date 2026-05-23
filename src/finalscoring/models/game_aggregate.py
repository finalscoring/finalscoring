"""GameAggregate record — computed scoring output for one game."""

from datetime import datetime

from sqlmodel import Field, SQLModel


class GameAggregate(SQLModel, table=True):
    __tablename__ = "game_aggregates"

    game_bgg_id: int = Field(primary_key=True, foreign_key="games.bgg_id")
    score: float = Field(ge=0.0, le=100.0)
    ci_lower: float = Field(ge=0.0, le=100.0)
    ci_upper: float = Field(ge=0.0, le=100.0)
    review_count: int = Field(gt=0)
    scoring_version: str
    scored_at: datetime
