# Final Scoring

A critic-focused review aggregation index for board games.

## Setting up

The build pipeline needs a local LLM for the extraction step. See
[docs/LLM_SETUP.md](docs/LLM_SETUP.md).

## Spiders

Run a spider by hand with `uv run python -m finalscoring.scraping <name>`.
`uv run scrapy check` runs the spider contracts — smoke tests that each parsing
callback still matches its source. See
[docs/SPIDER_CONTRACTS.md](docs/SPIDER_CONTRACTS.md).
