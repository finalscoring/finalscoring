# Gemini CLI Context: Final Scoring

This file provides critical context and instructions for Gemini CLI when working on the Final Scoring project.

## Project Overview

**Final Scoring** is a board game critic review aggregation platform (think "Metacritic for board games"). It focuses on professional critic reviews rather than user ratings.

### Core Technologies
- **Backend:** Python 3.13+, FastAPI, SQLAlchemy (ORM), Alembic (Migrations), Scrapy (Scraping), Polars (Data processing).
- **Frontend:** Next.js, TypeScript, pnpm.
- **Tooling:** `uv` (Python package management), `ruff` (linting/formatting), `pytest` (testing), Docker Compose (PostgreSQL).

### Architecture & Monorepo Structure
The project uses a monorepo structure with clear boundaries:
- `apps/api`: FastAPI service. Should remain "thin" (routing, validation, DI).
- `apps/worker`: CLI application for scraping, processing, and maintenance tasks.
- `apps/web`: Next.js frontend.
- `packages/py/finalscoring`: **The Shared Core.** Contains all domain models, DB models, scraping logic, and business rules.

## Building and Running

The project includes a `Makefile` for common tasks.

| Command | Description |
| :--- | :--- |
| `make db-up` | Start PostgreSQL via Docker Compose |
| `make db-down` | Stop PostgreSQL |
| `make api` | Run the FastAPI dev server (with reload) |
| `make worker` | Run the worker CLI help command |
| `make web` | Run the Next.js dev server |
| `make test` | Run all Python tests (Core, API, Worker) |
| `make lint` | Run ruff check and format check across Python projects |

### Manual Setup (if needed)
1. **Python Dependencies:** Use `uv sync` in `packages/py/finalscoring`, `apps/api`, and `apps/worker`.
2. **Frontend Dependencies:** Use `pnpm install` in `apps/web`.

## Development Conventions

### General Rules
- **Correctness over Speed:** Optimize for clarity and scope discipline (see `AGENTS.md`).
- **Vertical Slices:** Prefer completing one end-to-end feature (scrape -> process -> API -> web) over horizontal layers.
- **Thin Layers:** Keep `apps/api` and `apps/web` thin; keep business and domain logic in `packages/py/finalscoring`.

### Python Coding Standards
- **Typing:** Use modern Python with explicit type annotations on all function signatures.
- **Logic Placement:** Domain logic MUST live in `packages/py/finalscoring`.
- **Tooling:** Always use `ruff` for formatting and linting. Use `pytest` for testing.
- **Migrations:** Managed via Alembic. Always commit migrations alongside the code that requires them.

### Agent-Specific Guidance (`AGENTS.md`)
- **Read First:** Before major changes, consult `docs/current-priority.md` and `docs/decisions.md`.
- **Conservative Changes:** Avoid premature abstractions or "hidden" logic.
- **No Refactoring:** Do not perform broad refactors without explicit product justification.
- **Entity Resolution:** Be extremely careful with game/publication resolution and score normalization logic.

## Documentation Reference
- `docs/architecture.md`: System design and data flow.
- `docs/development.md`: Detailed setup and workflow.
- `docs/data-model.md`: Core entities and relationships.
- `docs/decisions.md`: Log of settled architectural and product questions.
- `AGENTS.md`: Specific instructions for AI-assisted development.
