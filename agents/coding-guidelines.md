# Coding guidelines

These guidelines are intentionally written to be useful for any coding agent or assistant working in this repository, not only Cursor.

## General principles

- prefer simple and maintainable solutions
- avoid premature abstraction
- prefer explicit code over clever code
- optimise for readability and ease of modification
- make small, well-scoped changes unless a larger refactor is clearly justified
- do not introduce new frameworks or infrastructure without a concrete reason

## Python guidelines

### Language and style

- use Python 3.12+
- use modern type annotations in function signatures
- prefer straightforward functions and classes over elaborate indirection
- keep modules focused on a clear responsibility
- prefer descriptive names over short clever ones

### Project conventions

- keep domain and business logic in `packages/py/finalscoring`
- keep FastAPI route handlers thin
- keep worker commands small and explicit
- prefer Polars for tabular processing tasks
- use Pydantic where structured validation is useful
- use SQLAlchemy and Alembic for database work

### Testing

- add or update tests when changing non-trivial logic
- prioritise tests for domain logic, score normalisation, ingestion, and API behaviour
- prefer clear test cases over overly abstract test machinery

## Frontend guidelines

### TypeScript and React

- keep components simple and focused
- prefer clear data flow over unnecessary indirection
- avoid state complexity unless it is clearly needed
- keep API integration explicit and easy to trace
- prefer server-friendly, content-oriented page design for the current stage of the product

### Product considerations

- the frontend should support a content-heavy, browseable, indexable product
- do not optimise prematurely for highly dynamic application behaviour
- prioritise clarity of presentation over flashy interaction patterns

## Architecture and boundaries

- preserve the monorepo structure unless there is a strong reason to change it
- do not create new top-level packages, services, or subsystems casually
- prefer shared logic over duplicated logic, but do not over-abstract too early
- design changes should remain portable and not tie the codebase deeply to one hosting provider
- avoid microservices, queues, or workflow frameworks unless they solve a real present problem

## Data and ingestion

- preserve raw source truth where useful, especially URLs and original score formats
- keep canonical entities distinct from raw source data
- make score normalisation explicit and traceable
- prefer simple ingestion pipelines that are easy to debug
- do not commit raw scraped datasets into git

## Documentation expectations

- update relevant docs in `docs/` when behaviour, architecture, or scope changes materially
- keep explanations concrete and operational rather than vague
- when adding a new pattern, document it if future contributors or agents would otherwise need to infer it

## What to avoid

- speculative architecture
- framework-driven complexity
- hidden magic in configuration or dependency injection
- spreading business logic across route handlers, scripts, and frontend code
- broad refactors with weak product justification

## Preferred change style

When implementing a change:

1. understand the local context first
2. make the smallest coherent change that solves the problem
3. keep naming and structure consistent with the existing codebase
4. add or update tests when appropriate
5. update docs when the change affects project understanding
