# Development guide

## Principles

Development should favour simplicity, readability, and fast iteration.

The project is early-stage. The priority is to build a coherent vertical slice rather than a perfectly general framework.

Guiding principles:

- keep solutions straightforward
- avoid premature abstraction
- prefer boring tools over clever infrastructure
- keep business logic out of route handlers
- add complexity only when it solves a real problem

## Core stack

### Backend and data

- Python 3.12+
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Scrapy
- Polars

### Frontend

- Next.js
- TypeScript
- pnpm

### Tooling

- uv
- Ruff
- pytest
- Docker Compose

## Repo structure

```text
apps/
  api/
  worker/
  web/
packages/
  py/
    finalscoring/
docs/
agents/
```

## Local setup

### Prerequisites

- Python 3.12+
- `uv`
- Node.js 22+
- `pnpm`
- Docker and Docker Compose

### Start PostgreSQL

```bash
docker compose up -d db
```

### Install Python dependencies

```bash
cd packages/py/finalscoring && uv sync
cd ../../../apps/api && uv sync
cd ../worker && uv sync
```

### Install frontend dependencies

```bash
cd apps/web && pnpm install
```

## Running the applications

### API

```bash
cd apps/api
uv run uvicorn finalscoring_api.main:app --reload
```

### Worker

```bash
cd apps/worker
uv run python -m finalscoring_worker.cli --help
```

### Web

```bash
cd apps/web
pnpm dev
```

## Testing

### Python tests

```bash
cd packages/py/finalscoring && uv run pytest
cd ../../../apps/api && uv run pytest
cd ../worker && uv run pytest
```

### Linting

```bash
cd packages/py/finalscoring && uv run ruff check . && uv run ruff format --check .
cd ../../../apps/api && uv run ruff check . && uv run ruff format --check .
cd ../worker && uv run ruff check . && uv run ruff format --check .
```

## Coding conventions

### Python

- use modern Python with explicit type annotations on function signatures
- prefer clear and direct code over abstraction-heavy designs
- keep domain logic in `packages/py/finalscoring`
- keep FastAPI route handlers thin
- prefer Polars for tabular processing work
- use Pydantic models where structured validation is useful

### TypeScript and frontend

- keep frontend components simple and focused
- avoid introducing frontend state complexity too early
- prefer server-friendly, content-oriented page design
- keep API integration explicit and easy to trace

## Data pipeline conventions

The data pipeline should be easy to reason about.

A typical flow is:

1. scrape raw source data
2. parse and structure it
3. map it into canonical entities
4. normalise scores
5. resolve entities such as games and publications
6. write the results into PostgreSQL

Raw scraped data should not be committed to git.

## Migrations

Database migrations are managed with Alembic.

Rules:

- schema changes should be explicit
- migrations should be committed with the code that depends on them
- avoid hidden schema drift from ad hoc manual database edits

## Documentation

Important project decisions should be written down in `docs/`.

In particular:

- update `product.md` when MVP scope changes
- update `data-model.md` when core entities or relationships change
- update `architecture.md` when component boundaries change materially

## What to avoid

- speculative architecture
- framework-driven complexity
- hidden magic in configuration or dependency injection
- spreading business logic across route handlers, scripts, or frontend code
- broad refactors with weak product justification

## AI-assisted development

The primary guidance for coding agents is in `AGENTS.md`. AI-generated changes should still be reviewed critically.
