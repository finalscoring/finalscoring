"""Per-critic score normalization.

Two-stage process:

1. Map each critic's raw score onto a common 0–100 scale based on their
   declared ``score_format`` (numeric_5, numeric_10, etc.). This is
   purely deterministic and lives in :func:`raw_to_scale`.

2. For critics with enough data, apply a z-score adjustment so that a
   grade-inflating reviewer's 9/10 doesn't carry the same weight as a
   hard marker's 9/10. Critics below the data threshold get a fallback
   normalization against the global distribution. See
   :func:`apply_z_score`.

The output is written to ``Review.score_normalized``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import mean, pstdev


SCORE_FORMAT_SCALES: dict[str, float] = {
    "numeric_5": 5.0,
    "numeric_10": 10.0,
    "numeric_100": 100.0,
}


def raw_to_scale(rating_inferred: int) -> float:
    """Map a 1–10 inferred rating to a 0–100 score.

    The inferred rating is the LLM's own 1–10 derived value, which
    already follows a defined rubric (see the extraction prompt).
    Mapping is linear with a fixed offset to avoid the all-zeros corner:
    rating 1 → 5, rating 10 → 95.
    """

    if not 1 <= rating_inferred <= 10:
        raise ValueError(f"rating_inferred out of range: {rating_inferred}")
    # 1 → 5, 10 → 95, linear in between.
    return 5.0 + (rating_inferred - 1) * 10.0


@dataclass(frozen=True)
class CriticStats:
    """Per-critic distribution statistics for z-score adjustment."""

    mean: float
    stdev: float
    count: int


def compute_critic_stats(scores: list[float]) -> CriticStats | None:
    """Compute mean and stdev for a critic's scores.

    Returns ``None`` if the critic has too few reviews or zero variance.
    A zero-variance critic (every score identical) cannot be z-score
    adjusted meaningfully; fall back to the global normalization.
    """

    if len(scores) < 2:
        return None
    m = mean(scores)
    sd = pstdev(scores)
    if sd == 0:
        return None
    return CriticStats(mean=m, stdev=sd, count=len(scores))


def apply_z_score(
    score: float,
    critic_stats: CriticStats | None,
    global_stats: CriticStats,
) -> float:
    """Adjust a single score against critic-personal or global stats.

    The output is a 0–100 value: the input score is rescaled relative to
    the chosen distribution, then mapped back to the original scale via
    the global mean and stdev. This is a deliberate choice — pure
    z-scores are unintuitive to display, while this approach keeps the
    output on the familiar 0–100 axis while removing per-critic bias.
    """

    reference = critic_stats if critic_stats is not None else global_stats
    if reference.stdev == 0:
        return score  # nothing meaningful to normalize against
    z = (score - reference.mean) / reference.stdev
    normalized = global_stats.mean + z * global_stats.stdev
    # Clip to a sane range; extreme z-scores from outlier reviewers
    # shouldn't drive the output outside 0–100.
    return max(0.0, min(100.0, normalized))


def global_score_stats(scores: list[float]) -> CriticStats:
    """Compute global mean/stdev over all scores in the database.

    Used as the reference distribution for critics that don't have
    enough data for personal z-score adjustment.
    """

    if not scores:
        # Degenerate case — return a neutral identity reference so
        # downstream math doesn't divide by zero. The build's
        # min-reviews threshold should prevent this in practice.
        return CriticStats(mean=50.0, stdev=15.0, count=0)
    m = mean(scores)
    sd = pstdev(scores) if len(scores) >= 2 else 15.0
    if sd == 0 or math.isnan(sd):
        sd = 15.0
    return CriticStats(mean=m, stdev=sd, count=len(scores))
