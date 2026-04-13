from pydantic import BaseModel


class Game(BaseModel):
    id: int | None = None
    name: str
    slug: str
    bgg_id: int | None = None
    year_published: int | None = None
