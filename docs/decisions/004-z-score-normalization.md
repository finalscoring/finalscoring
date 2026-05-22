# 004 — Per-critic z-score with sample-size threshold

**Status:** Accepted.
**Date:** 2026-05.

## Context

Critics differ systematically in how generously they score. A reviewer
who rates one game in a thousand a 10 gives more information when they
do so than a reviewer who rates many games at 9–10. Treating both
reviewers' nominal scores as equivalent in aggregation produces a
biased aggregate.

Z-score normalization against each critic's personal distribution
removes this bias cleanly. But it requires enough per-critic data to
estimate a personal mean and standard deviation reliably. A z-score
on three reviews is noise.

## Decision

The build applies z-score adjustment in two regimes:

1. **Critics with ≥15 ingested reviews.** Their reviews are normalized
   against their personal mean and standard deviation, then mapped back
   onto the global score scale.
2. **Critics with fewer than 15 reviews.** Their reviews are normalized
   against the global distribution (the same mean/stdev computed
   across all reviews from all critics).

The threshold (15) is a constant in `scoring.config.ScoringConfig`.
It is published on the methodology page so readers can see exactly
how each critic's scores are treated.

A zero-variance critic (every score identical, e.g. early in their
ingestion history) falls back to the global distribution as well —
their personal scale cannot be z-score-normalized meaningfully.

## Consequences

**Committed to:**
- The methodology page distinguishes the two regimes and links to the
  threshold value.
- The threshold is exposed as a tunable parameter; changing it
  produces a new methodology version and regenerates aggregates.

**Precluded:**
- A single uniform normalization scheme that ignores per-critic
  variance. We considered this and rejected it as inadequate to the
  brand promise of careful methodology.

## Reversibility

The threshold is a single integer in the scoring config. Changing it
is a config-level change that regenerates aggregates on the next
build. The two-regime structure could be replaced with a continuous
regularised estimator (e.g. shrinkage toward the global mean
proportional to sample size) in a future methodology version if
empirical evidence warrants.
