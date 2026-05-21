# Final Scoring

Board game review aggregation platform. Critic reviews only.

## Project Overview

Collects, normalises, aggregates board game critic opinions into rankings. Monorepo: three apps + one shared Python package.

- **Stack:** Python 3.13+, FastAPI, Next.js, TypeScript, PostgreSQL, SQLAlchemy, Alembic, Scrapy, Polars.
- **Tooling:** `uv` for Python, `pnpm` for Node.js, `Docker Compose` for local infra.
- **Architecture:** Monorepo. Thin API, simple worker CLI, shared domain logic.

## Repository Layout

- `apps/api`: FastAPI HTTP service.
- `apps/worker`: Python CLI for scraping/processing.
- `apps/web`: Next.js frontend.
- `packages/py/finalscoring`: Shared Python core (domain models, DB models, scraping).
- `docs/`: Project docs.

## Core Mandates & Principles

1.  **Read the Docs:** Read `AGENTS.md` and `docs/current-priority.md` before any change.
2.  **Thin API:** Route handlers stay thin; delegate logic to shared package.
3.  **Simple Worker:** CLI jobs stay simple; no heavy orchestration.
4.  **Shared Domain:** All canonical business logic in `packages/py/finalscoring`.
5.  **No Speculative Abstraction:** No generic frameworks or speculative architecture.
6.  **DB Foundation:** Current priority = **Phase 1 — Canonical DB foundation**.

## Building and Running

### Prerequisites
- Python 3.13+, `uv`
- Node.js 22+, `pnpm`
- Docker + Docker Compose

### Local Setup
1.  **Start DB:** `make db-up` (or `docker compose up -d db`)
2.  **Install Deps:**
    ```bash
    cd packages/py/finalscoring && uv sync
    cd ../../../apps/api && uv sync
    cd ../worker && uv sync
    cd ../web && pnpm install
    ```

### Running Applications
- **API:** `make api` (or `cd apps/api && uv run uvicorn finalscoring_api.main:app --reload`)
- **Worker:** `make worker` (or `cd apps/worker && uv run python -m finalscoring_worker.cli --help`)
- **Web:** `make web` (or `cd apps/web && pnpm dev`)

## Development Workflow

- **Testing:** `make test` (pytest across all Python components).
- **Linting:** `make lint` (Ruff check + format).
- **Migrations:** Alembic in `packages/py/finalscoring`.
- **Conventions:** Modern Python, explicit type annotations. Domain logic in shared package.

## Key Documentation Files

- `AGENTS.md`: Mandatory for coding agents; handoff guide + rules.
- `docs/architecture.md`: System design, data flow, component responsibilities.
- `docs/development.md`: Setup, commands, coding conventions.
- `docs/current-priority.md`: Active focus (Phase 1).
- `docs/data-model.md`: Core entities (`Game`, `Publication`, `Review`) + relationships.
- `docs/decisions.md`: Architectural + product decision log.