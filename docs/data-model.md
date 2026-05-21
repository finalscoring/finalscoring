# Data model

## Purpose

Support Final Scoring core use case: collect, normalise, store, present published critic reviews of board games.

Stay narrow. Model smallest entity set for useful game pages, review listings, simple rankings.

## Core entities

Three entities:

- `Game`
- `Publication`
- `Review`

`Critic` deferred — add if author-level modelling matters later.

## Entity definitions

### Game

Canonical board game in system.

Suggested fields:

- `id`
- `name`
- `slug`
- `bgg_id` for BoardGameGeek linkage where available
- `year_published`

Notes:

- canonical entity, not source-specific row
- aliases/source names deferred

### Publication

Source or outlet that published a review.

Suggested fields:

- `id`
- `name`
- `slug`
- `website_url`

Notes:

- publication-level modelling sufficient for MVP
- no need to model every site attribute immediately

### Review

One published critical review of one game from one publication.

Suggested fields:

- `id`
- `game_id`
- `publication_id`
- `title`
- `url`
- `original_score`
- `normalised_score`
- `published_date`

Notes:

- `original_score` preserves source form where practical: `8/10`, `4 stars`, `Recommended`
- `normalised_score` comparable numeric scale derived from original where possible
- not every review has usable score

## Relationships

### Game to Review

One `Game` → many `Review` records.

### Publication to Review

One `Publication` → many `Review` records.

### Review to Game and Publication

Each `Review` belongs to exactly one `Game` and one `Publication`.

## Canonical modelling principles

### Canonical first

Main tables = canonical entities, not raw source payloads.

### Preserve source truth where useful

Retain original score strings and source URLs.

### Normalise only where justified

Score normalisation explicit and traceable.

### Leave room for enrichment

Simple now, extensible later: critics, excerpts, tags, source metadata, confidence scores, alternate titles.

## Possible future entities

Deferred but likely.

### Critic

Individual author or reviewer.

Add when:

- multiple authors per publication matter analytically
- users need author-level browsing
- publication/author separation needed

### RawReview or SourceRecord

Raw scraped data before canonical mapping.

Add when:

- traceability needed
- ingestion debugging matters
- multiple parsers or pipelines

### GameAlias

Alternate names or source-specific titles.

Add when:

- source naming inconsistent
- localised names needed
- edition naming issues

## First relational sketch

```text
Game
  id
  name
  slug
  bgg_id
  year_published

Publication
  id
  name
  slug
  website_url

Review
  id
  game_id -> Game.id
  publication_id -> Publication.id
  title
  url
  original_score
  normalised_score
  published_date
```

## Open questions

Revisit as real data arrives.

- Need separate `Critic` entity early?
- Scoreless reviews in aggregates — how?
- Dedicated table for raw ingestion outputs?
- Multiple reviews of same game from same publication — how handled?
- Editions, expansions, reimplementations vs base games — how distinguished?

## Recommendation for first implementation

Start with:

- `games`
- `publications`
- `reviews`

Evolve only once real ingestion reveals pressure points.