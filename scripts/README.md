# Scripts

Operational helpers that don't belong in the main `fs` CLI — usually
because they're one-shot, environment-specific, or destructive enough
to warrant living outside the normal command surface.

Conventions:

- Each script is self-contained and runnable as
  `python scripts/<name>.py`.
- Each script has a docstring at the top explaining what it does and
  when to use it.
- Anything that mutates `data/overrides/` or the database announces
  what it's about to do and asks for confirmation unless `--yes` is
  passed.

## Anticipated scripts (not yet written)

- `scripts/import_recommend_games.py` — pull a fresh game snapshot
  from a Recommend.Games export.
- `scripts/backfill_extraction.py` — re-run LLM extraction on
  historical JSONL with a new prompt version.
- `scripts/validate_overrides.py` — sanity-check that
  `data/overrides/*.csv` parses cleanly and references only known
  slugs / BGG IDs.
- `scripts/inspect_aggregate.py` — pretty-print the score breakdown
  for a single game to help debug surprising aggregates.
