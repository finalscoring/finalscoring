# Agent handoff guide

Repo workable by coding agents. Optimise for correctness, clarity, scope — not speed alone.

## Read this first

Before substantial changes, read:

- `docs/current-priority.md`
- `docs/product.md`
- `docs/architecture.md`
- `docs/data-model.md`
- `docs/development.md`
- `docs/decisions.md`
- `docs/source-strategy.md`
- `docs/score-normalisation.md`
- `docs/entity-resolution.md`

Then task-specific docs:

- `docs/roadmap.md`
- `docs/api-principles.md`
- `docs/frontend-principles.md`
- `docs/testing-strategy.md`

## Project summary

Final Scoring = board game criticism + review aggregation platform.

Collect published critic opinions, normalise into comparable structure, present so readers understand reception.

Not a community product. MVP = critic aggregation. No user ratings, accounts, recommendations, social, collection management.

## Current stage

Early. Immediate focus: **Phase 1 — Canonical DB foundation** (`docs/current-priority.md`). Goal: coherent MVP vertical slice across source ingestion, canonical data modelling, score normalisation, backend API, frontend rendering.

## Stack, layout, and local workflow

Monorepo (`finalscoring`): FastAPI API, worker CLI, Next.js frontend, shared Python package under `packages/py/finalscoring`. Toolchain + install/run: **`docs/development.md`**. Repo shape, component roles, architectural principles: **`docs/architecture.md`**.

## High-level working rules

- Follow **`docs/architecture.md`** (thin API, simple worker, domain logic in shared package, no premature distribution).
- Preserve **`docs/decisions.md`**; don't silently invent undocumented product rules.
- Conservative, explicit behaviour over speculative automation; no premature abstraction.

## Expected change style

1. Understand local context first
2. Read relevant docs before changing code
3. Smallest coherent change that solves actual problem
4. Keep naming + structure consistent with existing repo
5. Add/update tests when appropriate
6. Update docs when behaviour, assumptions, or architecture change materially

## Special caution areas

Extra care in:

- source inclusion policy
- score normalisation
- entity resolution
- edition vs base game distinctions
- scoreless reviews
- duplicate review handling

Uncertain here → prefer explicitness and conservative behaviour.

## What not to optimise for yet

Don't prioritise:

- abstract architecture neatness over shipping
- generic frameworks for everything
- broad source coverage before first source works well
- complex frontend state systems
- speculative scalability work
- highly dynamic behaviour not yet needed

## Use the documented decisions

Explicit decisions in `docs/decisions.md`. Don't reopen settled questions:

- monorepo vs multi-repo
- Python vs other backend languages
- FastAPI vs another backend framework
- critic aggregation focus vs broader social/community scope
- REST vs GraphQL for MVP
- simple worker CLI vs heavy orchestration

Need to revisit? Reason must be concrete and implementation-driven.

## Prefer vertical progress

End-to-end progress beats disconnected subsystems.

Prefer:

- one real source ingested fully over half-building five
- one real game page rendered well over many empty surfaces
- one clear API flow over generic unused framework

## Good delivery shape

- solves real current problem
- fits MVP scope
- understandable without heroic context reconstruction
- tests when logic matters
- docs updated when assumptions changed

## Rule of thumb

When in doubt, pick option that:

1. helps ship MVP
2. keeps codebase understandable
3. preserves room for later extension
4. avoids unnecessary infrastructure or abstraction