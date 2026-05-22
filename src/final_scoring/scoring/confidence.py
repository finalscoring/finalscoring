"""Confidence intervals for aggregate scores.

Uses bootstrap resampling (percentile method) over the weighted review
set. Honest about both small-N games (wide CI from few reviews) and
disagreement among critics (wide CI from variance). The result is the
``score_ci_low``/``score_ci_high`` pair on each ``Aggregate`` row.

Why bootstrap rather than a closed-form weighted standard error: the
review counts are small (often single digits even for popular games),
the weights are not uniform, and the underlying distributions are not
necessarily normal. Bootstrap CIs degrade gracefully across all these
conditions without requiring distributional assumptions that wouldn't
hold.
"""

from __future__ import annotations

import numpy as np


def weighted_mean(scores: np.ndarray, weights: np.ndarray) -> float:
    """Compute the weighted mean of a score array."""

    w_sum = weights.sum()
    if w_sum == 0:
        return float("nan")
    return float((scores * weights).sum() / w_sum)


def bootstrap_ci(
    scores: list[float],
    weights: list[float],
    *,
    iterations: int = 2000,
    percentile_low: float = 10.0,
    percentile_high: float = 90.0,
    rng_seed: int | None = 42,
) -> tuple[float, float]:
    """Compute a percentile bootstrap CI for the weighted mean.

    Args:
        scores: Per-review normalized scores.
        weights: Per-review weights (typically the critic's source tier).
        iterations: Number of bootstrap resamples. 2000 is the default;
            higher gives tighter, more reproducible CIs at the cost of
            build time.
        percentile_low, percentile_high: The interval's endpoints, in
            percent. (10, 90) gives an 80% CI, which we display as the
            "range".
        rng_seed: Seed for reproducibility — fixed by default so that a
            given input always produces the same CI in successive
            builds. Set to ``None`` for non-reproducible runs.

    Returns:
        ``(low, high)`` — the CI endpoints in 0–100 score units.
    """

    if not scores:
        return (float("nan"), float("nan"))

    rng = np.random.default_rng(rng_seed)
    s = np.asarray(scores, dtype=float)
    w = np.asarray(weights, dtype=float)
    n = len(s)

    if n == 1:
        # A single review cannot generate a meaningful CI; return the
        # point estimate as both ends. The build sets review_count and
        # the frontend handles the degenerate display.
        return (float(s[0]), float(s[0]))

    indices = rng.integers(0, n, size=(iterations, n))
    sample_scores = s[indices]
    sample_weights = w[indices]
    w_sums = sample_weights.sum(axis=1)
    # Guard against any all-zero-weight resample (extremely unlikely but
    # not impossible if all weights are very small).
    w_sums[w_sums == 0] = 1.0
    means = (sample_scores * sample_weights).sum(axis=1) / w_sums

    low = float(np.percentile(means, percentile_low))
    high = float(np.percentile(means, percentile_high))
    return low, high
