# Testing strategy

This document defines how testing should be approached in Final Scoring.

The project is early-stage, so testing effort should be directed where mistakes are most costly.

## Main principle

Prioritise tests for product-critical logic and failure-prone transformation steps.

Do not chase blanket coverage for its own sake.

## Highest-priority test areas

The most important areas to test early are:

- score normalisation
- source parsing and extraction
- entity resolution
- canonical ingestion logic
- API behaviour for core product endpoints

These are the parts most likely to produce silent product errors if they are wrong.

## Lower-priority areas in MVP

The following can usually be lighter in the earliest stage:

- pure UI snapshot breadth
- highly abstract utility tests
- exhaustive framework wiring tests
- full end-to-end browser suites
- over-elaborate mocking infrastructure

## Python testing priorities

### 1. Domain and transformation logic

This should be the highest priority.

Examples:

- score mapping from source formats
- review canonicalisation
- duplicate handling behaviour
- unresolved entity handling
- source inclusion/exclusion logic where encoded in code

### 2. Parser and extractor tests

For each source, prefer tests that validate real extraction expectations against representative HTML or source fixtures.

These tests should help detect breakage when a source structure changes.

### 3. API tests

Core API routes should have integration-style tests that verify:

- status codes
- response shapes
- presence of expected fields
- handling of missing entities or empty data

### 4. Database-backed tests

Where business logic depends on persistence behaviour, use database-backed tests selectively and deliberately.

## Frontend testing priorities

Early frontend testing can remain lighter than backend/data testing.

Useful early frontend tests may include:

- rendering of core game page data
- basic behaviour of important data-driven components
- handling of missing or unscored review data

But the project should not spend disproportionate effort on frontend test infrastructure before the product surfaces stabilise.

## Fixture strategy

Fixtures should be easy to inspect and maintain.

Good candidates:

- source HTML fragments or saved review pages
- structured extracted source records
- canonical example games/publications/reviews

Avoid fixtures that are:

- overly huge
- hard to understand
- detached from real product behaviour

## Test style preferences

Prefer tests that are:

- direct
- concrete
- readable
- close to the product behaviour being protected

Avoid overly abstract or meta-programmed test machinery unless it is clearly justified.

## Regression philosophy

When a bug is found in:

- parsing
- normalisation
- matching
- duplicate handling
- API response semantics

add a regression test where practical.

These are precisely the areas where quiet recurrence is costly.

## Suggested testing order for MVP

1. score normalisation tests
2. source parser tests
3. entity resolution tests
4. ingestion pipeline tests
5. API route tests
6. selective frontend rendering tests

## Rule of thumb

If a piece of logic can silently distort critic reception data, it deserves stronger tests than a piece of code that only affects internal neatness.
