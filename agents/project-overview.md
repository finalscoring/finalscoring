# Final Scoring project overview

## What this project is

Final Scoring is a board game criticism and review aggregation platform.

The goal is to collect published critical opinions about board games, normalise them into a comparable structure, and present them in a way that helps readers understand how games are being received.

The product idea is closer to Metacritic for board games than to a general board game community site. The focus is on critic coverage rather than user ratings, collections, trading, community discussion, or recommendation features.

## Current project stage

This project is at an early stage.

The main priority is to establish a clean, coherent vertical slice across:

- data ingestion
- canonical data modelling
- score normalisation
- backend API
- frontend rendering

The project should optimise for clarity, maintainability, and speed of iteration rather than abstract completeness.

## Product scope for the MVP

The MVP should include:

- a canonical database of games, publications, and reviews
- ingestion from at least one real review source
- score normalisation into a common scale
- simple game pages showing critic information
- simple listing or ranking pages
- a small but coherent API and frontend

The MVP should not include:

- user accounts
- user ratings or reviews
- recommendation systems
- social features
- marketplace or collection management features
- heavy personalisation
- broad support for every review source from day one

## Technical direction

The project currently uses a single monorepo named `finalscoring`.

Top-level structure:

- `apps/api` for the FastAPI backend
- `apps/worker` for scraping, processing, and batch jobs
- `apps/web` for the Next.js frontend
- `packages/py/finalscoring` for shared Python domain, DB, scraping, processing, and scoring logic

## Preferred stack

### Backend and data

- Python 3.12+
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Scrapy
- Polars where tabular processing is useful

### Frontend

- Next.js
- TypeScript
- pnpm

### Tooling

- uv for Python dependency and environment management
- Ruff for linting and formatting
- pytest for tests
- Docker Compose for simple local infrastructure

## Architectural expectations

### Keep the API thin

Route handlers should mainly validate inputs, call shared logic, and return responses.

### Keep business logic in shared Python code

Core logic should live in `packages/py/finalscoring`, not be duplicated across apps.

### Keep the worker simple

Background and operational tasks should begin as plain CLI commands rather than a heavy workflow system.

### Avoid premature complexity

Do not introduce microservices, queues, event-driven architecture, or complicated abstractions unless there is clear evidence they are needed.

### Prefer boring and portable solutions

Favour straightforward designs that work locally and remain easy to move between hosting providers.

## Data model direction

The first canonical entities are:

- `Game`
- `Publication`
- `Review`

A `Critic` entity may be added later if author-level modelling becomes important.

The system should preserve source truth where useful, especially source URLs and original score representations, while also deriving a normalised comparable score when possible.

## Expectations for generated code and changes

When making changes in this repository:

- preserve the monorepo structure
- keep code easy to read and trace
- avoid moving too much logic into frameworks
- avoid creating new packages or subsystems without a concrete reason
- prefer small, well-scoped changes over speculative architecture work
- keep product goals in mind, not just code neatness

## Decision heuristic

When in doubt, choose the solution that:

1. makes the MVP easier to ship
2. keeps the codebase easier to understand
3. preserves room for later extension
4. avoids unnecessary infrastructure or abstraction
