# Development

## Prerequisites

- Python 3.11+
- An OpenAI-compatible LLM endpoint. For local development, either
  [vLLM][vllm] (recommended for production builds, requires a GPU)
  or [Ollama][ollama] (CPU-friendly, easier to install). The
  extraction code talks to both identically.
- For the eventual frontend: Node.js 20+ (not needed for backend
  development).

## Setup

```bash
git clone https://github.com/finalscoring/final-scoring.git
cd final-scoring
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

cp .env.example .env
# Edit .env: point LLM_API_BASE_URL at your local model.
```

## The CLI

Everything you'll want to do during development is exposed through the
`fs` command:

```bash
fs --help                       # see all commands
fs db init --drop-existing      # create a fresh empty database
fs scrape sdj --limit 5         # run one spider against 5 items
fs build                        # full build: import, load, score, vacuum
```

## Running a model locally

### Ollama (easiest)

```bash
ollama pull qwen2.5:14b-instruct
ollama serve  # exposes OpenAI-compatible API on :11434
```

In your `.env`:

```
LLM_API_BASE_URL=http://localhost:11434/v1
LLM_MODEL=qwen2.5:14b-instruct
```

### vLLM (faster, GPU required)

```bash
pip install vllm
vllm serve Qwen/Qwen2.5-14B-Instruct --port 8000
```

In your `.env`:

```
LLM_API_BASE_URL=http://localhost:8000/v1
LLM_MODEL=Qwen/Qwen2.5-14B-Instruct
```

## Adding a new critic source

See `data/overrides/README.md` for the registry workflow and
`src/final_scoring/scraping/spiders/spiel_des_jahres.py` for a worked
example of a sitemap-driven spider.

In short:

1. Add the critic to `data/overrides/critics.csv`.
2. Write a spider in `src/final_scoring/scraping/spiders/`.
3. Register it in `_discover_spiders()` in `src/final_scoring/cli/app.py`.
4. Run `fs scrape <slug> --limit 10` and check the JSONL output.

## Testing

```bash
pytest                          # unit + integration
pytest tests/unit               # unit only (fast)
ruff check .                    # lint
ruff format .                   # format
mypy src                        # type-check
```

## Iterating on prompts

Prompts are versioned under `prompts/<name>/<version>.md`. To change
the extraction prompt:

1. **Do not edit `v1.md`.** Create `v2.md` alongside it.
2. Update `DEFAULT_PROMPT_VERSION` in `pipeline/extraction.py`.
3. Document the diff in `prompts/<name>/CHANGELOG.md`.
4. Re-run extraction against your dev fixtures and compare outputs.

The version tag lands on every `Review` row's
`extraction_model_version` field so the database remembers which
prompt produced what.

## Iterating on scoring

Scoring parameters live in `src/final_scoring/scoring/config.py`. To
adjust thresholds:

1. Bump `ScoringConfig.version` from `v1` to `v2`.
2. Change the parameter values.
3. Update `docs/methodology.md` to describe the change.
4. Run `fs build` — aggregates regenerate under the new version.

[vllm]: https://github.com/vllm-project/vllm
[ollama]: https://ollama.com/
