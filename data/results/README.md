# Scraping results

This directory holds JSONL files produced by the scraping pipeline.
Each line is a `RawReviewItem` enriched with LLM-extracted `reviews`.

Contents are gitignored — they are intermediate artifacts that the
build replays into the SQLite database. To reproduce a state across
machines, share the SQLite output, not these files.

Filename convention (set by `SCRAPER_FEED_URI` in `.env.example`):

    <spider-name>-<utc-timestamp>-<batch-id>.jl

The build script (`fs build`) walks this directory and replays every
`.jl` / `.jsonl` file it finds.
