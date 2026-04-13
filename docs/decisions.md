# Project decisions

This document records explicit project decisions that should not be repeatedly re-litigated by contributors or coding agents unless there is a concrete reason to revisit them.

## 2026-04-13 — Final Scoring is a separate project

Final Scoring should live as its own GitLab project rather than inside the existing Recommend.Games project.

### Rationale

- it has its own domain and brand identity
- it is a distinct product, even if related in spirit
- it should have independent repo structure, issue tracking, CI, and deployment choices
- it should not inherit unnecessary licensing or packaging assumptions from Recommend.Games

## 2026-04-13 — Brand and naming conventions

The human-readable brand is **Final Scoring**.

Conventions:

- brand: `Final Scoring`
- domain: `finalscoring.games`
- technical slug / repo / namespace: `finalscoring`

### Rationale

This keeps the public-facing identity elegant and the technical identifiers simple and consistent.

## 2026-04-13 — Start with a monorepo

The project should start as a single monorepo named `finalscoring`.

### Rationale

- backend, frontend, scraping, processing, and scoring are tightly coupled during MVP
- shared domain and data-model changes will frequently span multiple parts of the system
- a monorepo makes it easier to iterate quickly and maintain consistency
- splitting into multiple repos too early would add unnecessary coordination and packaging overhead

## 2026-04-13 — Keep strong internal boundaries inside the monorepo

The monorepo should still have clear boundaries between runnable apps and shared libraries.

Expected structure:

- `apps/api`
- `apps/worker`
- `apps/web`
- `packages/py/finalscoring`

### Rationale

Monorepo does not mean unstructured code. Internal boundaries should remain clear even while everything lives in one repository.

## 2026-04-13 — Use Python for backend, ingestion, processing, and scoring

Python is the primary language for the backend and data side of the system.

### Rationale

- it aligns with existing strengths and preferred tooling
- scraping, parsing, processing, and scoring are naturally Python-shaped problems
- it avoids unnecessary language fragmentation
- it makes it easier to share core logic between API and worker code

## 2026-04-13 — Use FastAPI for the backend API

The backend API should be implemented with FastAPI.

### Rationale

- fast iteration
- good fit for typed request and response models
- straightforward development experience
- good alignment with Python-first backend architecture

## 2026-04-13 — Use Next.js for the frontend

The web frontend should be implemented with Next.js and TypeScript.

### Rationale

- good fit for public, content-heavy, indexable pages
- strong ecosystem and deployment flexibility
- suitable for server-rendered and browseable product pages
- easy for coding agents to work with

## 2026-04-13 — Use PostgreSQL as the primary database

PostgreSQL is the system of record for canonical application data.

### Rationale

- the project has a naturally relational data model
- PostgreSQL is mature, portable, affordable, and easy to run locally
- it provides enough capability for early search and aggregation use cases

## 2026-04-13 — Use SQLAlchemy and Alembic

Database persistence should use SQLAlchemy and Alembic.

### Rationale

- mature and well-understood tools
- good fit for Python-based application and migration workflows
- avoid experimental or over-clever data layers in MVP

## 2026-04-13 — Use Scrapy for scraping

Scraping should use Scrapy.

### Rationale

- existing familiarity and preference
- well suited to multi-source crawling and extraction
- fits the intended workflow of raw source extraction followed by later processing

## 2026-04-13 — Use uv for Python package and environment management

Python dependency and environment management should use `uv`.

### Rationale

- simple and fast
- suitable for app-local environments in a monorepo
- avoids unnecessary tooling complexity

## 2026-04-13 — Use pnpm for the frontend

The frontend should use `pnpm`.

### Rationale

- fast and efficient
- good fit for JS/TS work in a larger repo
- leaves room for future shared frontend packages if needed

## 2026-04-13 — Do not commit to hosting yet

The repo should remain portable and should not yet be deeply tied to any hosting provider.

### Rationale

- hosting is not the present bottleneck
- the priority is getting the product shape and implementation right
- architecture portability matters more than provider choice at this stage

## 2026-04-13 — Optimise for simplicity, affordability, and portability

Early decisions should favour:

- low cognitive overhead
- low operational complexity
- affordable infrastructure
- ability to move hosting later if needed

### Rationale

The project is early. It does not need scalability-driven architecture yet.

## 2026-04-13 — Local development should be lightweight

Local development should use:

- PostgreSQL via Docker Compose
- API run directly with `uv`
- worker run directly with `uv`
- web app run directly with `pnpm`

### Rationale

This keeps the development loop simple and avoids over-containerising day-one workflows.

## 2026-04-13 — Worker tasks should start as plain CLI commands

Background and operational tasks should begin as straightforward CLI commands rather than a queue or workflow system.

### Rationale

- simpler to build and debug
- compatible with cron, schedulers, CI, or future job runners
- avoids premature infrastructure

## 2026-04-13 — Avoid microservices, queues, and workflow systems in MVP

Do not introduce microservices, service decomposition, queues, or heavy workflow tools unless there is clear present pain that justifies them.

### Rationale

The MVP is a tightly coupled vertical slice and should not be distributed prematurely.

## 2026-04-13 — API should be REST-first

The backend API should start as a straightforward REST API.

### Rationale

- simpler to implement and debug
- fits the product shape well
- avoids GraphQL complexity before there is evidence it is needed

## 2026-04-13 — Final Scoring focuses on critic aggregation, not user community features

The core product focus is critic reviews and critical reception.

Not MVP priorities:

- user accounts
- user reviews
- user ratings
- recommendation features
- social/community mechanics
- marketplace and collection features

### Rationale

The product should stay focused on its differentiating value rather than trying to become a general-purpose board game platform.

## 2026-04-13 — First canonical entities are Game, Publication, and Review

The first version of the data model should centre on:

- `Game`
- `Publication`
- `Review`

A `Critic` entity may be added later if author-level modelling becomes important.

### Rationale

These are the minimal useful entities needed to support ingestion, storage, and presentation of critic coverage.

## When to revisit a decision

A recorded decision should only be revisited when at least one of the following is true:

- real implementation pain has emerged
- product requirements have materially changed
- there is strong evidence that the current decision blocks progress
- a change would simplify the system in practice, not just in theory

Contributors and coding agents should not reopen settled decisions casually.
