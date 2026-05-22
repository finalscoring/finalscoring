# Methodology

How Final Scoring turns critic reviews into the numbers on game pages.

This document is the canonical version. The same content is published
on the live site at `/methodology` and changes there only when this
file changes.

## What we ingest

Final Scoring indexes critic and reviewer opinion about board games.
Sources include text reviews on dedicated outlets, blogs, editorial
roundups, and BoardGameGeek-hosted critic writing where the reviewer
has been individually added to our registry.

We do **not** ingest community ratings, marketplace comments, or
generic user reviews. Final Scoring's value is editorial — turning it
into a community rating mirror would undo what makes it useful.

## The critic registry

Every critic or outlet that contributes a review is listed in our
[critic registry][registry]. For each, we publish:

- Name and outlet.
- Medium (text, video, podcast).
- Language.
- Score format the critic uses.
- The **source tier** weight applied to their reviews.

We are deliberately broad rather than gatekeep — any source with a
clear editorial identity and an accessible feed of reviews can be
added. Tier weighting handles quality differentiation.

## Source tiers

Each critic is assigned one of three tiers, expressed as a numeric
weight:

| Tier | Weight | Meaning |
|------|--------|---------|
| 1.0  | Tier 1 | Established editorial outlet or reviewer with substantial track record. |
| 0.5  | Tier 2 | Active reviewer with a clear editorial identity but less reach or history. |
| 0.25 | Tier 3 | Newer or narrower sources; included for breadth, not relied on for aggregate weight. |

Tier assignments are editorial judgments. They are listed publicly in
the registry, in git, and reviewable. We change them rarely and
document any change in commit history.

## Per-review normalization

Each review's underlying signal is a 1–10 rating, either declared by
the critic or inferred from their text. We label which is which on
every review page — "Declared: 4/5" vs. "Inferred: 7/10". Inferred
ratings are produced by the extraction model following a [published
rubric][prompt].

The 1–10 rating is mapped linearly to a 0–100 base score (rating 1 →
5, rating 10 → 95) so all critics start on the same scale before
further adjustment.

## Per-critic adjustment

Critics differ in how generously they score. To compare them fairly,
we apply a z-score adjustment to each review:

1. Compute the critic's personal mean and standard deviation across
   all their ingested reviews.
2. Express each of their scores as a z-score against that personal
   distribution.
3. Map the z-score back onto the global score scale using the global
   mean and standard deviation.

This adjustment is applied only to critics with at least 15 ingested
reviews. Below that threshold, a critic's personal distribution is
too noisy to be a reliable reference, and their reviews are
normalized against the global distribution instead. The threshold is
a tunable constant in the scoring config.

## Per-game aggregation

For each game with at least 4 ingested reviews, we compute:

- A **weighted mean** of the normalized review scores, with weights
  given by the source tiers. This is the headline score displayed
  on the game page.
- A **bootstrap confidence interval** (percentile method, 2000
  resamples, 80% interval) reflecting both how few reviews exist and
  how much the critics disagree. The CI is displayed alongside the
  headline score.
- The **distribution** of normalized review scores, displayed as a
  histogram so readers can see whether a 75 came from uniform mild
  praise or from polarized reception.

Below the 4-review threshold, no aggregate is computed. The
individual reviews still list, with a clear "insufficient critical
coverage" label.

## Score bands

For browse and discovery, scores are grouped into bands:

| Band         | Score   |
|--------------|---------|
| Acclaimed    | 85+     |
| Recommended  | 70–84   |
| Mixed        | 50–69   |
| Criticised   | <50     |

These are display conventions, not separate calculations. The
underlying number remains the weighted aggregate above.

## Declared vs. inferred scores

When a critic gives a numeric score or a recognised verdict band
("Recommended", "Tier S"), we use it as the basis for the normalized
score and label the review as **declared**.

When a critic publishes opinion without an explicit score, the
extraction model produces an inferred 1–10 rating from the text. We
label these reviews as **inferred**. They are used in aggregates with
the same weight as declared reviews from the same critic, but the
distinction is preserved everywhere they appear.

## Reproducibility

Every component of this methodology is versioned:

- The [extraction prompt][prompt] is committed under a version tag.
- The [scoring config][config] (thresholds, weights, CI parameters)
  is committed under a version tag.
- Every `Review` row in the database carries the prompt+model
  version that produced it.
- Every `Aggregate` row carries the scoring config version that
  produced it.

A change to the methodology produces a new version tag and
regenerates aggregates under the new version. Older aggregates can be
recomputed against the new methodology, and the difference compared.

## Critic opt-out

Any critic listed in the registry can request opt-out and their entry
will be set to `opt_out=true`. From the next build, their reviews
will not be ingested or displayed. Reviews already in the database
are retained but excluded from public surfaces.

## Open questions and changes

Material changes to this methodology are documented in
`docs/decisions/`. If you spot something here that contradicts what
the code does, that's a bug — please report it.

[registry]: ../data/overrides/critics.csv
[prompt]: ../prompts/review_extraction/v1.md
[config]: ../src/final_scoring/scoring/config.py
