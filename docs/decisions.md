# Project decisions

Records explicit decisions. Not re-litigated unless concrete reason exists.

## 2026-04-13 — Final Scoring is a separate project

Final Scoring = own GitLab project, not inside Recommend.Games.

### Rationale

- own domain and brand
- distinct product
- independent repo, issues, CI, deployment
- no inherited licensing or packaging from Recommend.Games

## 2026-04-13 — Brand and naming conventions

Human-readable brand: **Final Scoring**.

Conventions:

- brand: `Final Scoring`
- domain: `finalscoring.games`
- technical slug / repo / namespace: `finalscoring`

### Rationale

Public identity elegant. Technical identifiers simple and consistent.

## 2026-04-13 — Start with a monorepo

Single monorepo named `finalscoring`.

### Rationale

- backend, frontend, scraping, processing, scoring tightly coupled in MVP
- shared domain and data-model changes span multiple parts
- faster iteration, better consistency
- early split = unnecessary coordination overhead

## 2026-04-13 — Keep strong internal boundaries inside the monorepo

Clear boundaries between runnable apps and shared libraries.

Expected structure:

- `apps/api`
- `apps/worker`
- `apps/web`
- `packages/py/finalscoring`

### Rationale

Monorepo ≠ unstructured. Internal boundaries stay clear even in one repo.

## 2026-04-13 — Use Python for backend, ingestion, processing, and scoring

Python = primary language for backend and data side.

### Rationale

- matches existing strengths and tooling
- scraping, parsing, processing, scoring are Python-shaped problems
- no language fragmentation
- easy to share core logic between API and worker

## 2026-04-13 — Use FastAPI for the backend API

Backend API = FastAPI.

### Rationale

- fast iteration
- good fit for typed request/response models
- straightforward dev experience
- aligns with Python-first architecture

## 2026-04-13 — Use Next.js for the frontend

Web frontend = Next.js + TypeScript.

### Rationale

- good fit for public, content-heavy, indexable pages
- strong ecosystem and deployment flexibility
- supports server-rendered and browseable product pages
- easy for coding agents

## 2026-04-13 — Use PostgreSQL as the primary database

PostgreSQL = system of record for canonical application data.

### Rationale

- naturally relational data model
- mature, portable, affordable, easy to run locally
- sufficient for early search and aggregation

## 2026-04-13 — Use SQLAlchemy and Alembic

DB persistence = SQLAlchemy + Alembic.

### Rationale

- mature, well-understood tools
- good fit for Python app and migration workflows
- no experimental data layers in MVP

## 2026-04-13 — Use Scrapy for scraping

Scraping = Scrapy.

### Rationale

- existing familiarity
- well-suited to multi-source crawling and extraction
- fits raw extraction → later processing workflow

## 2026-04-13 — Use uv for Python package and environment management

Python deps and environments = `uv`.

### Rationale

- simple and fast
- fits app-local environments in monorepo
- no unnecessary tooling complexity

## 2026-04-13 — Use pnpm for the frontend

Frontend = `pnpm`.

### Rationale

- fast and efficient
- good fit for JS/TS in larger repo
- room for future shared frontend packages

## 2026-04-13 — Do not commit to hosting yet

Repo stays portable. No deep tie to any hosting provider.

### Rationale

- hosting not current bottleneck
- priority = right product shape and implementation
- portability matters more than provider choice now

## 2026-04-13 — Optimise for simplicity, affordability, and portability

Early decisions favour:

- low cognitive overhead
- low operational complexity
- affordable infrastructure
- ability to move hosting later

### Rationale

Project is early. No scalability-driven architecture needed yet.

## 2026-04-13 — Local development should be lightweight

Local dev uses:

- PostgreSQL via Docker Compose
- API run directly with `uv`
- worker run directly with `uv`
- web app run directly with `pnpm`

### Rationale

Keeps dev loop simple. No over-containerising day-one workflows.

## 2026-04-13 — Worker tasks should start as plain CLI commands

Background and operational tasks = CLI commands first, not queues or workflow systems.

### Rationale

- simpler to build and debug
- compatible with cron, schedulers, CI, future job runners
- no premature infrastructure

## 2026-04-13 — Avoid microservices, queues, and workflow systems in MVP

No microservices, service decomposition, queues, or heavy workflow tools unless clear present pain justifies them.

### Rationale

MVP = tightly coupled vertical slice. No premature distribution.

## 2026-04-13 — API should be REST-first

Backend API = straightforward REST.

### Rationale

- simpler to implement and debug
- fits product shape
- no GraphQL complexity before evidence it's needed

## 2026-04-13 — Final Scoring focuses on critic aggregation, not user community features

Core focus = critic reviews and critical reception.

Not MVP:

- user accounts
- user reviews
- user ratings
- recommendation features
- social/community mechanics
- marketplace and collection features

### Rationale

Stay focused on differentiating value. Not a general-purpose board game platform.

## 2026-04-13 — First canonical entities are Game, Publication, and Review

First data model centres on:

- `Game`
- `Publication`
- `Review`

`Critic` entity may come later if author-level modelling matters.

### Rationale

Minimal useful entities for ingestion, storage, and presentation of critic coverage.

## When to revisit a decision

Revisit only when at least one is true:

- real implementation pain emerged
- product requirements materially changed
- current decision blocks progress
- change simplifies system in practice, not just theory

Contributors and coding agents: don't reopen settled decisions casually.