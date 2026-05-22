"""Tests for the per-critic z-score normalization."""

from __future__ import annotations

import pytest

from final_scoring.scoring.normalize import (
    apply_z_score,
    compute_critic_stats,
    global_score_stats,
    raw_to_scale,
)


def test_raw_to_scale_endpoints() -> None:
    assert raw_to_scale(1) == 5.0
    assert raw_to_scale(10) == 95.0
    # And the midpoints are sensible.
    assert raw_to_scale(5) == pytest.approx(45.0)


@pytest.mark.parametrize("bad", [0, 11, -3, 100])
def test_raw_to_scale_rejects_out_of_range(bad: int) -> None:
    with pytest.raises(ValueError):
        raw_to_scale(bad)


def test_compute_critic_stats_returns_none_for_constant_critic() -> None:
    """A reviewer who gives the same score every time has no useful spread."""

    assert compute_critic_stats([80.0, 80.0, 80.0]) is None


def test_compute_critic_stats_returns_none_below_two_reviews() -> None:
    assert compute_critic_stats([80.0]) is None
    assert compute_critic_stats([]) is None


def test_compute_critic_stats_basic() -> None:
    stats = compute_critic_stats([50.0, 60.0, 70.0, 80.0, 90.0])
    assert stats is not None
    assert stats.mean == pytest.approx(70.0)
    assert stats.count == 5


def test_apply_z_score_centers_inflated_critic() -> None:
    """A grade-inflating critic's score moves toward the global mean."""

    inflated = compute_critic_stats([90.0, 92.0, 88.0, 95.0, 91.0])
    assert inflated is not None
    global_stats = global_score_stats(
        [50.0, 60.0, 70.0, 80.0, 91.0, 90.0, 88.0, 92.0, 95.0]
    )

    # The inflated critic's "average" score (~91) should normalize
    # close to the global mean, not stay at 91.
    normalized = apply_z_score(91.0, inflated, global_stats)
    assert abs(normalized - global_stats.mean) < abs(91.0 - global_stats.mean)


def test_apply_z_score_falls_back_to_global() -> None:
    """A critic with no usable stats normalizes against the global distribution."""

    global_stats = global_score_stats([40.0, 50.0, 60.0, 70.0, 80.0])
    # Passing None for critic_stats means "use global as the reference".
    # If score == global mean, output should equal global mean.
    result = apply_z_score(global_stats.mean, None, global_stats)
    assert result == pytest.approx(global_stats.mean)


def test_apply_z_score_clips_to_range() -> None:
    """Outliers do not produce scores outside 0–100."""

    tight_critic = compute_critic_stats([50.0, 50.1, 49.9, 50.0, 50.05])
    assert tight_critic is not None
    global_stats = global_score_stats(
        [10.0, 30.0, 50.0, 70.0, 90.0]
    )
    very_high = apply_z_score(80.0, tight_critic, global_stats)
    very_low = apply_z_score(20.0, tight_critic, global_stats)
    assert 0.0 <= very_high <= 100.0
    assert 0.0 <= very_low <= 100.0
