from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from finalscoring.db.base import Base


class GameModel(Base):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    bgg_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    year_published: Mapped[int | None] = mapped_column(Integer, nullable=True)


class PublicationModel(Base):
    __tablename__ = "publications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    website_url: Mapped[str | None] = mapped_column(String(500), nullable=True)


class ReviewModel(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"), index=True)
    publication_id: Mapped[int] = mapped_column(ForeignKey("publications.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(String(500), unique=True)
    original_score: Mapped[str | None] = mapped_column(String(64), nullable=True)
    normalised_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    published_date: Mapped[date | None] = mapped_column(Date, nullable=True)
