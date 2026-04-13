# Current priority

## Current phase

The project is currently in **Phase 1 — Canonical DB foundation**.

See `docs/roadmap.md` for the broader sequence, but contributors and coding agents should treat Phase 1 as the active focus until its exit criteria are met.

## Current objective

Build the first real persistence layer for Final Scoring.

This means establishing the canonical database foundation that the rest of the product will depend on.

## Definition of done for the current priority

The current priority is complete when all of the following are true:

- SQLAlchemy base and core models exist for `Game`, `Publication`, and `Review`
- Alembic is set up and the initial migration is committed
- the schema can be created locally from migrations
- backend code can create a database session cleanly
- the API can read from the canonical tables without ad hoc schema setup
- the structure is documented and consistent with the existing repo layout

## In-scope work

The following are in scope right now:

- SQLAlchemy model definitions
- DB session setup
- Alembic configuration
- initial migration creation
- wiring database access into backend code where needed
- small supporting refactors required to make the DB foundation coherent
- tests for the DB foundation where they materially reduce risk

## Explicitly out of scope right now

Unless needed to complete the current objective, do **not** prioritise:

- onboarding a real review source
- broad scraping work
- sophisticated score normalisation
- advanced entity resolution
- complex API design beyond what is needed to support the DB foundation
- frontend feature work beyond keeping the existing shell functional
- user accounts, recommendations, search, admin tooling, or other non-MVP features
- new infrastructure such as queues, workflow systems, microservices, or GraphQL

## Order of attack

Contributors and coding agents should generally proceed in this order:

1. define or refine the canonical SQLAlchemy models
2. establish DB session and engine wiring
3. set up Alembic properly
4. create and verify the initial migration
5. ensure the backend can use the schema cleanly
6. add or update tests for the most important DB behaviour

## Constraints and expectations

- keep the API thin
- keep business logic out of route handlers
- keep canonical logic in shared Python code under `packages/py/finalscoring`
- prefer straightforward, portable solutions
- do not introduce speculative abstractions or infrastructure
- preserve already documented project decisions unless there is a concrete reason to revisit them

## What to do after this phase is complete

Once Phase 1 exit criteria are met, the next priority should be **Phase 2 — First real source ingestion**.

That next phase should begin with selecting and documenting one real source, then implementing one end-to-end ingestion path rather than partial support for many sources.

## Rule of thumb

If a proposed task does not clearly help Final Scoring complete the canonical DB foundation, it should usually be deferred.
