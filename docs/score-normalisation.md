# Score normalisation

Defines how Final Scoring handles score normalisation.

Goal: make critic scores comparable across sources — explicit, conservative, traceable.

## Product principle

Normalisation aids comparison, not erases source truth.

Preserve original source score representations. Derive normalised numeric score only when justified mapping exists.

## Two values should usually be preserved

For scored reviews, keep both:

- original score representation: `8/10`, `4/5`, `B+`, `Recommended`
- derived normalised score, when defensible mapping exists

Different purposes:

- original score preserves source truth
- normalised score supports comparison and aggregation

## Preferred normalised scale

Default normalised scale: **0 to 100**.

### Rationale

- easy to understand
- compatible with familiar aggregator conventions
- easy to derive from common source scales
- flexible for later presentation choices

System may display differently in UI, but canonical stored comparable numeric scale = percentage-like.

## Straightforward deterministic mappings

Support these early.

### Ten-point scales

- `8/10` -> `80`
- `6.5/10` -> `65`

### Five-point scales

- `4/5` -> `80`
- `3.5/5` -> `70`

### Percentages

- `92%` -> `92`
- `75%` -> `75`

### Star ratings

When clearly out of five:

- `4 stars` -> `80`
- `3.5 stars` -> `70`

When clearly out of ten:

- `8 stars out of 10` -> `80`

Apply mappings only when source scale genuinely known.

## Source-specific mappings

Some score systems need source-specific handling:

- letter grades
- thumbs up / thumbs down
- recommendation badges
- publication-specific verdict vocabularies

Mappings must be explicit and documented, not silently inferred.

## Letter grades

Don't normalise letter grades until project-level mapping policy explicitly chosen and implemented.

### Rationale

Letter grades more culturally and publication-context dependent than numeric scales. Premature mapping = false precision.

If later supported, mapping must be:

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

Don't auto-convert to numeric scores during MVP unless clear documented policy adopted.

Keep as source truth, handle as verdict metadata — not silently converted to percentages.

## Scoreless reviews

Review valid even without numeric score.

In those cases:

- `original_score` may be null
- `normalised_score` should be null
- review still eligible for display on game page

Don't discard scoreless reviews solely for being unscored.

## Traceability requirements

Normalisation must be easy to inspect and debug.

Where practical, system should expose:

- raw score string extracted
- scale inferred
- mapping rule applied
- numeric value produced

Implement later in richer metadata if needed — but design must not hide transformation.

## Aggregation rules

MVP: only reviews with valid normalised numeric score contribute to numeric aggregates.

Scoreless reviews may still contribute to:

- review counts shown separately
- page completeness
- qualitative presentation on game pages

Don't quietly treat as numeric data.

## Precision and rounding

Preserve enough precision internally to avoid distortion.

Suggested default:

- store normalised scores as numeric values with decimals
- decide UI rounding separately

`3.5/5` stored as `70.0`; UI decides whether to show `70` or `70.0`.

## Conservative rule

When in doubt, don't normalise.

Better to leave score unnormalised than apply misleading conversion with false confidence.

## Early implementation recommendation

MVP support:

- x/10
- x/5
- percentages
- obvious star systems when denominator known

Defer:

- letter grades
- recommendation verdicts as numeric mappings
- publication-specific judgement systems without documented policy

## Open questions for later

- should verdict-only reviews influence non-numeric browse surfaces?
- how should letter grades be mapped, if at all?
- should source-specific weighting alter contribution of normalised score?
- should UI expose confidence or provenance of mapping?