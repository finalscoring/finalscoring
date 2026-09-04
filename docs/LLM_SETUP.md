# Running the extraction LLM

The extraction step (`finalscoring.extraction`) turns each scraped `RawItem`
into structured `ExtractedReview` records by calling an LLM. It needs an
**OpenAI-compatible `/v1/chat/completions` endpoint**. It runs at build time
only — nothing here serves the public site.

Three settings point the extractor at a backend; everything else has a
working default:

| Variable | What it is |
|---|---|
| `FS_LLM_BASE_URL` | The endpoint, ending in `/v1`. Default `http://localhost:11434/v1` (local Ollama). |
| `FS_LLM_MODEL` | The model name the endpoint expects. **No default worth using — always set it.** |
| `FS_LLM_API_KEY` | A real key for a hosted API; any non-empty string for a local server. |

Whichever backend you use, every `ExtractionRecord` stores the model name and
the prompt hash that produced it, so a corpus built from a mix stays
auditable.

**Local vs hosted is a real choice, not just performance.** A local model
keeps every review's text and every extracted quote on your machine. A hosted
API sends both to a third party — see [Hosted APIs](#hosted-apis-anthropic-openai-google)
for what that means for `QUOTATION_POLICY.md`.

---

## Pick a path

- **Just get it working on a Mac** → [Ollama](#local-ollama). Simplest, one
  binary, tested.
- **You need Qwen3 with thinking disabled, or token-level JSON enforcement**
  → [llama.cpp](#local-llamacpp). More flags, more control.
- **Weak machine, or you want it fast and cheap and don't mind the egress**
  → [Hosted API](#hosted-apis-anthropic-openai-google). A 2019 Intel Mac runs
  a 27B model at minutes per page (see [Hardware reality](#hardware-reality)).
- **One machine has the GPU/RAM, the pipeline runs on another** → serve the
  model on the strong box and point the pipeline at it
  [over the LAN](#local-network-model-on-another-machine).
- **You have an NVIDIA GPU** → vLLM is the fast option but is
  [not covered here](#not-covered).

---

## Local: Ollama

### Install and start

```sh
brew install ollama            # or the installer from https://ollama.com/download
ollama serve                   # leave this running in its own terminal
```

`ollama serve` listens on `127.0.0.1:11434` and exposes the OpenAI API at
`http://localhost:11434/v1`, which is already the `FS_LLM_BASE_URL` default —
no change needed.

### Pull a model

```sh
ollama pull qwen2.5:7b         # ~4.7 GB — development / smoke testing
ollama pull gemma3:27b         # ~17 GB  — a real-run candidate
ollama list                    # what you have
```

### Fix the context window (important)

Ollama defaults `num_ctx` to **2048 tokens**. The extraction prompt alone is
~1,800 tokens, and a Spiel-des-Jahres roundup adds ~2,000–4,000 more, so the
default silently truncates the article and the model never sees the reviews
at the end. Ollama does not warn you.

Bake a fixed model with a sane context and deterministic sampling:

```sh
cat > fs-gemma3.Modelfile <<'EOF'
FROM gemma3:27b
PARAMETER num_ctx 8192
PARAMETER temperature 0
EOF

ollama create fs-gemma3 -f fs-gemma3.Modelfile
```

```sh
# .env
FS_LLM_MODEL=fs-gemma3
```

(The extractor does not set `temperature`; Ollama's default is `0.8`, which is
wrong for extraction. The Modelfile is the place to pin it.)

### Warm it before the first real call

The first request also loads several GB into RAM and can exceed
`FS_LLM_TIMEOUT`:

```sh
ollama run fs-gemma3 "hi"
```

### Structured output

Ollama accepts the `response_format` `json_schema` the extractor sends
(v0.5.0+). It treats the schema as a hint, not a hard constraint — the
pydantic validation in `extraction/llm.py` is the real backstop, so a schema
miss costs a retry, not bad data.

---

## Local: llama.cpp

More setup than Ollama, but it is the local stack where you can **disable
Qwen3's thinking mode with a server flag** and where the JSON schema is
**enforced token by token** (converted to a GBNF grammar), so a smaller model
cannot emit malformed JSON at all.

### Install

```sh
brew install llama.cpp         # provides llama-server, llama-cli
brew install huggingface-cli   # to fetch model files
```

### Get a model file (GGUF)

```sh
huggingface-cli download bartowski/google_gemma-3-27b-it-GGUF \
  google_gemma-3-27b-it-Q4_K_M.gguf \
  --local-dir ~/models
```

Good sources for GGUF quants: `bartowski/…-GGUF`, `unsloth/…-GGUF`,
`ggml-org/…`. `Q4_K_M` is the usual quality/size compromise.

### Serve

```sh
llama-server \
  -m ~/models/google_gemma-3-27b-it-Q4_K_M.gguf \
  --host 127.0.0.1 --port 8080 \
  --ctx-size 8192 \
  --temp 0 \
  --jinja \
  -ngl 99                       # Apple Silicon: offload all layers to the GPU.
                                # 2019 Intel Mac: DROP this line (CPU only).
```

- `--jinja` uses the model's real chat template — needed for correct Gemma /
  Qwen formatting and for reasoning control.
- `--ctx-size` is the real context window here; no per-model config like
  Ollama's Modelfile.

For **Qwen3 with thinking off**, add (recent builds only — check
`llama-server --help | grep -i reason`):

```sh
  --reasoning-budget 0
```

### Point the extractor at it

```sh
# .env
FS_LLM_BASE_URL=http://127.0.0.1:8080/v1
FS_LLM_MODEL=local                 # llama.cpp serves the one loaded model;
                                   # the name is not checked
```

---

## Local network: model on another machine

Run the model on the machine that has the memory and the GPU — an Apple
Silicon Mac, say — and run the scraping/extraction pipeline anywhere else on
the same network. The text still never leaves your LAN.

### On the model host

**Ollama** binds to `127.0.0.1` by default. Make it listen on the network by
setting `OLLAMA_HOST` before `ollama serve`:

```sh
OLLAMA_HOST=0.0.0.0:11434 ollama serve
```

To make that permanent on macOS:

```sh
launchctl setenv OLLAMA_HOST "0.0.0.0:11434"
# then restart Ollama
```

**llama.cpp**: serve with `--host 0.0.0.0` (instead of `127.0.0.1`) and,
optionally, `--api-key <secret>`.

macOS will pop up a firewall prompt the first time — allow incoming
connections for `ollama` / `llama-server`.

### On the pipeline host

Point `FS_LLM_BASE_URL` at the model host by IP or mDNS name (`.local` works
between Macs):

```sh
# .env
FS_LLM_BASE_URL=http://studio.local:11434/v1     # or http://192.168.1.42:11434/v1
FS_LLM_MODEL=fs-gemma3
FS_LLM_API_KEY=not-needed                        # or the llama.cpp --api-key value
```

Check it from the pipeline host:

```sh
curl -s http://studio.local:11434/api/version    # Ollama
```

### Notes

- **Warm the model on the host**, not remotely — `ollama run fs-gemma3 "hi"`
  on the model machine. The first real call still pays the load time, so keep
  `FS_LLM_TIMEOUT` at 120 or higher.
- Traffic is tiny (~20 KB up per page, less down) and LAN latency is
  negligible — no throughput concern.
- This endpoint is **unauthenticated** (Ollama ignores `FS_LLM_API_KEY`).
  Fine on a trusted home network; never port-forward it to the internet. Use
  llama.cpp's `--api-key`, or an SSH tunnel, if you need it locked down.

---

## Hosted APIs (Anthropic, OpenAI, Google)

All three expose an OpenAI-compatible endpoint, so switching is `.env` only —
with three caveats.

**1. Data leaves the machine.** Review text and every extracted quote are sent
to the provider. The "nothing leaves the machine" property above no longer
holds. Check the provider's terms against `QUOTATION_POLICY.md` before a real
run, and make sure you are on a **no-training-on-input** plan:

- OpenAI API — does not train on API inputs by default.
- Anthropic API — does not train on API inputs.
- Google — the **free** Gemini tier trains on inputs; a billing-enabled
  (paid) key does not. Use a paid key.

**2. Pin a dated model.** Hosted models get silently updated and deprecated,
which breaks reproducibility. Use a snapshot name, not a floating alias.

**3. Keep the key out of git.** Put it in `.env` (git-ignored) or export it in
the shell. The `detect-secrets` pre-commit hook will catch an accidental
commit.

### OpenAI

```sh
# .env
FS_LLM_BASE_URL=https://api.openai.com/v1
FS_LLM_API_KEY=sk-...
FS_LLM_MODEL=gpt-4.1-2025-04-14        # example — pick a current dated snapshot
```

Native strict `json_schema` support — the best structured-output behaviour of
the three. System prompt is cached automatically.

### Google Gemini

```sh
# .env
FS_LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
FS_LLM_API_KEY=...                     # from https://aistudio.google.com/apikey (paid key)
FS_LLM_MODEL=gemini-2.5-flash          # or gemini-2.5-pro
```

Cheapest frontier option. The OpenAI-compat layer honours `response_format`.

### Anthropic

```sh
# .env
FS_LLM_BASE_URL=https://api.anthropic.com/v1/
FS_LLM_API_KEY=sk-ant-...
FS_LLM_MODEL=claude-sonnet-4-5-20250929   # example — pick a current dated snapshot
```

Anthropic's OpenAI-compat endpoint is real but **beta and partial** — in
particular its `response_format` `json_schema` handling is weaker than
OpenAI's. If extraction burns retries on shape errors, that is why; the fix
is a small native-`anthropic`-SDK adapter (a code change), not a config
tweak.

### Cost

~5k input + ~1k output tokens per page, retries included. Rough $/1,000
pages at early-2026 list prices:

| Model class | ~$/1k pages |
|---|---|
| Gemini 2.5 Flash, GPT-mini class | 3–5 |
| Claude Haiku | ~12 |
| Gemini 2.5 Pro | ~18 |
| GPT-4.1 / GPT-5 class | ~25 |
| Claude Sonnet | ~35 |

A weekly incremental run (a few hundred new pages) is cents to a couple of
euros. A one-time full backfill of ~10k pages is €30–50 on the cheap tier,
€100–350 on a frontier model — roughly half that with prompt caching of the
static system prompt.

---

## Hardware reality

Extraction speed is set by the machine, and it decides whether a local 27B is
practical.

| Machine | 7B Q4 | 27–32B Q4 | Verdict for a 27B |
|---|---|---|---|
| **2019 Intel Mac, CPU only** | ~65 s/page (measured) | ~4–5 min/page (extrapolated) | ~6–8 h for a 93-roundup pass. Fine unattended weekly; too slow to iterate on. Prefer a hosted API. |
| **Apple Silicon (M1 Pro / Max / M2 / M3+)** | a few s/page | ~30–90 s/page | Comfortable. Needs ~20 GB of unified memory free, so a 32 GB machine or larger. |

Measured baseline: `qwen2.5:7b` (Q4_K_M), one 5,395-character German roundup,
2019 Core i9-9980HK / 32 GB / **CPU only** (Ollama's Metal backend is Apple
Silicon only): **64.5 seconds**. No Apple Silicon figure has been measured;
the numbers above are estimates.

Memory rule of thumb: a 4-bit model needs roughly its file size in free RAM
plus a few GB for context. `gemma3:27b` at ~17 GB wants ~20–22 GB free.

---

## Choosing a model

`FS_LLM_MODEL` is only ever a config value — no code, schema or migration is
tied to any model. Develop against something small; run the real thing
against something larger, on another machine or a hosted API if you like.

### The axes that matter

Weigh candidates on these, roughly in order:

1. **German competence** — most sources are German. A model that is merely
   "multilingual" is not enough; it has to hold register and idiom.
2. **Instruction-following and JSON discipline** — the prompt is a structured
   schema with a rubric, not a chat.
3. **Verbatim copying** — the `quote` field must be the reviewer's exact
   words. A model that "tidies up" a sentence fails even when the meaning
   survives; `_drop_unverbatim_quotes` then discards the quote, so a sloppy
   model loses quotes rather than corrupting them — still a loss.
4. **Active parameters** — not the headline count (see below).
5. **Thinking mode** — none, or one you can turn off. A reasoning block
   before the JSON is wasted tokens and a parser hazard.
6. **Context ≥ 8k** — covers the longest roundup plus the prompt. All the
   candidates below clear this easily; it only rules out old 2k/4k models.
7. **Licence** — matters only if this project ships commercially. Apache-2.0
   (Mistral, Qwen) has no use restrictions; the Gemma licence permits
   commercial use but carries a prohibited-use policy you must pass through.
8. **Speed on your box** — see [Hardware reality](#hardware-reality). On the
   2019 Intel Mac the practical ceiling for a real run is ~14B; the 27–32B
   tier needs Apple Silicon or a hosted API.

### Active parameters, not the headline number

A mixture-of-experts model is named by its **total** size but runs only a
fraction per token. `qwen3:30b` is 30B total, **3B active**, and on
instruction-following and verbatim copying it behaves like a 3B model — which
is why the first real run with it produced non-verbatim quotes and dropped
facts. A dense model of the same nominal size, or an MoE with more active
parameters, is a different tool. Prefer dense models here unless you have
measured an MoE and it holds up.

### Candidates for a real run

Not decided — this is an open item in `DECISIONS_OPEN.md`. Compare them with
the method below, not by reputation. Sizes are the Ollama Q4 download; "min
free RAM" adds a few GB for context.

| Model | `FS_LLM_MODEL` | Params | Licence | Native ctx | Thinking | Disk (Q4) | Min free RAM |
|---|---|---|---|---|---|---|---|
| **Gemma 3 27B** | `gemma3:27b` | 27B dense | Gemma (custom) | 128k | none | ~17 GB | ~22 GB |
| **Mistral Small 3.2** | `mistral-small3.2` | 24B dense | Apache-2.0 | 128k | none | ~14 GB | ~18 GB |
| **Qwen3 32B** | `qwen3:32b` | 32B dense | Apache-2.0 | 32k | on by default — **disable it** | ~20 GB | ~25 GB |
| *(avoid)* Qwen3 30B-A3B | `qwen3:30b` | 30B total / **3B active** | Apache-2.0 | 32k | on by default | ~19 GB | ~24 GB |

**Trade-offs:**

- **Gemma 3 27B — the safe first pick.** Trained across 140+ languages, so
  German verbatim work is its strongest suit of the three; no thinking mode,
  nothing to configure. The catch is the licence: fine for a hobby build,
  needs a read before anything commercial.
- **Mistral Small 3.2 — pick this if the licence matters, or the machine is
  tight.** Apache-2.0, the smallest and fastest of the three, and Mistral's
  European focus means solid German and French. The 3.2 point release
  specifically fixed instruction-following and repetition regressions from
  3.1. Slightly less multilingual headroom than Gemma.
- **Qwen3 32B — the most raw capability, at a cost.** The *dense* 32B (not
  the 30B-A3B MoE) tops the three on most reasoning benchmarks and is
  Apache-2.0, but you must disable thinking (next section), it is the
  slowest, and Qwen is the family most prone to leaking CJK characters into
  non-Chinese text — exactly the failure seen in one `qwen3:30b` quote.
- **Do not use `qwen3:30b`.** 3B active parameters is the problem this whole
  section is about.

### Development / smoke-test models

Not for a real corpus — for checking the plumbing and iterating on the
prompt, where speed beats quality:

| Model | `FS_LLM_MODEL` | Disk (Q4) | Note |
|---|---|---|---|
| Qwen2.5 7B | `qwen2.5:7b` | ~4.7 GB | Apache-2.0, no thinking. The measured baseline; runs anywhere. |
| Gemma 3 12B | `gemma3:12b` | ~8 GB | Same family as the 27B, so behaviour scales predictably when you move up. |
| Qwen2.5 0.5B | `qwen2.5:0.5b` | ~0.4 GB | Proves the request path works. Output is not usable. |

### Disabling "thinking" (Qwen3 only)

Gemma 3 and Mistral Small have no reasoning mode — nothing to do.

Qwen3 emits a `<think>…</think>` block before its answer by default. For
extraction that is wasted tokens and, on a weak JSON parser, a broken
response. Its built-in switch is the string `/no_think` in a system or user
message — but **the extractor sends a fixed system prompt and does not add
it**, and Ollama's Modelfile `SYSTEM` only applies when the request has no
system message, so that route does not work here. Options:

- **Use llama.cpp** and pass `--reasoning-budget 0` (see that section). No
  code change.
- **Patch the prompt**: add a line `/no_think` to the end of the prompt file
  `extraction/prompts/extract_v3.txt`. `PROMPT` is read from that file and
  `prompt_sha` is derived from it, so every record correctly reflects the
  changed prompt.
- **Just pick Gemma 3 or Mistral Small** and avoid the question.

### Comparing models

Re-run extraction on a fixed set of raw items and score two things, neither
of which needs a human to read the reviews:

1. **Quote fidelity** — the share of quotes that survive
   `_drop_unverbatim_quotes` (which drops any quote not found verbatim in the
   text the model was shown). The first `qwen3:30b` run scored 34/48. See
   `QUOTATION_POLICY.md`.
2. **Fact carry-through** — where a `<review>` block supplied the outlet, URL
   or date, did that value reach the output, or did the model ignore it and
   re-derive from prose? `qwen3:30b` dropped the supplied `published_at` on
   most hall9000 reviews.

---

## Settings

All optional except `FS_LLM_MODEL`.

| Variable | Default | Notes |
|---|---|---|
| `FS_LLM_BASE_URL` | `http://localhost:11434/v1` | Any OpenAI-compatible endpoint, local or hosted. |
| `FS_LLM_MODEL` | `llama3.2` | **Set this.** The default is a placeholder. |
| `FS_LLM_API_KEY` | `not-needed` | Real key for a hosted API; local servers ignore it but the client refuses to start empty. |
| `FS_LLM_TIMEOUT` | `120.0` | Seconds per call. Raise it if the first (cold) call times out. |
| `FS_LLM_MAX_ATTEMPTS` | `3` | Total tries per item, including the first. |

---

## Verifying

Does the endpoint accept the request shape at all:

```sh
curl -s "$FS_LLM_BASE_URL/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $FS_LLM_API_KEY" \
  -d '{"model":"'"$FS_LLM_MODEL"'",
       "messages":[{"role":"user","content":"Return JSON: {\"ok\": true}"}],
       "response_format":{"type":"json_schema","json_schema":{"name":"t",
         "strict":false,"schema":{"type":"object",
         "properties":{"ok":{"type":"boolean"}},"required":["ok"]}}}}'
```

A server that rejects `json_schema` may still accept `{"type":"json_object"}`;
either works, since pydantic is the real check.

End to end, on one real page:

```sh
uv run python -m finalscoring.scraping spiel-des-jahres   # writes raw items
```

```python
import json
from finalscoring.scraping.item import RawItem
from finalscoring.extraction import ReviewExtractor

with open("data/results/<the file the crawl wrote>.jl") as f:
    item = RawItem.model_validate(json.loads(f.readline()))

record = ReviewExtractor().extract(item)
print(len(record.result.reviews), "reviews")
```

---

## Troubleshooting

**`ExtractionFailed: ... model 'llama3.2' not found`** — `FS_LLM_MODEL` is
still the placeholder. Set it to something you have pulled (`ollama list`).

**`ExtractionFailed: ... Request timed out` on the first call only** — the
first request also pays to load the model into RAM. Raise `FS_LLM_TIMEOUT` or
warm the model first (`ollama run <model> "hi"`).

**Connection refused** — `ollama serve` (or `llama-server`) is not running.
`curl -s http://localhost:11434/api/version` should answer for Ollama.

**Connection refused from another machine, but fine locally** — Ollama is
bound to `127.0.0.1`. Set `OLLAMA_HOST=0.0.0.0:11434` on the model host (see
[Local network](#local-network-model-on-another-machine)), or `--host
0.0.0.0` for llama.cpp. Check the model host's firewall too.

**Extraction finds too few reviews on long pages** — the context window is
too small and the article is being truncated. On Ollama, raise `num_ctx` (see
the Modelfile step); on llama.cpp, raise `--ctx-size`.

**Extraction finds too few reviews on short pages** — that is a
model-capability limit, not a setup problem. A roundup citing four critics
that yields one is a known weakness of small models.

**Quotes keep coming back `null`** — the model is paraphrasing rather than
copying, and `_drop_unverbatim_quotes` is discarding the results. Try a
stronger model; check the extraction logs for the `discarding non-verbatim
quote` lines.

---

## Not covered

**vLLM** is the fastest backend for a real backfill, with strict token-level
schema enforcement, but it requires an **NVIDIA GPU** (or ROCm / TPU) — no
Metal, no meaningful CPU path. If you get a GPU box, `vllm serve <hf-repo>
--port 8000` exposes the same OpenAI API and only `FS_LLM_BASE_URL` /
`FS_LLM_MODEL` change.
