"""SQLModel definitions for the Final Scoring database.

Conventions:

* All timestamps are stored as UTC ISO-8601 strings via SQLite's TEXT
  affinity. This keeps the database trivially inspectable with the
  ``sqlite3`` CLI and avoids driver-specific datetime handling.
* ``quote_verbatim`` carries a hard 200-character upper bound enforced
  at the schema level. Copyright discipline must not depend on whoever
  is writing the next prompt remembering to be brief.
* Tables that are *derived* (``Game``, ``Aggregate``) get rebuilt every
  build. Tables that are *persistent* (``Critic``, ``Review``,
  ``SourceRun``, override tables) are preserved across builds.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ─────────────────────────────────────────────────────────────────────────
# Imported / derived tables — rebuilt every build
# ─────────────────────────────────────────────────────────────────────────


class Game(SQLModel, table=True):
    """A board game. Imported from Recommend.Games at build time.

    The BGG ID is the canonical identifier across both projects; Final
    Scoring does not invent its own game identifiers. The remaining
    fields are a thin convenience copy of upstream metadata to avoid
    cross-database joins at query time.
    """

    bgg_id: int = Field(primary_key=True)
    title: str = Field(index=True)
    year: Optional[int] = Field(default=None, index=True)
    designer: Optional[str] = Field(default=None)
    publisher: Optional[str] = Field(default=None)
    cover_url: Optional[str] = Field(default=None)
    imported_at: str = Field(default_factory=_utcnow_iso)


class Aggregate(SQLModel, table=True):
    """Computed critical reception per game.

    Regenerated whenever the underlying review set for a game changes.
    Below the minimum-reviews threshold (see ``scoring.config``), no row
    exists and the frontend displays the raw review list with a
    "insufficient critical coverage" label.
    """

    game_bgg_id: int = Field(primary_key=True, foreign_key="game.bgg_id")
    score: float = Field(description="Weighted aggregate score, 0–100.")
    score_ci_low: float = Field(description="Lower bound of the bootstrap CI.")
    score_ci_high: float = Field(description="Upper bound of the bootstrap CI.")
    review_count: int
    # JSON-encoded array of normalized scores backing the histogram.
    distribution_json: str
    methodology_version: str = Field(
        description="Versioned identifier of the scoring config used."
    )
    generated_at: str = Field(default_factory=_utcnow_iso)


# ─────────────────────────────────────────────────────────────────────────
# Persistent tables — kept across builds
# ─────────────────────────────────────────────────────────────────────────


class Critic(SQLModel, table=True):
    """A critic or reviewer source.

    "Critic" here means either an individual reviewer (Tom Brewster,
    Quinns Smith) or an outlet that publishes under a unified editorial
    voice (Dicebreaker, Shut Up & Sit Down). The choice between
    individual and outlet representation is made per source and
    documented in the source registry.

    ``source_tier`` is the published weight applied during aggregation.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    slug: str = Field(unique=True, index=True)
    name: str
    outlet: Optional[str] = Field(default=None)
    medium: str = Field(description="text | video | podcast")
    language: str = Field(description="ISO 639-1 code, e.g. 'en', 'de'.")
    homepage_url: Optional[str] = Field(default=None)
    feed_url: Optional[str] = Field(default=None)
    score_format: str = Field(
        description="One of: numeric_5, numeric_10, numeric_100, "
        "verdict_band, none.",
    )
    source_tier: float = Field(
        default=1.0,
        description="Weight applied during aggregation. Conventionally "
        "one of 1.0, 0.5, 0.25.",
    )
    opt_out: bool = Field(
        default=False,
        description="If true, no reviews from this critic are ingested "
        "or displayed. Honored regardless of source-tier value.",
    )
    notes: Optional[str] = Field(default=None)
    added_at: str = Field(default_factory=_utcnow_iso)


class Review(SQLModel, table=True):
    """A single critic's verdict on a single game.

    Distinguishes carefully between *declared* and *inferred* values:

    * ``score_declared`` — what the critic actually said, verbatim
      (e.g. "4/5", "Recommended", "8.5"). Nullable.
    * ``rating_inferred`` — a 1–10 integer derived from the review
      text. Always populated. The frontend labels this as inferred
      wherever it appears.
    * ``score_normalized`` — a 0–100 float after per-critic z-score
      adjustment. Computed at build time.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    critic_id: int = Field(foreign_key="critic.id", index=True)
    game_bgg_id: int = Field(foreign_key="game.bgg_id", index=True)

    # Provenance
    original_url: str
    original_date: Optional[str] = Field(default=None)
    source_url: Optional[str] = Field(
        default=None,
        description="The URL Final Scoring scraped. Differs from "
        "original_url when ingested via a meta-source like a roundup.",
    )
    source_critic_id: Optional[int] = Field(
        default=None,
        description="If the review was extracted from a meta-source "
        "(e.g. the SdJ Kritikenrundschau), this is the critic ID of "
        "the meta-source itself. Null for primary-source ingestion.",
    )
    language: str

    # Scoring
    score_declared: Optional[str] = Field(default=None)
    rating_inferred: int = Field(ge=1, le=10)
    score_normalized: Optional[float] = Field(default=None)
    sentiment: str = Field(description="positive | neutral | negative")

    # Content
    quote_verbatim: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Short verbatim pull-quote. Hard-capped at 200 "
        "characters at schema level — copyright discipline must not "
        "depend on humans or models remembering to be brief.",
    )
    summary: str = Field(
        description="Model-written paraphrase of the critic's view. "
        "Never reproduces source text verbatim beyond quote_verbatim.",
    )

    # Provenance / reproducibility
    extraction_model_version: str
    ingested_at: str = Field(default_factory=_utcnow_iso)


class SourceRun(SQLModel, table=True):
    """One ingestion run for one source.

    The ingestion log is the operational ground truth — if a critic's
    coverage stops updating, the answer is in here. Kept indefinitely.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    critic_id: int = Field(foreign_key="critic.id", index=True)
    run_at: str = Field(default_factory=_utcnow_iso, index=True)
    status: str = Field(description="ok | partial | failed")
    items_found: int = Field(default=0)
    items_new: int = Field(default=0)
    error: Optional[str] = Field(default=None)


# ─────────────────────────────────────────────────────────────────────────
# Override tables — manually edited, version controlled
# ─────────────────────────────────────────────────────────────────────────


class GameMatchOverride(SQLModel, table=True):
    """Manual title-to-BGG-ID override.

    When the automatic title matcher fails or produces the wrong answer,
    add an entry here. Loaded at build time before the matcher runs and
    takes precedence over fuzzy matches.

    Source-of-truth lives in ``data/overrides/games.csv``; this table is
    populated from there during the build.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    raw_title: str = Field(index=True)
    critic_slug: Optional[str] = Field(
        default=None,
        description="If set, the override only applies for reviews from "
        "this critic. Useful when two critics use the same shorthand "
        "for different games.",
    )
    bgg_id: Optional[int] = Field(
        default=None,
        description="The correct BGG ID. If null, this title is "
        "deliberately ignored (e.g. a known false positive).",
    )
    notes: Optional[str] = Field(default=None)


class CriticAlias(SQLModel, table=True):
    """Alternative names the extraction LLM might produce for a critic.

    The LLM-generated ``reviewer_id`` field in the extraction schema is
    convenient but unstable across runs — the same person may come back
    as ``tom_brewster`` one day and ``thomas_brewster`` the next. This
    table maps observed aliases to canonical critic IDs.

    Source-of-truth lives in ``data/overrides/critics.csv``.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    alias: str = Field(unique=True, index=True)
    critic_id: int = Field(foreign_key="critic.id")
    notes: Optional[str] = Field(default=None)
