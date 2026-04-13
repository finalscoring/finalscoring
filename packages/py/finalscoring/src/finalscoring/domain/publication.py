from pydantic import BaseModel, HttpUrl


class Publication(BaseModel):
    id: int | None = None
    name: str
    slug: str
    website_url: HttpUrl | None = None
