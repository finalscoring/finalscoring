"""Outlet record — a publication, site, or channel that publishes reviews."""

from enum import StrEnum

from sqlmodel import Field, SQLModel


class Medium(StrEnum):
    text = "text"
    video = "video"
    podcast = "podcast"
    print_ = "print"
    social = "social"


class Outlet(SQLModel, table=True):
    __tablename__ = "outlets"

    slug: str = Field(primary_key=True)
    name: str = Field(index=True)
    url: str | None = Field(default=None, unique=True)
    medium: Medium
    quality_weight: float = Field(default=1.0, gt=0.0)
