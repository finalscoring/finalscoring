# 006 — Multilingual from day one

**Status:** Accepted.
**Date:** 2026-05.

## Context

Most board game critic aggregators in the English-speaking world
either ignore non-English reviews or treat them as second-class. A
credible international index that includes German-language hobby
press from the start is a real differentiator — and one that aligns
with the existing Spiel-des-Jahres scraper that seeds the project.

The cost of building multilingual capability later is non-trivial: it
requires schema changes (adding a `language` field everywhere it's
needed), prompt updates (the extraction prompt must be explicit about
language identification), UI changes (browse and filter must handle
multiple languages gracefully), and a back-population of historical
data with inferred languages.

The cost of launching multilingual is much smaller: include the
`language` field in the schema from the start, write the extraction
prompt to identify language, and surface it in the UI.

## Decision

Final Scoring launches with German and English sources. The schema
carries a `language` field (ISO 639-1) on both `Critic` and `Review`
rows from v1. The extraction prompt asks the model to identify the
review's language directly from the text. The frontend exposes
language as a filter on browse and displays the language tag on every
review listing.

The roadmap explicitly leaves room for additional languages (French,
Spanish, Italian) as sources are identified — no v1.x rework will be
needed to add them.

## Consequences

**Committed to:**
- Source curation effort split across multiple languages from day one.
  This is the main risk: editorial bandwidth is finite, and broadening
  the language scope makes the source-registry phase longer.
- A modern model with strong multilingual capability is required for
  extraction. Constrains model choice (see ADR 002).
- The methodology page is published in English but acknowledges
  multilingual coverage. (Translating the methodology page itself is
  out of scope for v1.)

**Precluded:**
- Translating individual reviews into a single display language. We
  link out to the original review in its original language; we do
  not present a translated version. This is both an editorial
  decision (translations would be derivative content beyond
  attribution) and a scope decision (out of scope for an aggregator).

## Reversibility

Easy. Dropping a language is a matter of opting out the relevant
critics. Adding a new language requires identifying sources and
writing spiders for them — same workflow as adding any new source.
