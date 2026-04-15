# Entity resolution

Defines how Final Scoring resolves scraped source records into canonical game entities.

Highest-risk area. System must be conservative, explicit, debuggable.

## Product principle

Wrong match worse than unresolved match.

Prefer leaving review unresolved over silently attaching to wrong canonical game.

## Resolution target

Goal: map source-level review rows to canonical entities in application database.

MVP priority:

- source review -> canonical `Game`
- source review -> canonical `Publication`

Publication resolution simpler. Game resolution higher-risk, needs most care.

## Preferred canonical anchor

BGG identifiers useful anchors for canonical game identity.

But:

- not every source exposes BGG link
- not every scraped record includes reliable external identifier
- absence of BGG ID must not block project

BGG IDs help when available. MVP must not assume they always exist.

## Resolution strategy hierarchy

Prefer this confidence order:

1. explicit known external identifier match
2. previously curated mapping for that source/title pair
3. exact or very strong title match under clear contextual agreement
4. unresolved

Avoid jumping from weak title similarity to canonical assignment.

## Acceptable MVP matching signals

Useful signals:

- exact title match
- near-exact title match after normalisation
- source-specific mapping tables
- year agreement when available
- BGG linkage when available
- publication-specific historical consistency

## Dangerous matching cases

Extra caution for:

- titles with common words
- games with subtitles
- localised names
- revised editions
- anniversary editions
- deluxe editions
- expansions vs base games
- reimplementations
- similar games from same franchise

Do not match aggressively with naive fuzzy matching.

## Title normalisation

Lightweight normalisation acceptable:

- case folding
- whitespace normalisation
- simple punctuation normalisation

Stay conservative. Not excuse for broad fuzzy matching without evidence.

## Editions and variants

Handle cautiously.

Guidelines:

- if review clearly about distinct edition and distinction matters, do not silently collapse into base game without policy
- if project not ready to represent edition distinctions cleanly, unresolved beats wrong collapse
- document assumptions when deliberately collapsing source distinctions

Area likely needs richer modelling later.

## Expansions

Do not silently attach expansions to base game.

If source review clearly about expansion:

- resolve to distinct canonical game-like entity if model supports it
- otherwise leave unresolved until model or policy supports it

## Publication resolution

Simpler. Often relies on deterministic source-level configuration.

Each scraper or source adapter should usually know which canonical publication it belongs to.

## Unresolved records

System must tolerate unresolved records during MVP:

- unresolved reviews must not crash pipeline
- unresolved rows must be visible for debugging
- unresolved records must be easy to inspect and fix later
- pipeline must support deliberate improvement over time

Preferable to forcing low-confidence matches.

## Debuggability expectations

Resolution must be inspectable.

Where practical, system should expose:

- what source title was extracted
- what candidate canonical entity was considered
- what signals were used
- why match succeeded or failed

No heavy framework needed. Logic must not be opaque.

## Recommended MVP approach

Pragmatic, conservative:

- deterministic matching where possible
- source-specific mappings
- exploit external identifiers when available
- allow unresolved rows
- avoid ambitious fuzzy matching

## What to avoid in MVP

Do not introduce unless clearly necessary:

- overly complex probabilistic matching pipelines
- opaque embedding-based resolution as default path
- aggressive fuzzy matching without review
- silent auto-collapse of editions and expansions into base games

## Open questions for later

- when should aliases become first-class entity?
- how should editions and reprints be represented canonically?
- when should critic or publication-specific knowledge influence matching?
- should there be internal review queue for unresolved matches?
- when does game-family model become necessary?