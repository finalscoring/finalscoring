# Architecture overview

## Repository shape

Final Scoring uses a single monorepo called `finalscoring`.

The monorepo contains three runnable applications and one shared Python core package.

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

The API is a FastAPI service.

Its responsibility is to expose Final Scoring data through a small and clear HTTP interface. It should stay relatively thin and delegate most business logic to the shared Python package.

Responsibilities:

- define HTTP routes
- validate requests and shape responses
- wire dependencies such as database sessions
- expose health and application endpoints

### `apps/worker`

The worker is a Python CLI application used for scheduled jobs and maintenance tasks.

Responsibilities:

- run scraping jobs
- run processing and normalisation jobs
- rebuild derived aggregates
- host operational scripts and backfill commands

The worker should remain a straightforward command-line surface rather than evolving into a heavy job framework too early.

### `apps/web`

The web app is a Next.js frontend.

Responsibilities:

- render public product pages
- consume the backend API
- present rankings, game pages, and publication information
- provide a simple, indexable, content-oriented user experience

### `packages/py/finalscoring`

This is the shared Python core of the system.

It contains:

- domain models
- database models and DB access primitives
- scraping code
- processing and canonicalisation logic
- scoring and aggregation logic
- shared utilities

Most business logic should live here rather than inside the API or web layers.

## Data flow

The core end-to-end data flow is:

1. scrape or ingest review source data
2. store raw or semi-structured source output
3. normalise the extracted data into canonical entities
4. resolve entities such as games and publications
5. compute derived values such as normalised scores and aggregates
6. persist the canonical data in PostgreSQL
7. expose the data through the API
8. render it in the web frontend

In simplified form:

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

The system uses PostgreSQL as its main database.

Reasons:

- relational data model fits games, publications, and reviews well
- strong support for constraints and joins
- mature tooling
- easy local and hosted deployment
- enough search capability for early stages

SQLAlchemy and Alembic are used for ORM mapping and schema migrations.

## Packaging and dependency management

### Python

Python is the primary language for backend, scraping, processing, and scoring.

Tooling choices:

- `uv` for dependency and environment management
- `pytest` for tests
- `ruff` for linting and formatting
- `SQLAlchemy` and `Alembic` for persistence
- `Scrapy` for scraping
- `Polars` for tabular processing where useful

### Frontend

The frontend uses:

- `Next.js`
- `TypeScript`
- `pnpm`

## Configuration

Applications should be configured through environment variables.

The project should avoid deep coupling to any single hosting provider. Runtime assumptions should stay portable so the system can be deployed locally, on Heroku-like platforms, or elsewhere with minimal change.

## Local development

Local development is intentionally simple.

The baseline setup is:

- PostgreSQL via Docker Compose
- API run directly with `uv`
- worker run directly with `uv`
- web app run directly with `pnpm`

This keeps the workflow lightweight while still being compatible with containerised deployment later.

## Architectural principles

### Keep the API thin

Route handlers should not accumulate business logic.

### Keep the worker simple

Scheduled and batch jobs should begin as plain CLI commands.

### Prefer shared domain logic

Canonical business logic should live in the shared Python package.

### Avoid premature distribution

No microservices, queues, or service decomposition should be introduced unless real operational pain justifies them.

### Design for portability

The codebase should remain easy to run locally and easy to move between hosting providers.

## Expected evolution

The initial system is intentionally simple, but it should leave room for later additions such as:

- richer search
- critic entities and author-level modelling
- source-specific parsing frameworks
- more advanced aggregate metrics
- internal admin tooling
- asynchronous jobs if justified by actual workload

These should be added only when the product demonstrates a concrete need for them.
