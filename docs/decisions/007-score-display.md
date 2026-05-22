# 007 — Single 0–100 score with confidence interval

**Status:** Accepted.
**Date:** 2026-05.

## Context

Three display models were considered:

1. **Single 0–100 number** (Metacritic style). Legible at a glance but
   invites the exact controversies Metacritic gets — readers fixate on
   the number, publishers push back on low scores, and the disagreement
   structure underneath the average is invisible.
2. **Score bands only** (Acclaimed / Recommended / Mixed / Criticised).
   Lower-resolution, harder to gameify, but loses information that
   readers genuinely use ("which acclaimed game is most acclaimed?").
3. **Distribution-first, no headline number.** Honest but illegible.
   Few readers parse a histogram cold.

A fourth hybrid emerged in conversation: a headline number paired with
a confidence interval reflecting reviewer agreement. "85, range 67–91"
carries strictly more information than "85" alone — it tells the
reader whether the critics agreed or disagreed.

## Decision

Game pages display a single 0–100 weighted aggregate score as the
headline, accompanied by a confidence interval ("85, range 67–91").
The distribution histogram is shown alongside as supporting detail.

Score bands (Acclaimed / Recommended / Mixed / Criticised) are used
for browse and discovery surfaces, derived deterministically from the
0–100 value. Band cutoffs are config constants.

## Consequences

**Committed to:**
- A confidence interval is computed for every published aggregate
  (see ADR 005).
- The UI design treats the CI as a first-class element, not a small
  footnote. Hiding it in tooltips would undermine the choice.
- The score bands are public, in config, and reviewable. Editorial
  judgement does not move games between bands; the number does.

**Precluded:**
- Showing a score below the 4-review threshold. Those games list
  their individual reviews with a "insufficient critical coverage"
  label and no aggregate.
- Manual editorial overrides on score display ("this game is
  acclaimed regardless of the number"). The number is the answer.

## Reversibility

The display choice can be revisited without touching the data layer
— the same `Aggregate` row supports any of the three display models
above. If we conclude the bare number is doing more harm than good,
we can switch to distribution-first without a schema change.
