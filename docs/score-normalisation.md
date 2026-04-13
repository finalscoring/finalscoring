# Score normalisation

This document defines how Final Scoring should think about score normalisation.

The goal is to make critic scores more comparable across sources while remaining explicit, conservative, and traceable.

## Product principle

Normalisation exists to aid comparison, not to erase source truth.

The system should preserve original source score representations where possible and derive a normalised numeric score only when there is a justified mapping.

## Two values should usually be preserved

For scored reviews, the system should keep both:

- the original score representation, such as `8/10`, `4/5`, `B+`, or `Recommended`
- the derived normalised score, when a defensible mapping exists

These serve different purposes:

- original score preserves source truth
- normalised score supports comparison and aggregation

## Preferred normalised scale

The default normalised scale should be **0 to 100**.

### Rationale

- easy to understand
- compatible with familiar aggregator conventions
- easy to derive from common source scales
- flexible enough for later presentation choices

The system may later display that value differently in the UI, but the canonical stored comparable numeric scale should be percentage-like.

## Straightforward deterministic mappings

These should be supported early.

### Ten-point scales

Examples:

- `8/10` -> `80`
- `6.5/10` -> `65`

### Five-point scales

Examples:

- `4/5` -> `80`
- `3.5/5` -> `70`

### Percentages

Examples:

- `92%` -> `92`
- `75%` -> `75`

### Star ratings

When clearly out of five:

- `4 stars` -> `80`
- `3.5 stars` -> `70`

When clearly out of ten:

- `8 stars out of 10` -> `80`

Mappings should only be applied when the source scale is genuinely known.

## Source-specific mappings

Some score systems may require source-specific handling.

Examples:

- letter grades
- thumbs up / thumbs down systems
- recommendation badges
- publication-specific verdict vocabularies

These mappings should be explicit and documented, not inferred silently in many places.

## Letter grades

Letter grades should not be normalised until a project-level mapping policy is explicitly chosen and implemented.

### Rationale

Letter grades are more culturally and publication-context dependent than simple numeric scales. Prematurely pretending they map cleanly to a percentage would create false precision.

If letter grades are later supported, the mapping should be:

- explicit
- centrally defined
- documented
- ideally source-aware

## Recommendation-style verdicts

Verdicts like:

- `Recommended`
- `Highly recommended`
- `Avoid`
- `Buy`
- `Pass`

should not automatically become numeric scores during MVP unless a clear and documented policy is adopted.

Instead, these should remain as source truth and be handled as verdict metadata rather than silently converted into percentages.

## Scoreless reviews

A review can still be a valid review even if it has no numeric score.

In those cases:

- `original_score` may be null
- `normalised_score` should be null
- the review should still remain eligible for display on the game page

Scoreless reviews should not be discarded solely because they are unscored.

## Traceability requirements

Normalisation should be easy to inspect and debug.

Where practical, the system should make it possible to determine:

- what raw score string was extracted
- what scale was inferred
- what mapping rule was applied
- what numeric value was produced

This can be implemented later in richer metadata structures if needed, but the design should not hide the transformation.

## Aggregation rules

For MVP, only reviews with a valid normalised numeric score should contribute to numeric aggregate scores.

Scoreless reviews may still contribute to:

- review counts shown separately if desired
- page completeness
- qualitative presentation on game pages

But they should not be quietly treated as numeric data.

## Precision and rounding

The system should preserve enough precision internally to avoid unnecessary distortion.

Suggested default:

- store normalised scores as numeric values that may include decimals
- decide on UI rounding separately

For example, a source score of `3.5/5` may be stored as `70.0`, while UI display could later choose whether to show `70` or `70.0`.

## Conservative rule

When in doubt, do not normalise.

It is better to leave a score unnormalised than to apply a misleading conversion with false confidence.

## Early implementation recommendation

For MVP, support:

- x/10
- x/5
- percentages
- obvious star systems when the denominator is known

Defer:

- letter grades
- recommendation verdicts as numeric mappings
- publication-specific judgement systems without a documented policy

## Open questions for later

- should verdict-only reviews influence non-numeric browse surfaces?
- how should letter grades be mapped, if at all?
- should source-specific weighting ever alter the contribution of a normalised score?
- should the UI expose confidence or provenance of a mapping?
