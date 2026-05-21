# Current priority

## Current phase

Project in **Phase 1 — Canonical DB foundation**.

See `docs/roadmap.md` for broader sequence. Treat Phase 1 as active focus until exit criteria met.

## Current objective

Build first real persistence layer for Final Scoring. Establish canonical DB foundation rest of product depends on.

## Definition of done for the current priority

Complete when all true:

- SQLAlchemy base and core models exist for `Game`, `Publication`, `Review`
- Alembic set up, initial migration committed
- schema creatable locally from migrations
- backend can create DB session cleanly
- API reads from canonical tables without ad hoc schema setup
- structure documented, consistent with existing repo layout

## In-scope work

- SQLAlchemy model definitions
- DB session setup
- Alembic configuration
- initial migration creation
- wiring DB access into backend where needed
- small supporting refactors for coherent DB foundation
- tests where they materially reduce risk

## Explicitly out of scope right now

Do **not** prioritise unless needed for current objective:

- onboarding real review source
- broad scraping work
- sophisticated score normalisation
- advanced entity resolution
- complex API design beyond DB foundation support
- frontend feature work beyond keeping existing shell functional
- user accounts, recommendations, search, admin tooling, other non-MVP features
- new infrastructure: queues, workflow systems, microservices, GraphQL

## Order of attack

1. define or refine canonical SQLAlchemy models
2. establish DB session and engine wiring
3. set up Alembic
4. create and verify initial migration
5. ensure backend uses schema cleanly
6. add/update tests for most important DB behaviour

## Constraints and expectations

- keep API thin
- keep business logic out of route handlers
- keep canonical logic in shared Python under `packages/py/finalscoring`
- prefer straightforward, portable solutions
- no speculative abstractions or infrastructure
- preserve documented project decisions unless concrete reason to revisit

## What to do after this phase is complete

Phase 1 done → next: **Phase 2 — First real source ingestion**. Start by selecting and documenting one real source, then implement one end-to-end ingestion path.

## Rule of thumb

Task doesn't clearly help complete canonical DB foundation → defer.