# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

Final Scoring is a board game criticism and review aggregation platform — closer to Metacritic for board games than a general community site. The MVP focus is critic aggregation, not user ratings, accounts, or social features.

**Before making substantial changes**, read `docs/current-priority.md` to understand the active phase. For architecture/product decisions read `docs/architecture.md`, `docs/data-model.md`, and `docs/decisions.md`. Agent-specific guidance is in `agents/coding-guidelines.md` and `agents/project-overview.md`.

## Repo structure

```
apps/api/        FastAPI backend (thin routes, delegates to shared package)
apps/worker/     Background jobs as plain CLI commands (not a job framework)
apps/web/        Next.js frontend
packages/py/finalscoring/   Shared Python core: domain, DB models, scraping, scoring
```

All core business logic lives in `packages/py/finalscoring`, not in apps.

## Commands

### Setup

```bash
docker compose up -d db                          # start PostgreSQL
cd packages/py/finalscoring && uv sync
cd apps/api && uv sync
cd apps/worker && uv sync
cd apps/web && pnpm install
```

### Run

```bash
make api      # cd apps/api && uv run uvicorn finalscoring_api.main:app --reload
make worker   # cd apps/worker && uv run python -m finalscoring_worker.cli --help
make web      # cd apps/web && pnpm dev
```

### Test

```bash
# Run all Python tests (from repo root)
make test

# Run tests for a specific package
cd packages/py/finalscoring && uv run pytest
cd apps/api && uv run pytest
cd apps/worker && uv run pytest

# Run a single test file
cd packages/py/finalscoring && uv run pytest tests/path/to/test_file.py
```

### Lint

```bash
make lint

# Or per package:
cd packages/py/finalscoring && uv run ruff check . && uv run ruff format --check .
```

## Architecture rules

- **API stays thin**: routes validate inputs, call shared logic, return responses — no business logic in handlers
- **Worker stays simple**: plain CLI commands, not a workflow framework
- **Domain logic in `packages/py/finalscoring`**: domain models, DB access, scraping, scoring, processing all belong here
- **No microservices, queues, or event-driven systems** unless justified by real operational pain

## Key areas requiring special caution

Mistakes here produce silent product errors — be explicit and conservative:

- **Score normalisation** (`docs/score-normalisation.md`) — normalisation must be traceable
- **Entity resolution** (`docs/entity-resolution.md`) — conservative matching policy
- **Source inclusion policy** (`docs/source-strategy.md`)
- Edition vs base game distinctions
- Scoreless review handling
- Duplicate review handling

## Data model

Three canonical entities: `Game`, `Publication`, `Review`. Preserve `original_score` string from source alongside derived `normalised_score`. Do not commit raw scraped data to git.

## Current phase

**Phase 1 — Canonical DB foundation**: SQLAlchemy models, Alembic setup, initial migration, DB session wiring. See `docs/current-priority.md` for the full definition of done.

## Python conventions

- Python 3.12+, modern type annotations on all function signatures
- Prefer Polars for tabular processing, Pydantic for structured validation
- SQLAlchemy + Alembic for DB; Scrapy for scraping
- Linting/formatting: Ruff
