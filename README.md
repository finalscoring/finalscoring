# Final Scoring


Final Scoring is a board game reviews and criticism aggregation platform.

## Start here

- Read `AGENTS.md` for the repository handoff guide and working rules
- Read `docs/current-priority.md` for the active implementation focus
- Read `docs/product.md` and `docs/decisions.md` before making major architectural or product changes

## Repo structure

- `apps/api` – FastAPI backend
- `apps/worker` – background jobs and CLI tasks
- `apps/web` – Next.js frontend
- `packages/py/finalscoring` – shared Python domain, DB, scraping, processing, scoring

## Key documentation

- `AGENTS.md` – entry point for coding agents and contributors
- `docs/current-priority.md` – what to work on now
- `docs/roadmap.md` – development phases and sequencing
- `docs/product.md` – product intent and MVP boundaries
- `docs/architecture.md` – repository and system structure
- `docs/data-model.md` – canonical entity model
- `docs/source-strategy.md` – source inclusion and ingestion policy
- `docs/score-normalisation.md` – score mapping principles
- `docs/entity-resolution.md` – conservative matching policy

## Prerequisites

- Python 3.12+
- `uv`
- Node.js 22+
- `pnpm`
- Docker + Docker Compose

## Getting started

### Start Postgres

```bash
docker compose up -d db
```

### Install Python packages

```bash
cd packages/py/finalscoring && uv sync
cd ../../../apps/api && uv sync
cd ../worker && uv sync
```

### Install web dependencies

```bash
cd apps/web && pnpm install
```

### Run the API

```bash
cd apps/api
uv run uvicorn finalscoring_api.main:app --reload
```

### Run the worker CLI

```bash
cd apps/worker
uv run python -m finalscoring_worker.cli --help
```

### Run the web app

```bash
cd apps/web
pnpm dev
```
