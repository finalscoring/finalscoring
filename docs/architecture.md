# Architecture

This document explains *why* Final Scoring is built the way it is.
For *what* it does, see the top-level README and `MANTRAS.md`.

## One-line summary

A read-mostly publication of critical reception, built weekly from a
SQLite snapshot baked into a Docker image. No live database in
production.

## Data flow

```
[ Recommend.Games game data ]      [ Critic source registry ]
              │                              │
              ▼                              ▼
        ┌─────────────────┐         ┌──────────────────┐
        │  Game import    │         │  Per-source      │
        │  (build step)   │         │  Scrapy spiders  │
        └────────┬────────┘         └─────────┬────────┘
                 │                            │
                 │                            ▼
                 │                  ┌──────────────────┐
                 │                  │  LLM extraction  │
                 │                  │  (Pydantic-      │
                 │                  │   structured)    │
                 │                  └─────────┬────────┘
                 │                            │
                 │                            ▼
                 │                  [ Versioned JSONL ]
                 │                            │
                 ▼                            ▼
        ┌────────────────────────────────────────────┐
        │           Build orchestrator               │
        │  ─ schema init                             │
        │  ─ load critics + override tables          │
        │  ─ resolve game titles, dedupe reviews     │
        │  ─ per-critic z-score normalization        │
        │  ─ tier-weighted aggregation + bootstrap CI│
        │  ─ vacuum                                  │
        └─────────────────────┬──────────────────────┘
                              │
                              ▼
                  [ final_scoring.db (SQLite) ]
                              │
                              ▼
                  [ Docker image with DB baked in ]
                              │
                              ▼
                          Production
```

## Why SQLite + bake-into-image

Final Scoring's workload is read-mostly: critics publish on the order
of days to weeks, readers want fast game pages. There is no live
writer in production — ingestion runs in CI or on a build host, and
the result is shipped as an image.

This profile maps to SQLite in read-only mode almost ideally:

- **Reads are faster than Postgres**, since there's no network hop and
  no connection pool. The whole database can be memory-mapped.
- **Deploys are atomic**. Every build is a new image; rollback is
  just running the previous image. No migration scripts, no
  "what state is production in" anxiety.
- **Backups are free**: every image is a snapshot.
- **The transparency mantra is easier to keep**: "here's the image,
  it contains everything you need" is a stronger claim than "here's
  the code, now wire up Postgres."
- **Costs are minimal**: a tiny container, hostable anywhere.

The pattern carries forward from Recommend.Games, which has run this
way for nearly a decade.

## Why a monorepo

For a one-person project, the cost of splitting components into
separate repositories — internal versioning, coordinated PRs, separate
CI pipelines — dramatically outweighs any benefit. Final Scoring lives
as one repository with:

- one Python package under `src/final_scoring/`,
- one frontend project under `frontend/`,
- one Docker image build that combines them.

The internal module boundaries (`schema`, `scraping`, `pipeline`,
`scoring`, `build`, `cli`) are enforced by convention, not by tooling.

## Why local open-weights LLM

The extraction workload is batch ingestion of public text — no
latency requirements, no privacy concerns. With constrained-decoding
support in modern open-weights tooling (vLLM `guided_json`, Ollama
schema constraints, llama.cpp GBNF), a 14–32B local model produces
schema-valid output reliably enough for production use. A single
24GB-VRAM GPU on the build host suffices; in production the model is
not needed at all.

This is reversible — the extraction layer talks to any
OpenAI-compatible endpoint, so a hosted provider can be swapped in via
config without code changes if local quality ever proves insufficient.

## Why per-critic z-score normalization with a fallback

A critic who rates one game in a thousand a 10 gives more information
when they do so than a critic who scores generously. Z-score
adjustment puts both critics' scores on a comparable scale.

But a critic with only a handful of ingested reviews has a noisy
personal distribution. Applying personal z-scores there introduces
*more* error than it removes. The compromise: critics get personal
z-score adjustment only above a minimum review threshold (see
`scoring.config.ScoringConfig.min_reviews_for_z_score`); below it,
they're normalized against the global distribution. This is
documented in the public methodology page so readers can see exactly
how each critic's scores are treated.

## Why bootstrap confidence intervals

Most critic-aggregator sites display a single number, which makes
disagreement invisible. Final Scoring displays both a point estimate
and a confidence interval: "85, range 67–91" tells the reader the
critics disagree more than "85, range 82–87" does.

The CI is computed by percentile bootstrap because:

- Sample sizes are small (often single digits per game).
- Weights are unequal (source tiers).
- The score distribution is not necessarily normal.

Bootstrap degrades gracefully across all three. Closed-form weighted
standard error would require distributional assumptions that
genuinely don't hold here.

## What's deliberately not here

- **A live database.** All data is materialized at build time.
- **A queue, worker pool, or scheduler beyond a weekly cron.** Build
  cadence is weekly; there is nothing in production that needs to run
  more often than that.
- **A CMS or admin interface.** Editorial state lives in CSV files in
  `data/overrides/`, edited with a text editor and reviewed in git.
- **User accounts, sessions, or any writable runtime state.** See the
  mantras.
