# CLAUDE.md

Guidance for Claude Code ([claude.ai/code](https://claude.ai/code)) in this repository.

## Read first

1. **`docs/current-priority.md`** — active phase and definition of done
2. **`AGENTS.md`** — working rules, full doc map, caution areas
3. **`docs/architecture.md`** and **`docs/development.md`** — structure, stack, setup, commands
4. **`docs/data-model.md`** and **`docs/decisions.md`** — entities and settled choices

## Commands

Install Postgres, sync Python packages, and install frontend deps: **`docs/development.md`** (single copy-paste chain from the repo root).

From the repository root, Makefile shortcuts:

```bash
make db-up    # PostgreSQL (Docker Compose)
make api      # API with reload
make worker   # worker CLI --help
make web      # Next.js dev
make test     # pytest in shared package, API, worker
make lint     # Ruff in those Python trees
make db-down  # tear down Compose stack
```

## Architecture (summary)

Thin FastAPI routes; plain worker CLI; business logic in **`packages/py/finalscoring`**. No microservices, queues, or heavy job frameworks unless justified. Full principles: **`docs/architecture.md`**.

## High-risk areas

Score normalisation, entity resolution, and source inclusion are easy to get wrong. Use **`docs/score-normalisation.md`**, **`docs/entity-resolution.md`**, **`docs/source-strategy.md`**, and the caution list in **`AGENTS.md`**.

## Python

3.12+, type hints, Ruff; Polars, Pydantic, SQLAlchemy, Alembic, Scrapy as in **`docs/development.md`**.
