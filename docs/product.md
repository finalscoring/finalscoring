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

## MVP goals

The MVP should prove that Final Scoring can deliver a useful, credible, and maintainable critic aggregation experience.

The MVP should include:

- a canonical database of games, publications, and reviews
- ingestion of review data from at least one real source
- score normalisation into a common comparable scale
- simple game pages showing aggregated critic information
- simple listing or ranking pages
- a small but coherent API and frontend

## MVP non-goals

The MVP should explicitly avoid trying to become a full board game platform.

Out of scope for the MVP:

- user accounts
- user ratings or reviews
- recommendation systems
- social/community features
- marketplace or collection management features
- complex personalisation
- full coverage of every review source
- rich critic profiles unless clearly needed

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

## Likely user journeys

### Researching a game

A user lands on a game page and sees:

- the aggregated critic score
- the number of critic reviews
- the contributing publications
- the underlying reviews and original scores where available

### Browsing highly rated games

A user visits a rankings or browse page and explores games sorted by critic score, review count, or related summary metrics.

### Comparing reception

A user compares multiple games by looking at their critic scores, review counts, source coverage, and score spread.

## Success criteria for the MVP

The MVP is successful if it can demonstrate all of the following:

- review data can be ingested and normalised reliably
- the resulting game pages are useful and intelligible
- the product can support a small number of real sources without architecture strain
- the system creates a strong base for later expansion
