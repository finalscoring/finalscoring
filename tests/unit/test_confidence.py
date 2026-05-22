"""Tests for bootstrap confidence intervals."""

from __future__ import annotations

import pytest

from final_scoring.scoring.confidence import bootstrap_ci, weighted_mean


def test_weighted_mean_basic() -> None:
    import numpy as np

    scores = np.array([70.0, 80.0, 90.0])
    weights = np.array([1.0, 1.0, 1.0])
    assert weighted_mean(scores, weights) == pytest.approx(80.0)


def test_weighted_mean_with_weights() -> None:
    import numpy as np

    scores = np.array([60.0, 90.0])
    weights = np.array([3.0, 1.0])
    # Weighted: (60*3 + 90*1) / 4 = 67.5
    assert weighted_mean(scores, weights) == pytest.approx(67.5)


def test_bootstrap_ci_single_review_degenerate() -> None:
    """A single review collapses the CI to the point estimate."""

    low, high = bootstrap_ci([85.0], [1.0])
    assert low == 85.0
    assert high == 85.0


def test_bootstrap_ci_brackets_the_mean() -> None:
    """The CI endpoints should bracket the point estimate."""

    scores = [70.0, 75.0, 80.0, 85.0, 90.0]
    weights = [1.0, 1.0, 1.0, 1.0, 1.0]
    low, high = bootstrap_ci(scores, weights, iterations=500)
    point = sum(scores) / len(scores)
    assert low <= point <= high


def test_bootstrap_ci_wider_with_disagreement() -> None:
    """Disagreement among critics widens the CI."""

    agreeing = [80.0, 81.0, 79.0, 80.0, 82.0]
    polarised = [50.0, 95.0, 60.0, 90.0, 55.0]
    weights = [1.0] * 5

    low_a, high_a = bootstrap_ci(agreeing, weights, iterations=500)
    low_p, high_p = bootstrap_ci(polarised, weights, iterations=500)

    assert (high_a - low_a) < (high_p - low_p)


def test_bootstrap_ci_is_reproducible() -> None:
    """Same inputs, same seed → identical CI across calls."""

    scores = [60.0, 70.0, 80.0, 90.0]
    weights = [1.0, 0.5, 1.0, 0.25]
    first = bootstrap_ci(scores, weights, iterations=500)
    second = bootstrap_ci(scores, weights, iterations=500)
    assert first == second
