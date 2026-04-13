# Source strategy

This document defines how Final Scoring should think about review sources and what kinds of material should be included in the product.

The goal is to keep source ingestion decisions consistent and avoid arbitrary assumptions by contributors or coding agents.

## Product principle

Final Scoring is about **published critical reception** of board games.

It is not a general web crawler for all board game content. Inclusion should be guided by whether a source materially contributes to understanding how a game was critically received.

## What counts as a source

A source is a publication, site, channel, outlet, or other identifiable origin of critical content that publishes board game reviews or review-like verdicts.

Examples may include:

- editorial board game review sites
- magazines with board game coverage
- video channels with structured review content
- publications with clearly attributable review pages and verdicts

The source model should remain conservative early on. It is better to support fewer, better-understood sources than broad and messy coverage.

## What counts as a review

A review is a piece of published content that expresses a meaningful evaluative judgement about a specific board game.

Typical indicators:

- the content is primarily about a specific game
- it includes a verdict, recommendation, or score
- it reflects a retrospective or evaluative view, not just first impressions
- it is attributable to a source and usually linkable to a stable URL

## Content that should usually be included

These are good default candidates for inclusion:

- written reviews of specific games
- scored reviews
- unscored reviews with a clear evaluative verdict
- structured video reviews when they can be tied to a stable source and game
- publication pages that clearly correspond to a single game review

## Content that should usually be excluded

These should normally be excluded unless a later policy says otherwise:

- previews
- unboxing articles or videos
- rules explanations
- session reports
- buying guides
- top lists not centred on one game review
- news posts
- crowdfunding previews
- first impressions
- roundups containing many games without a clear review entry per game
- marketplace or store listings

## Scoreless reviews

Scoreless reviews may still be included if they are clearly reviews rather than adjacent content.

However:

- they should not be forced into fake numeric scores
- they should remain distinguishable from scored reviews
- downstream aggregates should handle them explicitly rather than pretending they are numeric inputs

## Publication vs critic

For MVP, the system should model the source primarily at the publication level.

This means:

- publication identity matters first
- critic identity can be deferred
- author names may still be captured later, but should not block ingestion

If a source has many authors, that alone is not enough reason to introduce critic-level modelling before it is needed.

## Multiple reviews from the same source

Multiple reviews from the same publication may be allowed, but only if they are meaningfully distinct pieces of content.

Examples that may justify multiple entries:

- a separate review for a new edition that should be treated distinctly
- clearly separate review pages for base game and expansion
- publication-specific updated reviews where both versions are intentionally retained

However, the default assumption should be conservative. The system should avoid accidental duplication from:

- mirrored URLs
- revised pages that are really the same review
- alternate mobile / AMP / tracking variants
- scraper duplication bugs

## Videos, podcasts, and non-traditional formats

These may be supported later, but MVP should remain cautious.

To include non-written formats, the content should ideally have:

- a stable canonical URL
- a clear game target
- a clear review or verdict identity
- a reliable way to extract source and score metadata

Contributors should not aggressively expand to these formats before written sources are working well.

## Source onboarding philosophy

Add sources incrementally.

For each new source, aim to understand:

- what a canonical game review looks like on that source
- how scores are represented
- how stable the URLs are
- whether the publication uses multiple review templates
- whether the content is easy to parse reliably
- whether legal and politeness considerations are acceptable

## Recommended source onboarding checklist

Before onboarding a new source, confirm:

1. the source clearly publishes board game reviews
2. the review pages are structurally consistent enough to parse
3. the game title can be extracted reliably
4. the score or verdict representation is understandable
5. the source adds real product value
6. the source can be scraped or accessed politely and reasonably

## Scraping and politeness expectations

Source ingestion should be technically and operationally polite.

Contributors should:

- obey robots and site policies where appropriate
- avoid aggressive request rates
- avoid unnecessary repeated crawling
- prefer stable canonical pages
- make scraper behaviour easy to inspect and throttle
- preserve source attribution clearly

Final Scoring should not behave like an indiscriminate crawler.

## Early-stage recommendation

For MVP, source selection should prioritise:

- clarity of review structure
- extractability
- stable URLs
- understandable scores or verdicts
- editorial credibility
- ease of maintaining the parser

In practice, a small number of well-behaved sources is better than broad but fragile coverage.

## Open questions for later

These do not need to block MVP, but they should be revisited over time:

- how should video-first sources be modelled?
- when should critic-level attribution become first-class?
- should scoreless but strongly evaluative reviews influence browse surfaces?
- how should updated or revised reviews be represented?
- how should translated or localised versions of the same review be handled?
