# Entity resolution

This document defines how Final Scoring should think about resolving scraped source records into canonical game entities.

This is one of the highest-risk areas of the project. The system should therefore be conservative, explicit, and easy to debug.

## Product principle

A wrong match is usually worse than an unresolved match.

Contributors and coding agents should prefer leaving a review unresolved rather than silently attaching it to the wrong canonical game.

## Resolution target

The goal of entity resolution is to map source-level review rows onto canonical entities in the application database.

For MVP, the most important resolution task is:

- source review -> canonical `Game`
- source review -> canonical `Publication`

Publication resolution is usually simpler. Game resolution is the higher-risk problem and should receive the most care.

## Preferred canonical anchor

Where available, BoardGameGeek identifiers can be very useful anchors for canonical game identity.

However:

- not every source will expose a BGG link
- not every scraped record will include a reliable external identifier
- absence of a BGG identifier should not block the project

BGG IDs should help when available, but MVP should not assume they always exist.

## Resolution strategy hierarchy

When resolving a scraped review to a canonical game, prefer this order of confidence:

1. explicit known external identifier match
2. previously curated mapping for that source/title pair
3. exact or very strong title match under clear contextual agreement
4. unresolved

Contributors should avoid jumping too quickly from weak title similarity to a canonical assignment.

## Acceptable MVP matching signals

For MVP, useful signals may include:

- exact title match
- near-exact title match after normalisation
- source-specific mapping tables
- year agreement when available
- BGG linkage when available
- publication-specific historical consistency

## Dangerous matching cases

Use extra caution for:

- titles with common words
- games with subtitles
- localised names
- revised editions
- anniversary editions
- deluxe editions
- expansions vs base games
- reimplementations
- similar games from the same franchise

These should not be matched aggressively with naive fuzzy matching.

## Title normalisation

The system may use lightweight title normalisation to improve matching, such as:

- case folding
- whitespace normalisation
- simple punctuation normalisation

However, title normalisation should stay conservative. It should not become an excuse for broad fuzzy matching without evidence.

## Editions and variants

MVP should treat editions cautiously.

Guidelines:

- if the review is clearly about a distinct edition and that distinction matters, do not silently collapse it into the base game without a policy
- if the project is not yet ready to represent edition distinctions cleanly, unresolved is better than wrong collapse
- contributors should document assumptions if they deliberately collapse source distinctions

This is an area likely to need richer modelling later.

## Expansions

Expansions should not be silently attached to the base game.

If a source review is clearly about an expansion:

- it should resolve to a distinct canonical game-like entity if the model supports that
- otherwise it should remain unresolved until the model or policy supports it properly

## Publication resolution

Publication resolution is expected to be simpler and may often rely on deterministic source-level configuration.

For MVP, each scraper or source adapter should usually know which canonical publication it belongs to.

## Unresolved records

The system should be able to tolerate unresolved records during MVP.

That means:

- unresolved reviews should not necessarily crash the pipeline
- unresolved rows should be visible for debugging
- unresolved records should be easy to inspect and later fix
- the pipeline should support deliberate improvement over time

This is preferable to forcing low-confidence matches.

## Debuggability expectations

Entity resolution should be easy to inspect.

Where practical, the system should make it possible to understand:

- what source title was extracted
- what candidate canonical entity was considered
- what signals were used
- why the match succeeded or failed

This does not require a heavy framework, but the logic should not be opaque.

## Recommended MVP approach

For MVP, prefer a pragmatic and conservative approach:

- use deterministic matching where possible
- support source-specific mappings
- exploit external identifiers when available
- allow unresolved rows
- avoid ambitious fuzzy matching systems

## What to avoid in MVP

Do not introduce, unless clearly necessary:

- overly complex probabilistic matching pipelines
- opaque embedding-based resolution as the default path
- aggressive fuzzy matching without review
- silent auto-collapse of editions and expansions into base games

## Open questions for later

- when should aliases become a first-class entity?
- how should editions and reprints be represented canonically?
- when should critic or publication-specific knowledge influence matching?
- should there be an internal review queue for unresolved matches?
- when does a game-family model become necessary?
