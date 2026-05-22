# 005 — Bootstrap percentile confidence intervals

**Status:** Accepted.
**Date:** 2026-05.

## Context

Final Scoring displays a single 0–100 aggregate score per game, but
that number on its own is misleading. A game with 12 reviews averaging
85 with high agreement is a different signal from a game with 4
polarising reviews that happen to average 85. Showing a confidence
interval alongside the headline score communicates this distinction
without requiring readers to interpret a histogram.

The aggregate is a tier-weighted mean over a small, unequally-weighted
sample of normalized scores. The reviews are not drawn from a normal
distribution and the sample size is often single digits. A closed-form
weighted standard error would require distributional assumptions that
don't hold here.

## Decision

CIs are computed by percentile bootstrap:

- 2000 resamples (configurable via `ScoringConfig.bootstrap_iterations`).
- Sampling is with replacement, preserving the per-review weight.
- Endpoints are the 10th and 90th percentiles of the resampled weighted
  means (an 80% CI, displayed as a range).
- A fixed RNG seed ensures reproducibility: the same input always
  produces the same CI.

The CI endpoints are stored on every `Aggregate` row as
`score_ci_low` and `score_ci_high`.

## Consequences

**Committed to:**
- Bootstrap cost is part of the build budget. 2000 iterations × N
  reviews × M games is tractable for any realistic catalog size.
- CIs are deterministic across builds when inputs are unchanged. The
  RNG seed is a constant.
- Games with a single review have CI equal to the point estimate.
  The frontend treats this as a degenerate case worth labelling.

**Precluded:**
- Closed-form weighted SE-based CIs. The distributional assumptions
  don't hold and we don't want to defend them.

## Reversibility

The bootstrap parameters (iteration count, percentile endpoints) are
config values. Switching to a different CI method would require a
methodology version bump and a regeneration pass. The 80% CI display
choice (10th/90th percentiles) is also configurable; 90% is the main
alternative if readers find the current interval too tight.
