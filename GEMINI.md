# Final Scoring

Board game review aggregation platform focused on critic reviews.

## Project Overview

Final Scoring collects published critical opinions about board games, normalises them, and presents aggregated rankings. It is a monorepo containing three applications and one shared Python package.

- **Stack:** Python 3.13+, FastAPI, Next.js, TypeScript, PostgreSQL, SQLAlchemy, Alembic, Scrapy, Polars.
- **Tooling:** `uv` for Python, `pnpm` for Node.js, `Docker Compose` for local infrastructure.
- **Architecture:** Monorepo with a thin API, simple worker CLI, and shared domain logic.

## Repository Layout

- `apps/api`: FastAPI service exposing the HTTP interface.
- `apps/worker`: Python CLI application for scraping and processing jobs.
- `apps/web`: Next.js frontend for public product pages.
- `packages/py/finalscoring`: Shared Python core (domain models, DB models, scraping logic).
- `docs/`: Comprehensive project documentation.

## Core Mandates & Principles

1.  **Read the Docs:** Before any change, read `AGENTS.md` and `docs/current-priority.md`.
2.  **Thin API:** Route handlers must remain thin; delegate business logic to the shared package.
3.  **Simple Worker:** Keep CLI jobs straightforward; avoid heavy orchestration frameworks.
4.  **Shared Domain:** All canonical business logic lives in `packages/py/finalscoring`.
5.  **No Speculative Abstraction:** Avoid building generic frameworks or speculative architecture.
6.  **DB Foundation:** The current priority is **Phase 1 — Canonical DB foundation**.

## Building and Running

### Prerequisites
- Python 3.13+, `uv`
- Node.js 22+, `pnpm`
- Docker and Docker Compose

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

- **Testing:** `make test` (runs pytest across all Python components).
- **Linting:** `make lint` (runs Ruff check and format).
- **Migrations:** Managed via Alembic in `packages/py/finalscoring`.
- **Conventions:** Use modern Python with explicit type annotations. Keep domain logic in the shared package.

## Key Documentation Files

- `AGENTS.md`: Mandatory reading for coding agents; contains handoff guide and rules.
- `docs/architecture.md`: System design, data flow, and component responsibilities.
- `docs/development.md`: Detailed setup, commands, and coding conventions.
- `docs/current-priority.md`: Active implementation focus (Phase 1).
- `docs/data-model.md`: Core entities (`Game`, `Publication`, `Review`) and relationships.
- `docs/decisions.md`: Log of architectural and product decisions.
