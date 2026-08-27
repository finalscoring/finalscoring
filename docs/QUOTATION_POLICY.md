# Quotation Policy — Why Quotes Are Capped, and What Actually Protects Us

Final Scoring stores and displays a short verbatim pull-quote from each
review. This document records why the quote is capped, what the cap is
and is not, and which practices — not lengths — actually keep the
project on the right side of copyright.

**This is not legal advice and was not written by a lawyer.** It records
reasoning, so the next person doesn't mistake an engineering guardrail
for a legal finding. Get an actual opinion before public launch.

## There is no legal maximum

No jurisdiction defines a character count, word count, or percentage
below which quotation is safe. The figures that circulate — 300
characters, 250 words, "10% of the work" — are publishers' internal
permission-clearance policies that got mistaken for law. They have no
statutory basis anywhere.

The case that should end the "short means safe" intuition is *Harper &
Row v. Nation Enterprises* (1985): roughly **300 words** taken from a
200,000-word memoir was held infringing, because the excerpt was the
*heart* of the work. Quantity was never the question.

## The rules that actually apply

**Germany — § 51 UrhG (*Zitatrecht*).** The one that matters most for
German-language reviews. A *Kleinzitat* is lawful with no length limit,
provided there is a genuine **Zitatzweck**: the quote must serve one's
own intellectual engagement with the work — as evidence, reference, or
object of discussion. A quote that merely decorates a page, or that
substitutes for reading the original, fails the test *at any length*.
Attribution of source and author is mandatory, not optional.

**EU — InfoSoc Directive Art. 5(3)(d).** Same structure: quotation for
criticism or review, of a work already lawfully made available, with
attribution, used in accordance with fair practice and only "to the
extent required by the specific purpose."

**US — 17 U.S.C. § 107.** Four-factor fair use, decided case by case.
No safe harbour, no threshold.

## The specific risk in this design

The pipeline deliberately extracts the most quotable, most load-bearing
sentence in a review — the critic's verdict. For a review, that sentence
*is* the heart of the work, which is exactly what *Harper & Row*
scrutinised. No character cap insulates against that.

What makes it defensible is purpose and market effect rather than
length. An aggregation index that reports a critic's verdict alongside
their score, attributed and linked, has a strong quotation purpose and
sends readers *to* the review rather than replacing it. That is the
argument the product has to keep earning.

## What actually reduces exposure

Ranked by how much they matter — all of them more than the number.

1. **Attribution on every displayed quote.** Critic name and outlet.
   Legally required in DE/EU, a fair-use factor in the US. The schema
   already carries `reviews.critic_id` and `reviews.outlet_slug`.
2. **A link to the source review.** This is the strongest counter to
   market substitution, the factor most likely to sink a fair-use
   argument. Note the gap: `reviews.url` is the *scraped page*, which
   for a meta-source like an SdJ roundup is not the critic's own review
   (`SDJ_PIPELINE_NOTES.md` gap #2). That gap is a copyright concern,
   not only a data-modelling one.
3. **One quote per review, never several.** Multiple excerpts from one
   piece read as reproduction; a single excerpt reads as citation.
4. **Never let the page substitute for the review.** Score, one quote
   and a link is defensible. Score, quote, plus a full paraphrase of the
   critic's argument is much less so.
5. **A working takedown and opt-out path.** In practice this resolves
   almost every real dispute before it becomes one, and it is worth more
   than any cap. Currently an open item under editorial policy in
   `DECISIONS_OPEN.md`.

Two further notes:

- **Proportion matters more than absolute length.** 300 characters out
  of a 400-word review is a far larger taking than the same 300
  characters out of a 3,000-word one. The schema does not currently
  record source length, so nothing enforces this; it is a reason to keep
  the cap conservative rather than to raise it.
- **Accepted practice.** Metacritic and Rotten Tomatoes have run on
  roughly one-to-two-sentence attributed quotes with links for two
  decades. That is not authority, but it is meaningful evidence of what
  the industry treats as normal.

## The cap, and what it is for

The cap is **300 characters**, confirmed by the maintainer on
2026-08-22 and recorded in `PROJECT.md`. `ExtractedReview.quote`
enforces it at the schema level, and the current prompt
(`extraction/prompts/`, named by `PROMPT_VERSION`) states the same limit
and requires the quote be copied verbatim — one continuous passage of
the reviewer's own words, never spliced, paraphrased, or truncated to
fit.

The cap's real job is **engineering, not legal**: it stops the model
emitting three paragraphs when asked for a sentence, which is a genuine
failure mode, and a schema-level `max_length` is the only backstop
against it. 300 characters is roughly 45–50 words — one to two sentences
— which sits comfortably within "to the extent required by the specific
purpose" and matches accepted practice.

One known gap: **`Review.quote` is uncapped.** The limit exists only on
the extraction schema, so the guarantee does not survive into the
persisted record that actually ships to readers. The cap belongs at both
layers, and a review that arrives from any path other than the extractor
would otherwise bypass it entirely.

## Out of scope for this document

Acquiring the text in the first place — site terms of service, robots
directives, and the EU *sui generis* database right — is a separate
question from quoting it, with a different analysis. Nothing here speaks
to it. It deserves an actual lawyer before launch.
