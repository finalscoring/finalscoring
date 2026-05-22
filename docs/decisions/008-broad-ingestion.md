# 008 — Broad ingestion with tier weighting

**Status:** Accepted.
**Date:** 2026-05.

## Context

Two curation models were considered:

1. **Tightly curated** (~15 critics at launch, individually vetted,
   slow to add new sources). Easier editorial workload, less risk of
   low-quality sources dragging the aggregate, but narrower coverage
   and harder to defend the "credible international index" framing
   with few sources.
2. **Broad with weights** (ingest as many sources as can be identified,
   assign each a tier weight, let weights handle quality). More
   sources means better coverage and more credibility for the
   aggregate, but raises the weighting question to v1-critical and
   means more editorial work to assign tiers.

For a credibility-focused aggregator with multilingual ambitions, the
broader strategy gives a stronger v1 product. The risk it creates —
that the weighting math has to launch with the product, not be
deferred to v2 — is acceptable because the weighting scheme is
deliberately simple (three tiers, manually assigned).

## Decision

Final Scoring ingests broadly: any source with a clear editorial
identity and an accessible feed is a candidate. Each critic in the
registry is assigned one of three tier weights (1.0, 0.5, 0.25).
Per-critic z-score normalization handles per-reviewer bias (ADR 004);
tier weights handle source-quality differentiation.

Tier assignments are editorial judgments. They live in
`data/overrides/critics.csv`, in version control, and are reviewable.

## Consequences

**Committed to:**
- A weighting policy must be documented on the methodology page from
  v1 — not deferred.
- Tier assignments are public and debatable. We accept that some
  critics may disagree with their tier; the policy is to discuss
  publicly and adjust transparently or not at all.
- Adding a new source is a low-friction operation (CSV row + spider
  + register), so the registry can grow organically.

**Precluded:**
- The more sophisticated "critic impact weighting" approach (deriving
  weights from downstream signals like BGG community uptake or
  SU&SD-effect-style causal analysis) is v3, not v1. The data
  required does not exist yet, and the methodology would be
  controversial to launch with.

## Reversibility

The tier system is deliberately simple to keep the migration to a
more sophisticated weighting scheme cheap. When v3 introduces
impact-derived weights, the tier values become a starting prior that
gets refined by data, not a structure that needs replacing.
