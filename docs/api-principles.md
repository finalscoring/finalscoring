# API principles

This document defines the intended API style for Final Scoring.

The goal is to keep the backend interface simple, stable, and easy for both humans and coding agents to reason about.

## General direction

The API should start as a straightforward REST API.

It should expose the product’s canonical entities and derived views without introducing unnecessary protocol or schema complexity.

## API goals

The API should be:

- easy to read
- easy to debug
- easy to evolve
- well aligned with the product model
- boring in a good way

## Canonical orientation

The API should expose canonical application entities, not raw scraped payloads.

Examples of first-class concepts:

- games
- publications
- reviews
- rankings or browse surfaces derived from those entities

## Keep the API thin

Route handlers should mainly:

- validate inputs
- load or invoke shared business logic
- shape responses
- return clear errors

They should not become the place where ingestion, scoring, or matching logic lives.

## REST-first

The backend should begin with REST.

Reasons:

- simpler to implement
- easier to inspect manually
- suitable for current product needs
- avoids early GraphQL complexity

GraphQL should not be introduced unless there is clear real pressure that REST cannot handle cleanly.

## URL design

Prefer stable, descriptive resource-oriented routes.

Examples of likely patterns:

- `/games`
- `/games/{slug}`
- `/publications`
- `/publications/{slug}`
- `/rankings`

Prefer canonical slugs for public-facing lookup where practical.

## Response design

Responses should be:

- explicit
- predictable
- minimally surprising
- not overloaded with hidden semantics

Prefer stable field names over clever compression.

Do not prematurely optimise payloads for theoretical future clients.

## Pagination

List endpoints should use a simple and explicit pagination model once needed.

A consistent convention should be chosen and applied across endpoints rather than reinvented per route.

For MVP, a simple offset/limit or page-based scheme is acceptable.

## Filtering and sorting

Filtering and sorting should be introduced incrementally and only where they improve real product surfaces.

Examples that are likely useful:

- sort games by aggregate critic score
- sort by review count
- filter to scored vs unscored availability where relevant

Do not build an ultra-generic filtering DSL in MVP.

## Errors

Error responses should be clear and consistent.

The API should avoid:

- vague 500 errors for known user-facing failure modes
- inconsistent error shapes
- hidden null semantics where a clear error is better

A small standard error response structure is preferable.

## Public vs internal endpoints

Early on, it is acceptable for the same API to serve both the web frontend and basic internal needs.

However:

- internal maintenance actions should not casually leak into public routes
- operational or ingestion endpoints should remain clearly separated if exposed at all

## Derived values

The API may expose derived values such as:

- normalised aggregate score
- number of reviews
- list ordering data

But these should be clearly defined and sourced from shared backend logic, not ad hoc route-level calculations.

## Versioning

Do not introduce formal API versioning too early unless there is a real compatibility problem.

Early-stage product iteration is better served by keeping the API small and coherent.

## Security and auth

End-user authentication is not an MVP goal.

Therefore, the API should not be shaped around user-specific sessions or personalised behaviour.

If internal-only administrative actions are later needed, they should be added deliberately rather than assumed from the start.

## Documentation expectation

When API behaviour becomes meaningful to product usage, it should be documented concretely.

Good documentation should include:

- route purpose
- request parameters
- response shapes
- sorting/filtering semantics where relevant
- edge cases for scoreless or unresolved data

## Rule of thumb

If an API design decision makes the backend feel more like a generic framework and less like a clear interface for Final Scoring, it is probably the wrong direction for MVP.
