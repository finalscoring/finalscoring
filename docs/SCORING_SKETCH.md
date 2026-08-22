# Scoring Sketch — Algorithms and Reasoning

A sketch of the scoring layer's logic for Phase E. Algorithms and the
reasoning behind them; concrete parameters are deliberately left as open
TODOs because they are unconfirmed (see `DECISIONS_OPEN.md`). This is a
starting point so Phase E doesn't begin from a blank page — not a spec.

The scoring layer is pure functions over the review data: no I/O, highly
testable. Three stages.

## Stage 1 — Per-critic normalization

**Where the 0–100 scale comes from — not from here.** The extractor emits
a 1–10 `rating` on `ExtractedReview`, but `reviews.declared_score` and
`reviews.inferred_score` are already 0–100, so the conversion has to
happen in the load step (D2), before anything is persisted. Scoring reads
reviews that are already on the common scale. A linear map with a small
offset avoids the degenerate all-zeros corner (e.g. rating 1 → 5, rating
10 → 95). TODO (open): the exact mapping — and note that it is a D2
decision, not an E1 one.

**Which score to normalize.** A review may carry a declared score, an
inferred one, or both (`Review.score_is_inferred` distinguishes the
cases). Whether scoring prefers the declared value, treats the two
alike, or discounts inferred ones is not decided.

**Why per-critic normalization.** Critics differ systematically in
generosity. A reviewer who almost never gives top marks conveys more when
they do than a reviewer who scores everything highly. Comparing raw
scores across critics bakes in that bias.

**Approach: z-score against the critic's own distribution.**
1. Compute each critic's personal mean and standard deviation across
   their own reviews.
2. Express a given review as a z-score against that personal
   distribution.
3. Map the z-score back onto the global scale using the global mean and
   standard deviation, so the output stays on a human-readable 0–100 axis
   rather than as raw z-values.

**The small-sample problem.** A critic with very few reviews has a noisy
personal mean/stdev; normalizing against it adds more error than it
removes. So:
- Above a minimum-review threshold: use the critic's personal stats.
- Below it: fall back to the global distribution.
- A zero-variance critic (all identical scores) also falls back — there's
  no personal spread to normalize against.

TODO (open): the minimum-review threshold value; whether a hard
threshold or a smoother shrinkage-toward-global approach is preferred.
Clip outputs to 0–100 so extreme z-scores can't escape the range.

## Stage 2 — Per-game aggregation with source weights

**Minimum coverage.** A game needs at least N reviews before it gets an
aggregate at all; below that, show the individual reviews labelled as
insufficient coverage, no headline number. TODO (open): N (discussed
informally as ~4, not confirmed).

**Weighted mean.** Combine the normalized review scores with weights
given by source quality. This is where the agreed "broad crawl, weight by
quality" strategy is realised. TODO (open): the tier values and how
they're assigned, and which of the schema's two weight fields
(`critics.quality_weight`, `outlets.quality_weight`) a review's weight
comes from — see `DECISIONS_OPEN.md`. Only the *mechanism* (a per-review
weight applied in the mean) is agreed.

## Stage 3 — Confidence interval

**Why.** A bare aggregate hides whether critics agreed. The agreed
display is "score + interval" (e.g. "85, range 67–91"), so the interval
has to reflect both few-reviews uncertainty and critic disagreement.

**Approach: percentile bootstrap over the weighted mean.** Resample the
reviews with replacement (preserving weights), recompute the weighted
mean many times, take percentiles of the resulting distribution as the
interval. Bootstrap is chosen over a closed-form weighted standard error
because samples are small, weights are unequal, and the score
distribution isn't necessarily normal — bootstrap degrades gracefully
across all three without distributional assumptions.

**Properties any implementation should satisfy (good test targets):**
- Agreement among critics → narrow interval.
- Disagreement → wide interval.
- A single review → interval collapses cleanly to the point estimate
  (degenerate, but must not crash or produce nonsense).
- Reproducible: seed the resampler so the same inputs give the same
  interval across builds.

TODO (open): number of bootstrap iterations; which percentile endpoints
define the interval (e.g. 10th/90th for an 80% interval vs. a 90%
interval); the seed convention.

## Versioning note

Scoring parameters (thresholds, weights, CI settings) are part of the
methodology and should be a versioned artefact: stamp the version onto
each computed aggregate so a parameter change is an auditable, reviewable
diff and old aggregates can be recomputed and compared. The slot for that
stamp already exists: `game_aggregates.scoring_version`. The methodology
the public sees should be generated from the same source of truth, not
maintained separately.

## What is NOT decided

Everything marked TODO above, plus: whether normalization is the z-score
form sketched here or another comparable scheme; exact tier definitions;
the minimum-coverage and minimum-sample thresholds; and all CI
parameters. The *shape* (per-critic normalization → weighted aggregate →
CI) is agreed; the numbers are not. Settle them with the maintainer
before implementing Phase E.
