"""GameAggregate record — computed scoring output for one game."""

from datetime import datetime

from pydantic import field_validator
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

    @field_validator("score", "ci_lower", "ci_upper")
    @classmethod
    def score_in_range(cls, v: float) -> float:
        if not (0.0 <= v <= 100.0):
            raise ValueError("must be between 0 and 100")
        return v

    @field_validator("review_count")
    @classmethod
    def count_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("must be greater than 0")
        return v
