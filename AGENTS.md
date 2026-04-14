# Agent handoff guide

This repository is intended to be workable by coding agents, but agents should optimise for correctness, clarity, and scope discipline rather than speed alone.

## Read this first

Before making substantial changes, read these documents:

- `docs/current-priority.md`
- `docs/product.md`
- `docs/architecture.md`
- `docs/data-model.md`
- `docs/development.md`
- `docs/decisions.md`
- `docs/source-strategy.md`
- `docs/score-normalisation.md`
- `docs/entity-resolution.md`

Then consult task-specific docs such as:

- `docs/roadmap.md`
- `docs/api-principles.md`
- `docs/frontend-principles.md`
- `docs/testing-strategy.md`

## Project summary

Final Scoring is a board game criticism and review aggregation platform.

The product goal is to collect published critical opinions about board games, normalise them into a comparable structure, and present them in a way that helps readers understand how games are being received.

This is not a general board game community product. The MVP focus is critic aggregation, not user ratings, accounts, recommendations, social features, or collection management.

## Current stage

The project is early.

Immediate implementation focus is **Phase 1 — Canonical DB foundation** (`docs/current-priority.md`). The broader goal is a coherent MVP vertical slice across:

- source ingestion
- canonical data modelling
- score normalisation
- backend API
- frontend rendering

## Stack, layout, and local workflow

Monorepo (`finalscoring`): FastAPI API, worker CLI, Next.js frontend, shared Python package under `packages/py/finalscoring`. Toolchain and install/run commands: **`docs/development.md`**. Repository shape, component roles, and architectural principles: **`docs/architecture.md`**.

## High-level working rules

- Follow **`docs/architecture.md`** (thin API, simple worker, domain logic in the shared package, avoid premature distribution).
- Preserve **`docs/decisions.md`**; do not silently invent product rules that are not documented.
- Prefer conservative, explicit behaviour over speculative automation; avoid premature abstraction.

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

## Use the documented decisions

The repository contains explicit project decisions in `docs/decisions.md`. Do not casually reopen settled questions such as:

- monorepo vs multi-repo
- Python vs other backend languages
- FastAPI vs another backend framework
- critic aggregation focus vs broader social/community scope
- REST vs GraphQL for MVP
- simple worker CLI vs heavy orchestration system

If a decision truly needs revisiting, the reason should be concrete and implementation-driven.

## Prefer vertical progress

The project benefits most from end-to-end progress over building disconnected subsystems in parallel.

Prefer:

- ingesting one real source fully rather than half-building support for five
- rendering one real game page well rather than scaffolding many empty surfaces
- implementing one clear API flow rather than a generic but unused framework

## Good delivery shape

A good change usually has these qualities:

- solves a real current problem
- fits the MVP scope
- is understandable without heroic context reconstruction
- comes with tests when the logic matters
- updates docs when assumptions changed

## Rule of thumb

When in doubt, choose the option that:

1. helps ship the MVP
2. keeps the codebase understandable
3. preserves room for later extension
4. avoids unnecessary infrastructure or abstraction
