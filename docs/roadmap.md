# Roadmap

This document provides a practical phase-based roadmap for the early development of Final Scoring.

The aim is not to freeze all future work, but to give contributors and coding agents a sensible order of implementation so effort stays focused on a coherent vertical slice.

## Guiding principle

Prefer completing one end-to-end slice over building disconnected subsystems in parallel.

## Phase 0 — Repository scaffold

Goal: establish the repo structure and basic developer workflow.

Deliverables:

- monorepo layout in place
- `apps/api`, `apps/worker`, `apps/web`
- `packages/py/finalscoring`
- local PostgreSQL via Docker Compose
- API health endpoint
- worker CLI skeleton
- minimal web shell
- baseline docs

Exit criteria:

- local setup works
- API, worker, and web app can all run
- repo structure is clear and documented

## Phase 1 — Canonical DB foundation

Goal: create the first real persistence layer.

Deliverables:

- SQLAlchemy base and models
- Alembic setup
- initial migrations
- canonical tables for `games`, `publications`, and `reviews`
- DB session wiring in backend code

Exit criteria:

- schema can be created locally
- migrations run cleanly
- application code can read and write the core entities

## Phase 2 — First real source ingestion

Goal: ingest one real review source end-to-end.

Deliverables:

- one source selected and documented
- scraper or ingestion adapter implemented
- extraction of source title, URL, score/verdict, and game-identifying data
- structured output from that source
- source-specific parsing logic where needed

Exit criteria:

- at least one source can be ingested repeatedly and reliably
- extracted records are inspectable
- the ingestion path is understandable and debuggable

## Phase 3 — Normalisation and canonical mapping

Goal: convert raw source data into usable canonical application data.

Deliverables:

- score normalisation for supported score formats
- publication resolution
- conservative game entity resolution
- handling of unresolved or scoreless cases
- canonical rows written to PostgreSQL

Exit criteria:

- at least one real source lands in canonical tables
- supported score types normalise correctly
- unresolved cases do not silently corrupt data

## Phase 4 — First useful API surface

Goal: expose meaningful product data via the backend.

Deliverables:

- `GET /games`
- `GET /games/{slug}` or equivalent canonical detail route
- inclusion of associated reviews on game detail
- response shape suitable for the frontend
- simple error handling conventions

Exit criteria:

- frontend can fetch and render real game data through the API
- payloads are simple and coherent
- routes reflect canonical product entities

## Phase 5 — First useful frontend pages

Goal: render a real, browseable critic aggregation experience.

Deliverables:

- homepage or browse page
- game detail page
- display of critic reviews and original source links
- display of normalised aggregate score where available
- basic rankings or listing page

Exit criteria:

- the product feels like a real critic aggregation site
- at least a small set of real games can be browsed
- pages are legible, content-oriented, and useful

## Phase 6 — Stabilisation and expansion

Goal: make the first slice more credible and easier to extend.

Deliverables:

- improve scraper robustness
- refine score normalisation coverage
- improve entity resolution handling
- add tests in the highest-risk areas
- improve docs and contributor guidance
- optionally add a second source if it does not destabilise the first slice

Exit criteria:

- the vertical slice is robust enough for demonstration or soft launch
- common failure modes are easier to detect
- the codebase remains understandable

## Defer until later unless clearly needed

The following are intentionally lower priority:

- rich search
- user accounts
- recommendations
- community features
- admin tooling
- critic-level modelling
- large-scale source onboarding frameworks
- queues and workflow systems
- microservices
- GraphQL

## Roadmap rule of thumb

If a proposed task does not clearly support the current or next phase, it should usually be deferred.
