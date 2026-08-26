# Running a Local LLM

The extraction step needs an OpenAI-compatible endpoint. It runs at build
time only — nothing here is needed to serve the site, and no review text
leaves the machine.

## Quick start

Three commands and one setting. This is the whole minimal path.

```sh
brew install ollama          # or: https://ollama.com/download
ollama serve                 # leave running in its own terminal
ollama pull qwen2.5:7b       # ~4.7 GB
```

Then in `.env`:

```sh
FS_LLM_MODEL=qwen2.5:7b
```

`FS_LLM_BASE_URL` already defaults to `http://localhost:11434/v1`, which is
where `ollama serve` listens, so it needs no change for a local setup.

Verify with one real page:

```sh
uv run python -m finalscoring.scraping spiel-des-jahres   # produces raw items
```

then extract from one of them in a REPL:

```python
import json
from finalscoring.scraping.item import RawItem
from finalscoring.extraction import ReviewExtractor

with open("data/results/<the file the crawl wrote>.jl") as f:
    item = RawItem.model_validate(json.loads(f.readline()))

record = ReviewExtractor().extract(item)
print(len(record.result.reviews), "reviews")
```

## Choosing a model

The model is **only ever a config value**. `FS_LLM_MODEL` is a string; there
is no code, schema or migration tied to any particular one. Develop against
something small and run the real thing against something larger, on a
different machine if you like — every `ExtractionRecord` stores the model
that produced it, so a corpus built from a mix stays auditable.

What the task actually demands:

- **German and English competence.** Most sources are German. This matters
  far more than raw parameter count.
- **Instruction-following and JSON discipline** — the prompt asks for a
  specific structure with a rubric.
- **~8k context is plenty.** A Spiel-des-Jahres roundup runs about 5,400
  characters, roughly 2,000 tokens, plus the prompt.

Rough tiers:

| Purpose | Example | Size | Notes |
|---|---|---|---|
| Smoke test only | `qwen2.5:0.5b` | ~0.4 GB | Proves the plumbing. Extraction quality will be poor. |
| Development | `qwen2.5:7b` | ~4.7 GB | Verified working. See measurements below. |
| Real runs | a 14B–32B class model | ~9–20 GB | Worth it on a machine with the memory and the speed. |

**Check <https://ollama.com/library> for what is current** rather than
trusting the names above — the model landscape moves fast, and these are a
starting point, not a recommendation to freeze.

Rule of thumb for memory: a 4-bit quantised model needs roughly its file size
in free RAM, plus a little. `qwen2.5:7b` at 4.7 GB is comfortable on 16 GB and
trivial on 32 GB.

## What was actually measured

On a 2019 Intel Core i9-9980HK, 32 GB, **CPU inference only** — no useful GPU
acceleration, since Ollama's Metal support targets Apple Silicon's unified
memory rather than a discrete AMD card:

- `qwen2.5:7b` (Q4_K_M), one 5,395-character German roundup: **64.5 seconds**.
- That puts a full 93-roundup pass at roughly 100 minutes, which is fine for
  something that runs weekly.
- Apple Silicon will be substantially faster, but no figure is recorded here
  because none has been measured.

## Settings

All optional except the model name.

| Variable | Default | Notes |
|---|---|---|
| `FS_LLM_BASE_URL` | `http://localhost:11434/v1` | Ollama's default. Point it anywhere OpenAI-compatible, including another machine. |
| `FS_LLM_MODEL` | `llama3.2` | **Set this.** The default is a placeholder, not a recommendation. |
| `FS_LLM_API_KEY` | `not-needed` | Local servers ignore it; the OpenAI client refuses to start without something. |
| `FS_LLM_TIMEOUT` | `120.0` | Seconds per call. See the cold-start note below. |
| `FS_LLM_MAX_ATTEMPTS` | `3` | Total tries per item, including the first. |

## Other serving stacks

The client talks to `/v1/chat/completions` with a `json_schema`
`response_format`, which vLLM, llama.cpp's server and LM Studio all serve as
well. Switching should mean changing `FS_LLM_BASE_URL` and nothing else.

Only Ollama has actually been tested. If you use something else, the check
that matters is whether it accepts the request at all:

```sh
curl -s http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen2.5:7b",
       "messages":[{"role":"user","content":"Return JSON: {\"ok\": true}"}],
       "response_format":{"type":"json_schema","json_schema":{"name":"t",
         "strict":false,"schema":{"type":"object",
         "properties":{"ok":{"type":"boolean"}},"required":["ok"]}}}}'
```

A server that rejects `json_schema` may still accept
`{"type": "json_object"}`. Either way the pydantic validation in
`extraction/llm.py` is what actually enforces the shape — the schema is
guidance, so a weaker server costs retries rather than correctness.

## When it does not work

**`ExtractionFailed: ... model 'llama3.2' not found`** — `FS_LLM_MODEL` is
still the placeholder default. Set it to a model you have pulled;
`ollama list` shows them.

**`ExtractionFailed: ... Request timed out` on the first call, fine
afterwards** — the first request also pays for loading several GB into RAM.
Either raise `FS_LLM_TIMEOUT`, or warm the model first:

```sh
ollama run qwen2.5:7b "hi"
```

**Connection refused** — `ollama serve` is not running, or is on another
port. `curl -s http://localhost:11434/api/version` should answer.

**Extraction succeeds but finds too few reviews** — that is a prompt and
model-capability question, not a setup problem. A roundup citing four critics
yielding one is a known current limitation, not a broken installation.
