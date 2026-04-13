# Final Scoring

Final Scoring is a board game reviews and criticism aggregation platform.

## Repo structure

- `apps/api` – FastAPI backend
- `apps/worker` – background jobs and CLI tasks
- `apps/web` – Next.js frontend
- `packages/py/finalscoring` – shared Python domain, DB, scraping, processing, scoring

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
