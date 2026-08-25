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
- Nothing records which prompt and model produced an extracted review.
  Prompts are versioned files (`scraping/prompts/`), but no record
  carries the version that generated it, so re-running under a new prompt
  is not auditable — see `SDJ_PIPELINE_NOTES.md` gap #9. Whether the
  stamp belongs on the extracted record, on the persisted review, or in
  per-run metadata is not decided. Settle before C3, where the values
  first exist.

## Loading reviews

- How an `ExtractedReview` becomes a `Review` is not decided. The
  extractor emits `rating` (1–10, the model's read of the verdict) and
  `raw_score` (the score verbatim, e.g. "4/5", "sehr gut"); the table
  stores `declared_score` and `inferred_score`, both 0–100. The intended
  routing is `raw_score` → declared and `rating` → inferred, but nothing
  states it and nothing implements it.
- Parsing `raw_score` needs the critic's native scale, which is not
  always in the string. "4/5" carries it, "4 Sterne" does not, and "sehr
  gut" carries none at all. Whether that scale lives on the outlet, is
  inferred per review, or makes the score unusable is not decided.
- **There is no uniqueness rule on `reviews` at all.** `url unique` was
  the only one and it was wrong — one scraped page yields many reviews —
  so it was removed. The replacement is an upsert on
  `(critic_id, game_bgg_id)` in D2, but neither the key nor the
  which-one-wins rule is decided. Options discussed: prefer a direct
  source over a meta-source, prefer a declared score over an inferred
  one, take the most recent, or keep every row and resolve at scoring
  time. Note `critic_id` is nullable, so unresolved critics need a
  fallback and must not be merged silently. This matters more than it
  looks: one critic counted twice moves a game's aggregate *and* pads
  that critic's own distribution, skewing their normalization. See
  `SDJ_PIPELINE_NOTES.md` gap #7. Settle before D2.
- Translated quotes are not handled. When a German roundup cites an
  English-language critic, the jury renders their words in German, so
  the "verbatim" quote is a translation attributed to that critic —
  which `QUOTATION_POLICY.md` requires be copied exactly, and which
  misrepresents them further than a paraphrase would. Whether extraction
  should flag such a quote, store it labelled, or drop it is not
  decided. The footnote links the SdJ spider will carry are a better
  signal than asking the model to guess, so settle this once they exist
  and before C3 writes a corpus.
- `medium` now exists on both `outlets` and `reviews`, and which is
  authoritative is not decided — an outlet spans several media, so the
  per-review value is the more precise one, but the outlet value is what
  a quality tier would attach to. Structurally the same question as the
  two `quality_weight` fields below.

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
