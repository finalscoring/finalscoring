"""Critic record — an individual reviewer."""

from sqlmodel import Field, SQLModel


class Critic(SQLModel, table=True):
    __tablename__ = "critics"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    quality_weight: float = Field(default=1.0)
