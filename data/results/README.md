# Scraping results

This directory holds the JSON Lines files produced by the scraping
pipeline: `RawItem` records from the spiders, and the `ExtractedReview`
records the LLM extraction step derives from them. Whether those travel
as one enriched stream or two separate ones is not yet decided — see
`docs/DECISIONS_OPEN.md`.

Contents are gitignored — they are intermediate artifacts that the
build replays into the SQLite database. To reproduce a state across
machines, share the SQLite output, not these files.

The filename convention is not decided either. It will be fixed by the
spider's feed configuration when the first spider lands; until then, no
setting in `.env.example` governs it.
