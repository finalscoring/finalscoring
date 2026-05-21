# Development guide

## Principles

Simplicity, readability, coherent vertical slice over generic frameworks. Product scope: **`docs/product.md`**. Component boundaries, data flow, persistence: **`docs/architecture.md`**. Contributor norms: **`AGENTS.md`**.

## Core stack

### Backend and data

- Python 3.13+
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
```

## Local setup

### Prerequisites

- Python 3.13+
- `uv`
- Node.js 22+
- `pnpm`
- Docker and Docker Compose

### Start PostgreSQL

```bash
docker compose up -d db
```

### Install dependencies

From repo root:

```bash
cd packages/py/finalscoring && uv sync
cd ../../../apps/api && uv sync
cd ../worker && uv sync
cd ../web && pnpm install
```

### Environment variables

Copy `.env.example` to `.env` in each app dir. Adjust if needed. Defaults work for standard local Docker Compose setup.

```bash
cp apps/api/.env.example apps/api/.env
```

### Apply migrations

From `packages/py/finalscoring`:

```bash
uv run alembic upgrade head
```

Run after initial setup and after pulling new migration files.

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

## Makefile shortcuts (optional)

From repo root, same workflows via `Makefile` targets:

- `make db-up` — start PostgreSQL (`docker compose up -d db`)
- `make db-down` — `docker compose down`
- `make migrate` — run `alembic upgrade head` in shared package
- `make api`, `make worker`, `make web` — API reload, worker CLI `--help`, Next.js dev
- `make test` — pytest in `packages/py/finalscoring`, `apps/api`, `apps/worker`
- `make lint` — Ruff check and format check in those Python trees

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

Flow: scrape → parse → canonical entities → normalise scores → resolve games and publications → PostgreSQL. No raw scraped data commits. End-to-end picture: **`docs/architecture.md`** (Data flow).

## Migrations

Managed with Alembic.

Rules:

- schema changes explicit
- migrations committed with dependent code
- no hidden schema drift from ad hoc manual DB edits

## Documentation

Decisions go in `docs/`.

- update `product.md` on MVP scope changes
- update `data-model.md` on core entity/relationship changes
- update `architecture.md` on material component boundary changes

## What to avoid

See **`AGENTS.md`**. In code: speculative architecture, framework-heavy setups, hidden config magic, business logic in route handlers or frontend, broad refactors without product justification.

## AI-assisted development

Primary guidance for coding agents: `AGENTS.md`. AI-generated changes still need critical review.