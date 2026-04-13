# Agent handoff guide

This repository is intended to be workable by coding agents, but agents should optimise for correctness, clarity, and scope discipline rather than speed alone.

## Read this first

Before making substantial changes, read these documents:

- `docs/product.md`
- `docs/architecture.md`
- `docs/data-model.md`
- `docs/development.md`
- `docs/decisions.md`
- `docs/mvp.md`
- `docs/source-strategy.md`
- `docs/score-normalisation.md`
- `docs/entity-resolution.md`

Then consult task-specific docs such as:

- `docs/roadmap.md`
- `docs/api-principles.md`
- `docs/frontend-principles.md`
- `docs/testing-strategy.md`
- `docs/contribution-playbook.md`

## Project summary

Final Scoring is a board game criticism and review aggregation platform.

The product goal is to collect published critical opinions about board games, normalise them into a comparable structure, and present them in a way that helps readers understand how games are being received.

This is not a general board game community product. The MVP focus is critic aggregation, not user ratings, accounts, recommendations, social features, or collection management.

## Current stage

The project is early.

The current priority is to build a coherent MVP vertical slice across:

- source ingestion
- canonical data modelling
- score normalisation
- backend API
- frontend rendering

## Stack and repo shape

The project uses a monorepo called `finalscoring`.

Main structure:

- `apps/api` — FastAPI backend
- `apps/worker` — scraping, ingestion, processing, and batch jobs
- `apps/web` — Next.js frontend
- `packages/py/finalscoring` — shared Python domain, DB, scraping, processing, and scoring logic

Main technologies:

- Python 3.12+
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Scrapy
- Polars
- Next.js
- TypeScript
- pnpm
- uv

## High-level working rules

- keep the API thin
- keep business logic in shared Python code
- keep worker tasks simple and explicit
- avoid premature abstraction
- avoid microservices, queues, and workflow systems unless clearly necessary
- preserve already-made project decisions unless there is strong evidence they should be revisited
- prefer conservative product behaviour over speculative automation
- do not silently invent product rules that are not documented

## Expected change style

When implementing work:

1. understand the local context first
2. read the relevant docs before changing code
3. make the smallest coherent change that solves the actual problem
4. keep naming and structure consistent with the existing repo
5. add or update tests when appropriate
6. update docs when behaviour, assumptions, or architecture change materially

## Special caution areas

Be especially careful in these parts of the project:

- source inclusion policy
- score normalisation
- entity resolution
- edition vs base game distinctions
- scoreless reviews
- duplicate review handling

If uncertain in these areas, prefer explicitness and conservative behaviour.

## What not to optimise for yet

Do not prioritise:

- abstract architecture neatness over shipping
- generic frameworks for everything
- broad source coverage before the first source works well
- complex frontend state systems
- speculative scalability work
- highly dynamic product behaviour that is not yet needed

## Rule of thumb

When in doubt, choose the option that:

1. helps ship the MVP
2. keeps the codebase understandable
3. preserves room for later extension
4. avoids unnecessary infrastructure or abstraction
