# Final Scoring — Open Decisions

These were discussed but have NOT been decided by the maintainer. An
agent must NOT pick any of these unilaterally. Surface the options and
let the maintainer choose. This list is the boundary between "agreed"
(see `PROJECT.md`) and "still open".

## Data layer

- ORM / data-access choice for the SQLite schema (e.g. SQLAlchemy,
  SQLModel, raw sqlite3 + dataclasses/attrs, or other). Not decided.
- Concrete schema: table set, field names, types, constraints, keys.
  Nothing here is decided. The data model is explicitly the
  maintainer's call.
- Which entity to build first (e.g. the imported game record vs. the
  review record). Not decided.

## Recommend.Games integration

- Whether to reuse Recommend.Games data and/or infrastructure at all, or
  build equivalent capabilities independently, is not decided.
- The source of BGG-matching / game-identity infrastructure for Final
  Scoring is not decided. No matching mechanism currently exists in this
  repo; one must either be built or sourced.
- The integration mechanism itself is not decided. Options discussed but
  not chosen: shared database, periodic import/snapshot, shared
  library/internal API, or building it into the SQLite bake step. No
  choice has been made.

## Scoring methodology details

- Score normalization is agreed in principle (per-critic z-score
  approach). NOT decided: minimum review counts/thresholds, how
  unscored/verbal reviews map to numbers, the exact weighting scheme for
  source quality, and how the confidence interval is computed.
- Source quality tiers/weights: the broad-crawl-with-weighting strategy
  is agreed, but the actual tier definitions, values, and assignment
  process are not decided.

## Sources

- The initial list of critics/sources to ingest is not decided.
- Which source to implement first (beyond the existing SdJ
  proof-of-concept) is not decided.
- Whether/how to treat BGG user comments: discussed only as "a subset of
  high-quality BGG users could be added as critics by explicit editorial
  decision". This was not confirmed as a decision.

## LLM specifics

- Specific local model, serving stack (e.g. vLLM, Ollama, llama.cpp),
  and structured-output/constrained-decoding mechanism are not decided.
- Whether any step ever calls a hosted endpoint instead of local is not
  decided.

## Frontend

- Entire frontend stack is undecided and deferred. Nothing about the
  current placeholder site is committed.

## Product surfaces

- Page structure (game page, critic page, browse/search, homepage) was
  discussed at a high level but no specific layout, content, or feature
  set has been decided.
- Score bands vs. raw number for browse/discovery: a single 0–100 score
  with CI is agreed for display, but band cutoffs and their use are not
  decided.

## Editorial policy

- Critic opt-out policy, handling of objections to scores, and the
  declared-vs-inferred score labelling were raised as things to decide
  before public launch. None are decided.

## Deferred features (named, not scheduled)

Discussed as possible future work, explicitly NOT in current scope and
NOT decided as committed roadmap items:

- Themed "consensus summary" synthesis feature.
- Video and podcast ingestion (transcription).
- Critic-impact-derived weighting.
- Languages beyond German and English.
