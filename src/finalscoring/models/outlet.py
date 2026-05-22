"""Outlet record — a publication, site, or channel that publishes reviews."""

from sqlmodel import Field, SQLModel


class Outlet(SQLModel, table=True):
    __tablename__ = "outlets"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    url: str | None = None
    medium: str  # "blog", "youtube", "podcast", "magazine", …
    quality_weight: float = Field(default=1.0)
