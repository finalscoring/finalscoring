# 002 — Local open-weights LLM for extraction

**Status:** Accepted.
**Date:** 2026-05.

## Context

The LLM extraction stage processes scraped review text into structured
records (see `prompts/review_extraction/v1.md`). The workload has
three properties that matter for the hosting choice:

1. **Batch.** Extraction runs during weekly builds, not in response to
   user requests. Latency is not a concern.
2. **Public input data.** The texts being processed are public web
   pages; no privacy considerations.
3. **Structured output.** Reliability depends on the model emitting
   schema-valid JSON, not on free-form prose quality.

For (3), constrained-decoding tooling on open-weights stacks (vLLM
`guided_json`, Ollama schema constraints, llama.cpp GBNF) is now
mature enough that a 14–32B local model produces schema-valid output
indistinguishable from hosted providers.

The cost model also matters for a side project: hosted-API costs
accrue per build, indefinitely. A local model is a one-time hardware
cost (or none, if a GPU is already available).

## Decision

The LLM extraction stage runs against a local open-weights model
served by an OpenAI-compatible endpoint (vLLM or Ollama). Default
model: Qwen 2.5 14B Instruct, with constrained decoding for
structured output.

The extraction code talks to the model exclusively through the
OpenAI-compatible interface — there is no model-specific code in the
extraction layer. Switching to a different open-weights model, or to
a hosted provider (OpenAI, Anthropic via a proxy, etc.), is a
configuration change: set `LLM_API_BASE_URL`, `LLM_API_KEY`, and
`LLM_MODEL`.

## Consequences

**Committed to:**
- The build host needs GPU access (or CPU patience for Ollama).
  Production does not — the LLM is not called at runtime.
- Model and prompt versions land on every `Review` row's
  `extraction_model_version` field, so a future migration to a
  different model is auditable.
- The multilingual mantra requires a model with strong German plus
  English capability. Qwen 2.5 and Mistral Small both qualify; this
  shapes future model choice.

**Precluded:**
- Reliance on hosted-provider features that don't have local
  equivalents (e.g. provider-specific tool use, very long contexts
  beyond what the local model supports).

## Reversibility

Trivial. Change three env vars and the same code runs against any
OpenAI-compatible endpoint. The consensus snapshot feature (v2) may
selectively use a hosted endpoint for that specific call if local
quality on multi-document synthesis proves insufficient; the
architecture supports mixing.
