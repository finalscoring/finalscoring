# Product overview

## What Final Scoring is

Final Scoring is a board game criticism and review aggregation platform.

Its purpose is to collect published critical opinions about board games, normalise them into a comparable structure, and present them in a way that helps readers understand how games are being received.

The core idea is closer to Metacritic for board games than to a general board game community site. The focus is on critical reception rather than user ratings, collections, trading, forum discussion, or rules references.

## Who it is for

Final Scoring is primarily for people who want to understand how a board game is regarded by critics and reviewers before deciding whether to buy, play, cover, or investigate it further.

This includes:

- hobby board gamers researching games
- journalists, reviewers, and content creators
- publishers and designers tracking reception
- analytically minded readers who want a higher-level view of review sentiment

## The user problem

Board game criticism is scattered across many sites, blogs, channels, and publications. It is hard to answer simple questions such as:

- Which games are most highly regarded by critics?
- How strong is the consensus around a game?
- Which publications reviewed a game?
- Are critics split or broadly aligned?
- How does one game compare with another on critical reception?

Today, users often need to manually search multiple sources and reconcile inconsistent score scales and formats.

## Product principles

### 1. Critical opinion first

The product should centre published critical coverage, not crowd sentiment.

### 2. Credibility over quantity

A smaller set of well-understood, well-normalised sources is better than broad low-quality coverage.

### 3. Transparency

Users should be able to see where aggregated scores come from and which reviews contributed to them.

### 4. Simplicity

The first version should aim for a clear and legible product, not a maximal feature set.

### 5. Extensibility

The data model and pipeline should leave room for richer analysis later, such as critic weighting, publication quality signals, excerpts, topic tagging, or disagreement measures.

## Core product entities

The first version should revolve around three core entities:

- `Game`
- `Publication`
- `Review`

A `Critic` entity may be added later if it becomes useful to distinguish publications from individual authors.

## MVP goal

The MVP should prove that Final Scoring can ingest, normalise, store, and present board game critic reviews in a way that is already useful to readers.

The MVP is not trying to be complete. It is trying to validate the product concept with a coherent and credible first slice.

A user should be able to visit Final Scoring and:

- browse at least a small set of games
- open a game page
- see which publications reviewed the game
- see the original review links and source score representations where available
- see a normalised critic summary that makes cross-source comparison easier

## Required capabilities

### 1. Canonical data model

The system must have a canonical representation of games, publications, and reviews in PostgreSQL, queryable by the application.

### 2. At least one real source ingestion path

The system must ingest review data from at least one real publication or source, including scraping, parsing into a structured form, canonical mapping, and database storage.

### 3. Score normalisation

The system must support a normalised comparable score for scored reviews where feasible. The pipeline must clearly handle at least a few common scoring schemes.

### 4. Useful API endpoints

A small but coherent REST API supporting at minimum: a list of games, a single game with its associated critic reviews, and publication information for display.

### 5. Usable frontend pages

At minimum: a homepage or browse page, a listing or rankings-style page, and a game detail page. Pages should be clear, legible, and content-oriented.

## Strongly preferred capabilities

These are not strictly mandatory but are highly desirable if they do not significantly delay delivery:

- more than one review source
- basic publication pages
- simple sorting or filtering on game lists
- display of review count alongside aggregate score
- clear indication when a review is unscored

## Explicit non-goals

The MVP should not include:

- user accounts or authentication
- user-submitted ratings or reviews
- recommendation systems
- social or community features
- collection or marketplace functionality
- heavy personalisation
- admin platform
- heavy workflow orchestration
- dedicated search engine
- GraphQL
- microservices

## Acceptable shortcuts

The MVP may:

- support only one or a few review sources
- support only a subset of scoring schemes initially
- use straightforward deterministic matching before more advanced entity resolution exists
- use simple rankings and aggregate formulas before more nuanced weighting exists
- defer critic-level modelling if publication-level modelling is enough
- keep visual design simple as long as pages are clear and usable

## Quality bar

A feature is good enough for MVP when it is understandable, reasonably reliable, easy to inspect and debug, not obviously misleading, and consistent with the project's core concept.

## Launch criteria

The MVP can be considered ready for an initial launch or external demo when all of the following are true:

- at least one real source is ingested end-to-end
- canonical game, publication, and review data exists in the database
- score normalisation is functioning for the supported source types
- the frontend can render game pages with meaningful critic information
- the system can support a small catalogue without manual breakage
- the product already feels like a board game critic aggregation site rather than a code demo

## Likely user journeys

### Researching a game

A user lands on a game page and sees the aggregated critic score, the number of critic reviews, the contributing publications, and the underlying reviews and original scores where available.

### Browsing highly rated games

A user visits a rankings or browse page and explores games sorted by critic score, review count, or related summary metrics.

### Comparing reception

A user compares multiple games by looking at their critic scores, review counts, source coverage, and score spread.

## What can wait until later

- richer search
- author / critic entities
- sophisticated weighting of publications or critics
- disagreement metrics and richer analytics
- admin tooling
- large-scale source onboarding frameworks
- polished visual design systems
- hosting optimisation
- performance optimisation beyond obvious bottlenecks
- large automated regression suites outside the highest-risk areas

## Contributor rule of thumb

When deciding whether work belongs in MVP, ask:

1. does this directly improve the core critic aggregation experience?
2. is it necessary for the first real end-to-end product slice?
3. would the MVP be meaningfully worse without it?

If the answer is mostly no, it is probably post-MVP work.
