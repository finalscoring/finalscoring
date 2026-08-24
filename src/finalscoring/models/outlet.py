"""Outlet record — a publication, site, or channel that publishes reviews."""

from pydantic import field_validator
from sqlmodel import Field, SQLModel

from finalscoring.models.enums import Medium


class Outlet(SQLModel, table=True):
    __tablename__ = "outlets"

    slug: str = Field(primary_key=True)
    name: str = Field(index=True)
    url: str | None = Field(default=None, unique=True)
    medium: Medium
    quality_weight: float = Field(default=1.0, gt=0.0)

    @field_validator("quality_weight")
    @classmethod
    def weight_positive(cls, v: float) -> float:
        if v <= 0.0:
            raise ValueError("must be greater than 0")
        return v
