# Pipeline data

Everything under `data/` is an intermediate build artifact. The pipeline
recreates these directories as it needs them, so a fresh clone starts
with only this README; the contents are gitignored. To reproduce a state
across machines, share the built database (see below), not these files.

## `data/scraping/`

The JSON Lines files the spiders produce: one `RawItem` record per line.

Filenames follow `<spider>-<crawl start>-<batch>.jl`, for example
`spiel-des-jahres-2026-08-24T09-12-33+00-00-00001.jl`. The pattern comes
from the feed configuration in `finalscoring.scraping.scrapy_settings`.
`FS_SCRAPING_DIR` chooses the directory; the template itself is not
configurable, because the load step has to find and order these files
without being told how they were named. Batches are capped at 10,000
items, so an interrupted crawl leaves its finished batches behind.

## `data/extraction/`

The `ExtractionRecord` lines the LLM extraction step derives from the raw
items, one file per run (`extraction-<timestamp>.jl`). Kept separate from
`data/scraping/` on purpose: the load step globs the scraping directory
for raw items, and an extraction record is not a raw item.
`FS_EXTRACTION_DIR` chooses the directory.

## `data/jobs/`

Scrapy's JOBDIR resume state, one subdirectory per spider, so an
interrupted crawl can continue where it stopped. `FS_JOBS_DIR` chooses
the directory. To wipe state and re-crawl from scratch, delete this
directory's contents and re-run the spider.

## `data/finalscoring.db`

The built SQLite database (`FS_DB_PATH`) — the product of a build rather
than an input to one, which is why it sits beside these directories
rather than inside one. Rebuilt from the artifacts above every time,
never edited in place.
