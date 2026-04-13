from datetime import date

from pydantic import BaseModel, HttpUrl


class Review(BaseModel):
    id: int | None = None
    game_id: int
    publication_id: int
    title: str
    url: HttpUrl
    original_score: str | None = None
    normalised_score: float | None = None
    published_date: date | None = None
