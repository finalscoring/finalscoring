# Architecture overview

## Repository shape

Single monorepo: `finalscoring`. Three runnable apps, one shared Python core package.

```text
apps/
  api/
  worker/
  web/
packages/
  py/
    finalscoring/
```

## Main components

### `apps/api`

FastAPI service. Thin HTTP interface over shared package.

Responsibilities:

- define HTTP routes
- validate requests and shape responses
- wire dependencies such as database sessions
- expose health and application endpoints

### `apps/worker`

Python CLI for scheduled jobs and maintenance.

Responsibilities:

- run scraping jobs
- run processing and normalisation jobs
- rebuild derived aggregates
- host operational scripts and backfill commands

Stay simple CLI — not job framework.

### `apps/web`

Next.js frontend.

Responsibilities:

- render public product pages
- consume backend API
- present rankings, game pages, publication info
- simple, indexable, content-oriented UX

### `packages/py/finalscoring`

Shared Python core. Contains:

- domain models
- database models and DB access primitives
- scraping code
- processing and canonicalisation logic
- scoring and aggregation logic
- shared utilities

Most business logic lives here, not in API or web layers.

## Data flow

Core end-to-end flow:

1. scrape or ingest review source data
2. store raw or semi-structured source output
3. normalise into canonical entities
4. resolve entities (games, publications)
5. compute derived values (normalised scores, aggregates)
6. persist in PostgreSQL
7. expose through API
8. render in web frontend

```text
Source websites
  -> scraping
  -> raw extracted review data
  -> processing and canonicalisation
  -> PostgreSQL
  -> FastAPI
  -> Next.js frontend
```

## Persistence

PostgreSQL as main database.

Reasons:

- relational model fits games, publications, reviews
- strong constraints and joins
- mature tooling
- easy local and hosted deployment
- sufficient search for early stages

SQLAlchemy + Alembic for ORM and migrations.

## Packaging and dependency management

### Python

Primary language for backend, scraping, processing, scoring.

Tooling:

- `uv` — dependency and environment management
- `pytest` — tests
- `ruff` — linting and formatting
- `SQLAlchemy` and `Alembic` — persistence
- `Scrapy` — scraping
- `Polars` — tabular processing

### Frontend

- `Next.js`
- `TypeScript`
- `pnpm`

## Configuration

Configure via environment variables. No deep coupling to any hosting provider. Stays portable for local, Heroku-like, or other deployment.

## Local development

PostgreSQL via Docker Compose, API and worker via `uv`, web via `pnpm`. Details: **`docs/development.md`**.

## Architectural principles

### Keep the API thin

No business logic in route handlers.

### Keep the worker simple

Batch jobs start as plain CLI commands.

### Prefer shared domain logic

Canonical business logic in shared Python package.

### Avoid premature distribution

No microservices, queues, or decomposition without real operational pain.

### Design for portability

Easy to run locally, easy to move between hosting providers.

## Expected evolution

Add only when product shows concrete need:

- richer search
- critic entities and author-level modelling
- source-specific parsing frameworks
- more advanced aggregate metrics
- internal admin tooling
- async jobs if justified by workload