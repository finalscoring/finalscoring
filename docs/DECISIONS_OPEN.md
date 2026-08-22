# Final Scoring — Open Decisions

These were discussed but have NOT been decided by the maintainer. An
agent must NOT pick any of these unilaterally. Surface the options and
let the maintainer choose. This list is the boundary between "agreed"
(see `PROJECT.md`) and "still open".

## Ingestion artifacts

- JSON Lines is the agreed intermediate format, but the stream layout is
  not decided: whether the extraction step re-emits enriched `RawItem`
  records as a single stream, or writes `ExtractedReview` records to a
  stream of their own. The load step has to read whichever it is, so
  settle this before D2.
- The filename convention for those files, and the setting that
  configures it, are not decided. No code sets either today.
- Nothing records which prompt and model produced an extracted review.
  Prompts are versioned files (`scraping/prompts/`), but no record
  carries the version that generated it, so re-running under a new prompt
  is not auditable — see `SDJ_PIPELINE_NOTES.md` gap #9. Whether the
  stamp belongs on the extracted record, on the persisted review, or in
  per-run metadata is not decided. Settle before C3, where the values
  first exist.

## Recommend.Games integration

- Recommend.Games has comprehensive BGG game data that Final Scoring
  will need for title → BGG id resolution. The matching logic itself
  must be built here; the open question is how to access the R.G. game
  data. Options discussed but not chosen: shared database, periodic
  import/snapshot, shared library/internal API, or building it into the
  SQLite bake step. No choice has been made.

## Scoring methodology details

- Score normalization is agreed in principle (per-critic z-score
  approach). NOT decided: minimum review counts/thresholds, how
  unscored/verbal reviews map to numbers, the exact weighting scheme for
  source quality, and how the confidence interval is computed.
- Source quality tiers/weights: the broad-crawl-with-weighting strategy
  is agreed, but the actual tier definitions, values, and assignment
  process are not decided.
- The schema carries two weights — `critics.quality_weight` and
  `outlets.quality_weight` — and how they combine into the weight a
  single review actually gets is not decided: critic only, outlet only,
  their product, or outlet as the fallback when the critic is unknown
  (`reviews.critic_id` is nullable, so that case is real).
  `SCORING_SKETCH.md` assumes one per-critic weight; the schema offers
  two. Settle before E2.

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
