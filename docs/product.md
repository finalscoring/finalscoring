# Product overview

## What Final Scoring is

Final Scoring: board game criticism + review aggregation platform.

Collects published critical opinions, normalises into comparable structure, presents for understanding reception.

Core idea: Metacritic for board games. Focus on critical reception — not user ratings, collections, trading, forums, or rules references.

## Who it is for

For people wanting to understand critic regard before buying, playing, covering, or investigating.

Includes:

- hobby board gamers researching games
- journalists, reviewers, content creators
- publishers and designers tracking reception
- analytically minded readers wanting higher-level sentiment view

## The user problem

Board game criticism scattered across many sites, blogs, channels, publications. Hard to answer:

- Which games most highly regarded by critics?
- How strong is consensus around a game?
- Which publications reviewed a game?
- Are critics split or broadly aligned?
- How does one game compare with another on critical reception?

Users currently must manually search multiple sources and reconcile inconsistent score scales and formats.

## Product principles

### 1. Critical opinion first

Centre published critical coverage, not crowd sentiment.

### 2. Credibility over quantity

Smaller set of well-understood, well-normalised sources beats broad low-quality coverage.

### 3. Transparency

Users see where aggregated scores come from and which reviews contributed.

### 4. Simplicity

First version: clear and legible, not maximal feature set.

### 5. Extensibility

Data model and pipeline leave room for richer analysis later — critic weighting, publication quality signals, excerpts, topic tagging, disagreement measures.

## Core product entities

First version revolves around three core entities:

- `Game`
- `Publication`
- `Review`

`Critic` entity may be added later if useful to distinguish publications from individual authors.

## MVP goal

MVP proves Final Scoring can ingest, normalise, store, and present board game critic reviews in a way already useful to readers.

MVP not trying to be complete. Trying to validate concept with coherent, credible first slice.

User should be able to:

- browse at least small set of games
- open a game page
- see which publications reviewed the game
- see original review links and source score representations where available
- see normalised critic summary enabling cross-source comparison

## Required capabilities

### 1. Canonical data model

Canonical representation of games, publications, reviews in PostgreSQL, queryable by application.

### 2. At least one real source ingestion path

Ingest review data from at least one real publication — scraping, parsing to structured form, canonical mapping, database storage.

### 3. Score normalisation

Support normalised comparable score for scored reviews where feasible. Pipeline handles at least a few common scoring schemes.

### 4. Useful API endpoints

Small coherent REST API: list of games, single game with critic reviews, publication info for display.

### 5. Usable frontend pages

Minimum: homepage or browse page, listing or rankings page, game detail page. Clear, legible, content-oriented.

## Strongly preferred capabilities

Not strictly mandatory but highly desirable if they don't significantly delay delivery:

- more than one review source
- basic publication pages
- simple sorting or filtering on game lists
- review count alongside aggregate score
- clear indication when review is unscored

## Explicit non-goals

MVP excludes:

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

MVP may:

- support only one or few review sources
- support only subset of scoring schemes initially
- use deterministic matching before advanced entity resolution
- use simple rankings and aggregate formulas before nuanced weighting
- defer critic-level modelling if publication-level is enough
- keep visual design simple as long as pages are clear and usable

## Quality bar

Feature good enough for MVP when: understandable, reasonably reliable, easy to inspect and debug, not obviously misleading, consistent with core concept.

## Launch criteria

MVP ready for initial launch or external demo when all true:

- at least one real source ingested end-to-end
- canonical game, publication, review data in database
- score normalisation functioning for supported source types
- frontend renders game pages with meaningful critic information
- system supports small catalogue without manual breakage
- product feels like board game critic aggregation site, not code demo

## Likely user journeys

### Researching a game

User lands on game page, sees aggregated critic score, review count, contributing publications, underlying reviews and original scores where available.

### Browsing highly rated games

User visits rankings or browse page, explores games sorted by critic score, review count, or related summary metrics.

### Comparing reception

User compares multiple games by critic scores, review counts, source coverage, score spread.

## What can wait until later

- richer search
- author / critic entities
- sophisticated publication or critic weighting
- disagreement metrics and richer analytics
- admin tooling
- large-scale source onboarding frameworks
- polished visual design systems
- hosting and performance optimisation
- large automated regression suites outside highest-risk areas

## Contributor rule of thumb

Work belongs in MVP if:

1. directly improves core critic aggregation experience?
2. necessary for first real end-to-end product slice?
3. MVP meaningfully worse without it?

Mostly no → post-MVP.