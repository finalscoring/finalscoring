# Final Scoring

Board game **critic** review aggregation — closer to Metacritic for board games than a general community site. The MVP centres on critic aggregation, not user ratings, accounts, or social features.

## Start here

- **`AGENTS.md`** — handoff guide and working rules for contributors and coding agents
- **`docs/current-priority.md`** — active implementation focus
- **`docs/development.md`** — prerequisites, install, run, test, lint
- **`docs/product.md`** and **`docs/decisions.md`** — before major product or architecture changes

## Repository layout

`apps/api` (FastAPI), `apps/worker` (CLI jobs), `apps/web` (Next.js), and `packages/py/finalscoring` (shared domain and data logic). Full structure, boundaries, and data flow: **`docs/architecture.md`**.

## Documentation

The full reading list (roadmap, data model, source strategy, score normalisation, entity resolution, API/frontend/testing notes) is in **`AGENTS.md`**.
