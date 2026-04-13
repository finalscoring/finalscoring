# Data model

## Purpose

The initial data model should support the core Final Scoring use case: collecting, normalising, storing, and presenting published critic reviews of board games.

The first version should stay narrow. It should model the smallest set of entities needed to support useful game pages, review listings, and simple rankings.

## Core entities

The initial model centres on three entities:

- `Game`
- `Publication`
- `Review`

A `Critic` entity may be introduced later if author-level modelling becomes important.

## Entity definitions

### Game

A `Game` represents a canonical board game in the system.

Suggested fields:

- `id`
- `name`
- `slug`
- `bgg_id` for BoardGameGeek linkage where available
- `year_published`

Notes:

- this should represent the canonical game entity, not a source-specific row
- aliases or source-specific names can be handled later if needed

### Publication

A `Publication` represents the source or outlet that published a review.

Suggested fields:

- `id`
- `name`
- `slug`
- `website_url`

Notes:

- in the MVP, publication-level modelling is likely enough
- the system does not need to model every site attribute immediately

### Review

A `Review` represents one published critical review of one game from one publication.

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

- `original_score` should preserve the source form where practical, such as `8/10`, `4 stars`, or `Recommended`
- `normalised_score` should represent a comparable numeric scale derived from the original review score where possible
- not every review will necessarily have a usable score

## Relationships

### Game to Review

One `Game` can have many `Review` records.

### Publication to Review

One `Publication` can have many `Review` records.

### Review to Game and Publication

Each `Review` belongs to exactly one `Game` and one `Publication` in the canonical model.

## Canonical modelling principles

### Canonical first

The main tables should represent canonical entities, not raw source-specific payloads.

### Preserve source truth where useful

Important source values such as original score strings and source URLs should be retained.

### Normalise only where justified

Score normalisation should be explicit and traceable.

### Leave room for enrichment

The model should be simple now but allow later extensions such as critics, excerpts, tags, source metadata, confidence scores, or alternate titles.

## Possible future entities

These are intentionally deferred, but likely candidates later.

### Critic

Represents an individual author or reviewer.

Possible reasons to add it:

- multiple authors per publication matter analytically
- users benefit from author-level browsing
- publication and author need to be separated cleanly

### RawReview or SourceRecord

Represents raw scraped source data before canonical mapping.

Possible reasons to add it:

- traceability
- easier debugging of ingestion
- support for multiple parsers or ingestion pipelines

### GameAlias

Represents alternate names or source-specific titles for a game.

Possible reasons to add it:

- source naming inconsistencies
- localised names
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

These do not need to block the MVP, but they should be revisited as real data arrives.

- Do we need a separate `Critic` entity early?
- How should scoreless reviews be represented in aggregates?
- Do we need a dedicated table for raw ingestion outputs?
- How should multiple reviews of the same game from the same publication be handled?
- How should editions, expansions, or reimplementations be distinguished from base games?

## Recommendation for the first implementation

Start with just:

- `games`
- `publications`
- `reviews`

Then evolve the model only once real ingestion work reveals the pressure points.
