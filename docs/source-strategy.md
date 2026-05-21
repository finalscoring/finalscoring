# Source strategy

Defines how Final Scoring thinks about review sources and what material belongs in product.

Goal: keep source ingestion decisions consistent, avoid arbitrary assumptions.

## Product principle

Final Scoring = **published critical reception** of board games.

Not general web crawler. Inclusion guided by: does source materially contribute to understanding critical reception?

## What counts as a source

Publication, site, channel, or outlet publishing board game reviews or review-like verdicts.

Examples:
- editorial board game review sites
- magazines with board game coverage
- video channels with structured review content
- publications with attributable review pages and verdicts

Source model: stay conservative early. Fewer, better-understood sources beat broad messy coverage.

## What counts as a review

Published content expressing meaningful evaluative judgement about specific board game.

Indicators:
- primarily about specific game
- includes verdict, recommendation, or score
- retrospective/evaluative view, not just first impressions
- attributable to source, usually linkable to stable URL

## Content that should usually be included

- written reviews of specific games
- scored reviews
- unscored reviews with clear evaluative verdict
- structured video reviews tied to stable source and game
- publication pages clearly corresponding to single game review

## Content that should usually be excluded

- previews
- unboxing articles or videos
- rules explanations
- session reports
- buying guides
- top lists not centred on one game review
- news posts
- crowdfunding previews
- first impressions
- roundups with many games, no clear per-game review entry
- marketplace or store listings

## Scoreless reviews

May be included if clearly reviews, not adjacent content.

But:
- no fake numeric scores
- remain distinguishable from scored reviews
- downstream aggregates handle them explicitly, not as numeric inputs

## Publication vs critic

MVP: model source at publication level.

- publication identity first
- critic identity deferred
- author names capturable later, but should not block ingestion

Many authors alone = not enough reason for critic-level modelling before needed.

## Multiple reviews from same source

Allowed only if meaningfully distinct content.

May justify multiple entries:
- separate review for new edition treated distinctly
- separate pages for base game and expansion
- publication-specific updated reviews where both versions intentionally retained

Default: conservative. Avoid duplication from:
- mirrored URLs
- revised pages that are really same review
- alternate mobile/AMP/tracking variants
- scraper duplication bugs

## Videos, podcasts, and non-traditional formats

Defer to later. MVP: stay cautious.

To include non-written formats, ideally need:
- stable canonical URL
- clear game target
- clear review/verdict identity
- reliable way to extract source and score metadata

Don't expand to these before written sources work well.

## Source onboarding philosophy

Add sources incrementally.

Per new source, understand:
- what canonical game review looks like on that source
- how scores represented
- how stable URLs are
- whether publication uses multiple review templates
- whether content parses reliably
- whether legal and politeness considerations acceptable

## Recommended source onboarding checklist

Before onboarding:

1. source clearly publishes board game reviews
2. review pages structurally consistent enough to parse
3. game title extractable reliably
4. score or verdict representation understandable
5. source adds real product value
6. source scrapable politely and reasonably

## Scraping and politeness expectations

Ingestion must be technically and operationally polite.

- obey robots and site policies where appropriate
- avoid aggressive request rates
- avoid unnecessary repeated crawling
- prefer stable canonical pages
- scraper behaviour easy to inspect and throttle
- preserve source attribution clearly

Final Scoring not an indiscriminate crawler.

## Early-stage recommendation

MVP: prioritise:
- clarity of review structure
- extractability
- stable URLs
- understandable scores or verdicts
- editorial credibility
- ease of maintaining parser

Small number of well-behaved sources beats broad but fragile coverage.

## Open questions for later

Not blocking MVP, revisit over time:
- how should video-first sources be modelled?
- when should critic-level attribution become first-class?
- should scoreless but strongly evaluative reviews influence browse surfaces?
- how should updated or revised reviews be represented?
- how should translated or localised versions of same review be handled?