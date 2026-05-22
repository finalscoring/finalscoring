# Override tables

This directory holds the editorial source-of-truth for things Final
Scoring cannot derive automatically:

- **`critics.csv`** — the curated critic registry. Every reviewer or
  outlet that should appear in Final Scoring has a row here. Columns:
  `slug, name, outlet, medium, language, homepage_url, feed_url,
  score_format, source_tier, opt_out, notes`. Loaded into the `critic`
  table at the start of every build.
- **`critic_aliases.csv`** — alternative names the LLM might produce
  for a given critic, mapped to canonical `slug`. Loaded into the
  `criticalias` table. Add a row whenever you spot the LLM producing
  a new variant.
- **`game_matches.csv`** — manual title-to-BGG-ID overrides for cases
  where the automatic matcher gets it wrong. Loaded into the
  `gamematchoverride` table.

All three files are checked into the repository — the mantras commit
Final Scoring to publishing exactly which critics it includes and how
they're weighted.

## Adding a new critic

1. Add a row to `critics.csv`.
2. If a spider doesn't already exist for the source, write one under
   `src/final_scoring/scraping/spiders/`.
3. Run `fs scrape <slug> --limit 10` and check the JSONL output.
4. Iterate on the spider until the extraction looks right.
5. Add the spider to `_discover_spiders()` in
   `src/final_scoring/cli/app.py` so `fs scrape <slug>` works.
6. Commit. Next weekly build will pick up the new source.

## Editing tier weights

Allowed values are `1.0`, `0.5`, `0.25`. The build fails if any critic
row has a different value (see `scoring.config.ScoringConfig.valid_tiers`).
Editing a tier in `critics.csv` is enough — the next build will use the
new weight for all reviews from that critic.

## Opting a critic out

Set `opt_out=true` in `critics.csv`. The build will skip ingestion for
that source and exclude any existing reviews from the public site. The
data itself is retained — flip back to `false` to restore.
