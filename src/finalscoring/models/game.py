"""Game record — the canonical representation of a board game."""

from sqlmodel import Field, SQLModel


class Game(SQLModel, table=True):
    __tablename__ = "games"

    bgg_id: int = Field(primary_key=True)
    name: str
    year_published: int | None = None
    thumbnail_url: str | None = None
