# Scraping results

This directory holds the JSON Lines files produced by the scraping
pipeline: `RawItem` records from the spiders, and the `ExtractedReview`
records the LLM extraction step derives from them. Whether those travel
as one enriched stream or two separate ones is not yet decided — see
`docs/DECISIONS_OPEN.md`.

Contents are gitignored — they are intermediate artifacts that the
build replays into the SQLite database. That database is written to
`data/finalscoring.db` (`FS_DB_PATH`), deliberately outside this
directory: it is the product of a build rather than an input to one. To
reproduce a state across machines, share it, not these files.

Filenames follow `<spider>-<crawl start>-<batch>.jl`, for example
`spiel-des-jahres-2026-08-24T09-12-33+00-00-00001.jl`. The pattern comes
from the feed configuration in `finalscoring.scraping.scrapy_settings`.
`FS_RESULTS_DIR` chooses the directory; the template itself is not
configurable, because the load step has to find and order these files
without being told how they were named. Batches are capped at 10,000
items, so an interrupted crawl leaves its finished batches behind.
