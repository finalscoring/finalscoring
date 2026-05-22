# SdJ Pipeline Notes — Reference Analysis

Notes on the existing proof-of-concept review spider and LLM extraction
pipeline (from the Spiel-des-Jahres project), read against what Final
Scoring needs. This is reference material for Phase C, not a porting
guide. The PoC is good and the architecture is right; the points below
are gaps to close when rebuilding deliberately, not criticisms.

## What the PoC gets right (keep these ideas)

- Scrapy `SitemapSpider` driven by `sitemap_rules` — clean, resumable
  discovery. JOBDIR resume is already wired.
- Structured-output extraction via the OpenAI-compatible client with a
  Pydantic `text_format` (`ReviewList`). This is the right pattern;
  don't go back to parsing free text.
- Configurable `base_url` so the same code points at a local model or a
  hosted endpoint — matches the agreed local-LLM decision.
- Tenacity retries with exponential backoff on the LLM call.
- Token accounting into Scrapy stats.
- Batched JSON Lines output — matches the Recommend.Games build pattern.
- A 1–10 rubric in the prompt to derive a rating when no score is given.

## What this source actually is (important framing)

The spider targets `kritikenrundschau-*` pages — the SdJ jury's
editorial *roundups*, which cite many critics. So one scraped page maps
to many reviews, and the cited critic — not the roundup author — is the
real reviewer. In Final Scoring terms this is a **meta-source**: useful,
but the provenance model has to record that a review came in via the
roundup, with the original critic and (where available) the original
review URL preserved. The PoC does not yet capture that distinction.

## Gaps to close for Final Scoring

### 1. Declared vs. inferred score are conflated
The PoC `Review` has `score` (the stated score, nullable) and `rating`
(always a derived 1–10). That's the right raw material, but Final
Scoring needs the distinction to be explicit and preserved end-to-end:
what the critic *declared* vs. what was *inferred* from text. Reviews
must be labelled as such everywhere they surface. Keep both fields, name
them unambiguously, and never let the inferred rating masquerade as a
declared score.

### 2. No provenance back to the original review
The PoC keeps the scraped page `url` but, for a meta-source, that's the
roundup — not the critic's own review. Final Scoring needs, per review:
the original review URL (when the roundup links/cites it), the original
publication date (distinct from the roundup's date), and the outlet.
None of these are in the PoC schema. The roundup text usually contains
them; the prompt should extract them.

### 3. No verbatim quote field
The PoC has a model-written `summary` only. Final Scoring wants a short,
attributed, verbatim pull-quote *in addition to* the paraphrase — and
for copyright safety the quote must be hard-capped (cap at the schema
level, e.g. a max length, so it can't depend on the model or a human
remembering to be brief). Confirm the exact cap with the maintainer.

### 4. `reviewer_id` is LLM-generated and will drift
The PoC asks the model for a snake_case `reviewer_id`. Across runs the
same person will come back as `tom_brewster` / `thomas_brewster` / etc.
Final Scoring needs a canonical critic identity resolved against a
registry, with an alias-mapping step. Treat the model's `reviewer_id` as
a hint, never the key.

### 5. `game_title` is a free string
Expected at the PoC stage. Final Scoring resolves titles to BGG ids
(via Recommend.Games), with a manual override path for misses. That's a
separate resolution step downstream, not a spider concern — just noting
the title stays a string until then.

### 6. No language field
The PoC is implicitly German. Final Scoring is multilingual from the
start, so every extracted review needs an explicit language code,
identified from the text rather than assumed from the source.

### 7. No dedupe key for (critic, game)
The same critic may be covered in multiple roundups. The load step needs
an upsert key and a "which wins" rule (e.g. most recent, or merge). Not a
spider concern, but the schema and load step must account for it.

### 8. Config is read ad hoc from env / Scrapy settings
The PoC reads `os.getenv(...)` in `custom_settings` and pulls LLM config
out of Scrapy settings. Fine for a PoC; Final Scoring has an agreed
central config object (Phase A2) those values should flow through, so
there's one place that defines and validates them.

### 9. Prompt is an inline string constant
`LLM_INSTRUCTIONS` lives in the module. Final Scoring should keep prompts
as versioned files and stamp the prompt+model version onto each extracted
review, so a later re-run with a new prompt is auditable. (Reproducibility
matters more here than in the PoC because scores are the product.)

## Net

The PoC retires most of the *engineering* risk for ingestion — the hard
parts (sitemap crawl, structured extraction, retries, JSONL output) work.
The Final Scoring rebuild is mostly about a richer record (provenance,
declared-vs-inferred, verbatim quote, language) and canonical identity
resolution (critic registry + aliases, BGG matching). Build it fresh
with these in mind rather than porting the PoC and patching.
