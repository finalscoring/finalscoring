# API principles

Defines intended API style for Final Scoring. Goal: simple, stable, easy for humans and agents to reason about.

## General direction

Straightforward REST API. Expose canonical entities and derived views. No unnecessary protocol complexity.

## API goals

- easy to read
- easy to debug
- easy to evolve
- well aligned with product model
- boring in a good way

## Canonical orientation

Expose canonical application entities, not raw scraped payloads.

First-class concepts:

- games
- publications
- reviews
- rankings or browse surfaces derived from those entities

## Keep the API thin

Route handlers should:

- validate inputs
- load or invoke shared business logic
- shape responses
- return clear errors

Not the place for ingestion, scoring, or matching logic.

## REST-first

Start with REST.

Reasons:

- simpler to implement
- easier to inspect manually
- suitable for current product needs
- avoids early GraphQL complexity

No GraphQL unless clear real pressure REST can't handle cleanly.

## URL design

Stable, descriptive resource-oriented routes.

Likely patterns:

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

Stable field names over clever compression. No premature payload optimisation for theoretical future clients.

## Pagination

List endpoints use simple, explicit pagination once needed. One consistent convention across endpoints. For MVP, offset/limit or page-based scheme acceptable.

## Filtering and sorting

Introduce incrementally, only where they improve real product surfaces.

Likely useful:

- sort games by aggregate critic score
- sort by review count
- filter scored vs unscored availability where relevant

No ultra-generic filtering DSL in MVP.

## Errors

Clear and consistent error responses.

Avoid:

- vague 500s for known user-facing failures
- inconsistent error shapes
- hidden null semantics where clear error is better

Small standard error response structure preferred.

## Public vs internal endpoints

Same API can serve web frontend and basic internal needs early on.

But:

- internal maintenance actions must not leak into public routes
- operational or ingestion endpoints stay clearly separated if exposed

## Derived values

API may expose:

- normalised aggregate score
- number of reviews
- list ordering data

Must be clearly defined, sourced from shared backend logic — not ad hoc route-level calculations.

## Versioning

No formal API versioning until real compatibility problem exists. Keep API small and coherent during early iteration.

## Security and auth

End-user auth not MVP goal. No user-specific sessions or personalised behaviour. Internal admin actions added deliberately if needed, not assumed from start.

## Documentation expectation

Document API behaviour concretely when it becomes meaningful to product usage.

Include:

- route purpose
- request parameters
- response shapes
- sorting/filtering semantics where relevant
- edge cases for scoreless or unresolved data

## Rule of thumb

If design makes backend feel like generic framework instead of clear interface for Final Scoring — wrong direction for MVP.