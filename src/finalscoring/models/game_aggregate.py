"""GameAggregate record — computed scoring output for one game."""

from datetime import datetime

from sqlmodel import Field, SQLModel


class GameAggregate(SQLModel, table=True):
    __tablename__ = "game_aggregates"

    game_bgg_id: int = Field(primary_key=True, foreign_key="games.bgg_id")
    score: float
    ci_lower: float
    ci_upper: float
    review_count: int
    scoring_version: str
    scored_at: datetime
