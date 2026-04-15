# Testing strategy

Early-stage project. Direct effort where mistakes cost most.

## Main principle

Prioritise product-critical logic and failure-prone transforms. No blanket coverage for its own sake.

## Highest-priority test areas

- score normalisation
- source parsing and extraction
- entity resolution
- canonical ingestion logic
- API behaviour for core product endpoints

Silent product errors live here.

## Lower-priority areas in MVP

- pure UI snapshot breadth
- highly abstract utility tests
- exhaustive framework wiring tests
- full end-to-end browser suites
- over-elaborate mocking infrastructure

## Python testing priorities

### 1. Domain and transformation logic

Highest priority.

Examples:

- score mapping from source formats
- review canonicalisation
- duplicate handling behaviour
- unresolved entity handling
- source inclusion/exclusion logic where encoded in code

### 2. Parser and extractor tests

Per source: validate real extraction against representative HTML or source fixtures. Detect breakage when source structure changes.

### 3. API tests

Core routes need integration-style tests verifying:

- status codes
- response shapes
- presence of expected fields
- handling of missing entities or empty data

### 4. Database-backed tests

Where business logic depends on persistence, use DB-backed tests selectively and deliberately.

## Frontend testing priorities

Keep lighter than backend/data testing early.

Useful early:

- rendering of core game page data
- basic behaviour of important data-driven components
- handling of missing or unscored review data

Don't over-invest in frontend test infrastructure before product surfaces stabilise.

## Fixture strategy

Fixtures must be easy to inspect and maintain.

Good candidates:

- source HTML fragments or saved review pages
- structured extracted source records
- canonical example games/publications/reviews

Avoid fixtures that are overly huge, hard to understand, or detached from real product behaviour.

## Test style preferences

Prefer: direct, concrete, readable, close to protected product behaviour.

Avoid overly abstract or meta-programmed test machinery unless clearly justified.

## Regression philosophy

Bug found in parsing, normalisation, matching, duplicate handling, or API response semantics → add regression test where practical.

Quiet recurrence in these areas is costly.

## Suggested testing order for MVP

1. score normalisation tests
2. source parser tests
3. entity resolution tests
4. ingestion pipeline tests
5. API route tests
6. selective frontend rendering tests

## Rule of thumb

Logic that can silently distort critic reception data deserves stronger tests than code affecting only internal neatness.