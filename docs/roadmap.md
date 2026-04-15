# Roadmap

Phase-based roadmap for early Final Scoring development. Not a freeze — gives contributors sensible implementation order for coherent vertical slice.

## Guiding principle

Complete one end-to-end slice. No disconnected parallel subsystems.

## Phase 0 — Repository scaffold

Goal: repo structure + basic dev workflow.

Deliverables:

- monorepo layout
- `apps/api`, `apps/worker`, `apps/web`
- `packages/py/finalscoring`
- local PostgreSQL via Docker Compose
- API health endpoint
- worker CLI skeleton
- minimal web shell
- baseline docs

Exit criteria:

- local setup works
- API, worker, web all run
- repo structure clear + documented

## Phase 1 — Canonical DB foundation

Goal: first real persistence layer.

Deliverables:

- SQLAlchemy base + models
- Alembic setup
- initial migrations
- canonical tables for `games`, `publications`, `reviews`
- DB session wiring in backend

Exit criteria:

- schema creates locally
- migrations run clean
- app code reads/writes core entities

## Phase 2 — First real source ingestion

Goal: ingest one real review source end-to-end.

Deliverables:

- one source selected + documented
- scraper or ingestion adapter
- extraction of title, URL, score/verdict, game-identifying data
- structured output
- source-specific parsing where needed

Exit criteria:

- one source ingestable repeatedly + reliably
- extracted records inspectable
- ingestion path debuggable

## Phase 3 — Normalisation and canonical mapping

Goal: convert raw source data into canonical app data.

Deliverables:

- score normalisation for supported formats
- publication resolution
- conservative game entity resolution
- handling of unresolved/scoreless cases
- canonical rows written to PostgreSQL

Exit criteria:

- one real source lands in canonical tables
- supported score types normalise correctly
- unresolved cases don't silently corrupt data

## Phase 4 — First useful API surface

Goal: expose meaningful product data via backend.

Deliverables:

- `GET /games`
- `GET /games/{slug}` or equivalent canonical detail route
- associated reviews on game detail
- response shape suitable for frontend
- simple error handling conventions

Exit criteria:

- frontend fetches + renders real game data
- payloads simple + coherent
- routes reflect canonical product entities

## Phase 5 — First useful frontend pages

Goal: render real, browseable critic aggregation experience.

Deliverables:

- homepage or browse page
- game detail page
- critic reviews + original source links
- normalised aggregate score where available
- basic rankings/listing page

Exit criteria:

- product feels like real critic aggregation site
- small set of real games browseable
- pages legible, content-oriented, useful

## Phase 6 — Stabilisation and expansion

Goal: make first slice credible + easier to extend.

Deliverables:

- improve scraper robustness
- refine score normalisation coverage
- improve entity resolution
- tests in highest-risk areas
- improve docs + contributor guidance
- optionally add second source if it doesn't destabilise first slice

Exit criteria:

- vertical slice robust enough for demo or soft launch
- common failure modes easier to detect
- codebase stays understandable

## Defer until later unless clearly needed

Lower priority:

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

Task doesn't clearly support current or next phase → defer.