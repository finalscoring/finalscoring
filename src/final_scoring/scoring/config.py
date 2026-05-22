"""Scoring configuration.

All tunable parameters of the scoring methodology live here, in one
versioned config object. The version string lands on every ``Aggregate``
row, so a later change is auditable: any score generated under v1 of
the methodology stays comparable to others generated under v1.

The methodology document on the public site is generated from the same
constants — there is no separate "the methodology page says X but the
code does Y" risk.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ScoringConfig(BaseModel):
    """Versioned scoring parameters."""

    version: str = Field(
        description="Methodology version tag stored on Aggregate rows."
    )

    # ─── Aggregation ──────────────────────────────────────────────────
    min_reviews_for_aggregate: int = Field(
        default=4,
        description="A game needs at least this many ingested reviews "
        "before a public aggregate is computed. Below the threshold, "
        "individual reviews still list but no score is shown.",
    )

    # ─── Per-critic normalization ────────────────────────────────────
    min_reviews_for_z_score: int = Field(
        default=15,
        description="Critics with fewer than this many ingested reviews "
        "do not get personal z-score adjustment; their reviews are "
        "compared to the global mean instead. Below the threshold, the "
        "personal mean is too noisy to be useful.",
    )

    # ─── Source tiering ───────────────────────────────────────────────
    valid_tiers: tuple[float, ...] = Field(
        default=(1.0, 0.5, 0.25),
        description="Allowed values for Critic.source_tier. Build "
        "fails if a critic record uses any other value.",
    )

    # ─── Confidence intervals ────────────────────────────────────────
    bootstrap_iterations: int = Field(
        default=2000,
        description="Number of bootstrap resamples for CI computation. "
        "2000 is a reasonable balance of stability and build speed.",
    )
    ci_percentile_low: float = Field(default=10.0, ge=0.0, le=50.0)
    ci_percentile_high: float = Field(default=90.0, ge=50.0, le=100.0)

    # ─── Score band cutoffs (informational, for the methodology page) ─
    band_acclaimed: float = Field(default=85.0)
    band_recommended: float = Field(default=70.0)
    band_mixed: float = Field(default=50.0)
    # Below band_mixed is "criticised".


def default_scoring_config() -> ScoringConfig:
    """Return the current Final Scoring scoring config.

    Bumping the version here invalidates all previously-computed
    aggregates on the next build — they get regenerated under the new
    config. Existing reviews are not affected; only aggregates.
    """

    return ScoringConfig(version="v1")
