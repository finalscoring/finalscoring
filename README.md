# Final Scoring

A critic-focused review aggregation index for board games.

Final Scoring collects, organises and summarises critical opinion from board
game reviewers, critics and media sources, giving readers a clear sense of
how a game has been received critically. It is deliberately distinct from
community rating sites, recommendation engines, and social platforms.

**Status:** pre-launch. Domain reserved at <https://finalscoring.games/>.

## Mantras

These are binding constraints, not aspirations. See [`MANTRAS.md`](MANTRAS.md).

- No tracking, ever.
- 100% open source, full transparency.
- Single-minded focus on the mission: board game review aggregation.

## What this is

A read-mostly publication of critical reception, built weekly from a
SQLite snapshot. Every game page shows:

- A single 0–100 weighted score with a confidence interval reflecting how
  much critics agree.
- The distribution of underlying reviews.
- Each individual review with attribution, a short verbatim pull-quote, an
  outbound link to the original, and clear labelling of whether the score
  is declared by the critic or inferred from their text.

## What this is not

- Not a community rating site. No user accounts, no ratings, no comments.
- Not a recommendation engine. Browse and filter, but no "games like this".
- Not a database. Game metadata is imported from
  [Recommend.Games](https://recommend.games/); Final Scoring's contribution
  is the critical layer on top.

See [`docs/scope.md`](docs/scope.md) for the full out-of-scope list.

## Architecture in one paragraph

Python + Scrapy ingest reviews from a curated registry of critic sources.
A local open-weights LLM (via an OpenAI-compatible endpoint) extracts
structured review records. Game-title resolution uses Recommend.Games
matching infrastructure. Per-critic z-score normalization, source-tier
weighting, and bootstrap confidence intervals are computed at build time.
The result is baked into a SQLite database, shipped inside a Docker image,
and served by a static-ish frontend. Builds run weekly. There is no live
database in production — every deploy is an atomic, fully self-contained
image. See [`docs/architecture.md`](docs/architecture.md).

## Repository layout

```
src/final_scoring/      Python package (schema, scraping, pipeline, scoring, build, CLI)
prompts/                Versioned LLM prompts (treated as code)
frontend/               Web UI (TBD — placeholder for now)
scripts/                Operational scripts (backfills, manual matching, etc.)
data/                   Override tables, scraper job state, build results
tests/                  Unit and integration tests
docs/                   Architecture, methodology, scope, decisions
.github/workflows/      CI and scheduled rebuilds
```

## Quickstart (development)

```bash
# 1. Install in editable mode with dev extras
pip install -e ".[dev]"

# 2. Copy and edit env
cp .env.example .env
# Edit .env to point LLM_API_BASE_URL at your local model server.

# 3. Materialize an empty SQLite schema
fs db init --path data/final_scoring.db

# 4. Run a single spider end-to-end against the existing test fixtures
fs scrape sdj --limit 5

# 5. Run the full build (ingest → extract → score → bake)
fs build
```

See [`docs/development.md`](docs/development.md) for more.

## License

[AGPLv3](LICENSE). This applies to all code, prompts, and methodology
documents in this repository. Anyone running a modified version of Final
Scoring as a network service must publish their modifications under the
same terms. This is deliberate — the project's transparency mantra
applies to derivatives, not just to this codebase.

## Acknowledgements

Final Scoring builds on infrastructure and ideas from
[Recommend.Games](https://recommend.games/), in particular game-matching
against [BoardGameGeek](https://boardgamegeek.com/) and the
Spiel-des-Jahres review scraping pipeline that the ingestion layer here
descends from.
