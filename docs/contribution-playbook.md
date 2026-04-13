# Contribution playbook

This document explains how contributors and coding agents should approach work in the Final Scoring repository.

It is intended to reduce unnecessary refactors, context loss, and speculative implementation.

## First rule: understand before changing

Before making non-trivial changes:

1. read the relevant local code
2. read the relevant docs
3. identify whether the task is product-facing, ingestion-facing, data-model-facing, or infrastructure-facing
4. confirm that the proposed change fits the MVP direction

Do not start by inventing architecture.

## Use the documented decisions

The repository already contains explicit project decisions.

Contributors should not casually reopen settled questions such as:

- monorepo vs multi-repo
- Python vs other backend languages
- FastAPI vs another backend framework
- critic aggregation focus vs broader social/community scope
- REST vs GraphQL for MVP
- simple worker CLI vs heavy orchestration system

If a decision truly needs revisiting, the reason should be concrete and implementation-driven.

## Prefer vertical progress

The project benefits most from end-to-end progress.

Good examples:

- ingest one real source fully rather than half-building support for five
- render one real game page well rather than scaffolding many empty surfaces
- implement one clear API flow rather than a generic but unused framework

## Make the smallest coherent change

When solving a task:

- avoid broad refactors unless they are clearly necessary
- do not rewrite nearby code just because it could be cleaner
- preserve naming and structural consistency
- keep the scope of a change legible

## Be conservative with product semantics

Do not silently invent:

- review inclusion rules
- score mappings
- entity resolution behaviour
- edition collapse rules
- browse ranking semantics

If a product rule is unclear, prefer:

- conservative handling
- unresolved states
- explicit documentation
- clear follow-up notes

## Keep business logic in the right place

Preferred boundaries:

- API routes should stay thin
- shared domain and transformation logic should live in `packages/py/finalscoring`
- worker tasks should orchestrate explicit steps rather than hide complex logic in scripts
- frontend should focus on rendering and interaction, not duplicate backend business logic

## Testing expectations

When changing important logic:

- add or update tests
- protect against regression where practical
- prefer direct, readable test cases

Testing priority should be highest for:

- parsing
- normalisation
- matching
- ingestion
- API behaviour

## Documentation expectations

Update docs when changes materially affect:

- project understanding
- product semantics
- architecture
- contributor expectations
- source handling or score handling rules

Good code changes with stale docs still create confusion.

## What to avoid

Avoid:

- speculative architecture
- unnecessary framework adoption
- hidden magic in configuration
- scattered product logic across unrelated layers
- broad “cleanup” refactors with weak product value
- pretending uncertain data is certain

## Good delivery shape

A good change usually has these qualities:

- solves a real current problem
- fits the MVP scope
- is understandable without heroic context reconstruction
- comes with tests when the logic matters
- updates docs when assumptions changed

## Final rule of thumb

The best contribution is usually not the most ambitious one.

It is the one that moves Final Scoring toward a real, credible critic aggregation product while keeping the repo easy to understand and extend.
