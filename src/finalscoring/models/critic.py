"""Critic record — an individual reviewer."""

from pydantic import field_validator
from sqlmodel import Field, SQLModel


class Critic(SQLModel, table=True):
    __tablename__ = "critics"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    quality_weight: float = Field(default=1.0, gt=0.0)

    @field_validator("quality_weight")
    @classmethod
    def weight_positive(cls, v: float) -> float:
        if v <= 0.0:
            raise ValueError("must be greater than 0")
        return v
