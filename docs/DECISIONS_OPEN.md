# Final Scoring — Open Decisions

These were discussed but have NOT been decided by the maintainer. An
agent must NOT pick any of these unilaterally. Surface the options and
let the maintainer choose. This list is the boundary between "agreed"
(see `PROJECT.md`) and "still open".

## Loading reviews

*The `ExtractedReview` → `Review` mapping, `raw_score`/`rating` routing,
and the dedupe key + which-one-wins rule are now decided — see
`PROJECT.md`, "`ExtractedReview` → `Review` load mapping (D2)".*

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

*Data access for D1 (title → BGG id resolution) is now decided — see
`PROJECT.md`, "Game data access (D1)". The matching logic itself still
needs to be built.*

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
- A narrower variant of the above: some critics who write prose-only
  reviews (no stated score) also rate on BGG under a known username and
  link back to their own review from the comment. Verified for Dan
  Thurot / space-biff — BGG user `the innocent` has 1755 ratings, many
  with a comment containing the review's exact URL, e.g. "Read my review
  here: http://spacebiff.com/2015/10/06/samurai/". This is not a new
  critic, unlike the item above — it is a possible source for
  `raw_score` on a critic already ingested via their own outlet, for the
  reviews where prose alone gives the extractor no number. Needs no new
  scraping: Recommend.Games' `board-game-data/scraped/bgg_RatingItem.jl`
  already carries `bgg_user_name`, `bgg_user_rating`, and `comment` per
  rating. Not decided: whether to build this at all; whether the match
  key is the review URL found in the comment (highest confidence) or
  something looser; where `bgg_username` lives (a field on `critics`, or
  per-source config); and how a miss should degrade — presumably to
  leaving `declared_score` unset rather than discarding the review.

## LLM specifics

- Specific local model, serving stack (e.g. vLLM, Ollama, llama.cpp),
  and structured-output/constrained-decoding mechanism are not decided.
  The first real run used `qwen3:30b` on Ollama — the Qwen3-30B **A3B**
  mixture-of-experts, 3B active parameters — and the output showed the
  cost: 14 of 48 quotes were non-verbatim (paraphrase, splice, mid-word
  truncation, one fragment leaking Chinese); a `published_at` supplied by
  a `<review>` block was dropped on most hall9000 reviews; and a
  `year_published` and publisher were confabulated where the source
  stated neither. Candidates to evaluate against it, all ~15–20 GB at
  4-bit and in the Ollama library: **Gemma 3 27B** (broad multilingual,
  no thinking mode), **Qwen3-32B** (the dense model, far more active
  compute, prompt unchanged), **Mistral Small 3.2** (Apache-2.0, tuned
  for instruction adherence). Evaluate by re-running extraction on a
  fixed set of raw items and scoring the verbatim-quote pass rate and
  whether `<review>`-block facts carry through — see `LLM_SETUP.md`,
  "Comparing models". Also open: whether to prefer a serving stack with
  token-level constrained decoding (vLLM, llama.cpp grammar) over
  Ollama's schema-as-hint.
- Whether any step ever calls a hosted endpoint instead of local is not
  decided. It is possible in principle — the client is already a plain
  OpenAI-compatible one, so Anthropic, OpenAI and Google (via their
  OpenAI-compatible endpoints) need only `FS_LLM_BASE_URL`, a real
  `FS_LLM_API_KEY` from an environment secret, and `FS_LLM_MODEL` set to
  their model name. The blockers are policy, not code: review text and
  quotes would leave the machine (the "no review text leaves the
  machine" line in `LLM_SETUP.md` would no longer hold), the provider's
  terms would need checking against the copyright analysis in
  `QUOTATION_POLICY.md`, and a hosted model still has to pass the same
  quote-fidelity and fact-carry checks before it is trusted. Cost is
  small either way: ~5k input plus ~1k output tokens per page, so a
  weekly incremental run of a few hundred pages is cents on a cheap
  hosted model (Gemini Flash, GPT mini class, Claude Haiku) and a euro
  or two on a frontier one; a one-time full backfill of ~10k pages is
  under €50 on the cheap tier and roughly €100–350 on a frontier model,
  less with prompt caching of the static system prompt.

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
