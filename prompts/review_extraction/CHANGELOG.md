# Review extraction — changelog

Versions are loaded by `final_scoring.pipeline.prompts.load_prompt`.
Each version is immutable once committed — edits go in a new version
file so the `extraction_model_version` field on every `Review` row
remains a stable provenance pointer.

## v1 — initial

Initial extraction prompt for Final Scoring. Extended from the
proof-of-concept prompt used in the Spiel-des-Jahres scraper with:

- `outlet`, `original_url`, `original_date` fields for attribution when
  ingesting via meta-sources.
- `language` (ISO 639-1) for multilingual operation.
- Strict separation of `score_declared` (what the critic actually said,
  nullable) from `rating_inferred` (derived 1–10, always populated).
- `quote_verbatim` field with a hard 15-word limit, with explicit
  instructions to set to null rather than paraphrase or truncate.
