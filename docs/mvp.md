# MVP definition

This document defines the minimum viable product for Final Scoring.

Its purpose is to prevent scope creep and to give contributors and coding agents a concrete definition of what must exist before the first meaningful version can be considered done.

## MVP goal

The MVP should prove that Final Scoring can ingest, normalise, store, and present board game critic reviews in a way that is already useful to readers.

The MVP is not trying to be complete. It is trying to validate the product concept with a coherent and credible first slice.

## Core MVP outcome

A user should be able to visit Final Scoring and:

- browse at least a small set of games
- open a game page
- see which publications reviewed the game
- see the original review links and source score representations where available
- see a normalised critic summary that makes cross-source comparison easier

## Required capabilities

### 1. Canonical data model

The system must have a canonical representation of:

- games
- publications
- reviews

This data must live in PostgreSQL and be queryable by the application.

### 2. At least one real source ingestion path

The system must ingest review data from at least one real publication or source.

This includes:

- scraping or otherwise collecting source data
- parsing it into a structured form
- mapping it into canonical entities
- storing the resulting rows in the main database

### 3. Score normalisation

The system must support a normalised comparable score for scored reviews where feasible.

This does not mean every source type must be supported immediately, but the pipeline must clearly handle at least a few common scoring schemes.

### 4. Useful API endpoints

The backend must expose a small but coherent REST API that supports the frontend.

At minimum, the system should be able to fetch:

- a list of games
- a single game and its associated critic reviews
- publication information where relevant for display

### 5. Usable frontend pages

The frontend must provide at least:

- a homepage or browse page
- at least one listing or rankings-style page
- a game detail page

The pages should be clear, legible, and content-oriented.

## Strongly preferred MVP capabilities

These are not strictly mandatory, but they are highly desirable if they do not significantly delay delivery:

- more than one review source
- basic publication pages
- simple sorting or filtering on game lists
- display of review count alongside aggregate score
- clear indication when a review is unscored

## Explicit non-goals

The MVP should not include the following unless there is a very strong reason:

- user accounts
- authentication for end users
- user-submitted ratings
- user-submitted reviews
- recommendation systems
- social or community features
- collection or marketplace functionality
- a generic admin platform
- a heavy workflow orchestration system
- a dedicated search engine
- GraphQL
- microservices
- personalised experiences

## Acceptable shortcuts

The MVP may take the following shortcuts:

- support only one or a few review sources
- support only a subset of scoring schemes initially
- use straightforward deterministic matching before more advanced entity resolution exists
- use simple rankings and aggregate formulas before more nuanced weighting exists
- defer critic-level modelling if publication-level modelling is enough
- keep visual design simple as long as the pages are clear and usable

## Quality bar

The MVP does not need to be large, but it does need to be coherent.

A feature is good enough for MVP when it is:

- understandable
- reasonably reliable
- easy to inspect and debug
- not obviously misleading
- consistent with the project’s core concept

## Launch criteria

The MVP can be considered ready for an initial launch or external demo when all of the following are true:

- at least one real source is ingested end-to-end
- canonical game, publication, and review data exists in the database
- score normalisation is functioning for the supported source types
- the frontend can render game pages with meaningful critic information
- the system can support a small catalogue without manual breakage
- the product already feels like a board game critic aggregation site rather than a code demo

## What can wait until later

The following are important but explicitly post-MVP unless they become necessary sooner:

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
