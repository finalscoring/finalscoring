# Decisions

This directory records significant architectural and editorial
decisions, lightweight-ADR style. The format for each entry:

```
NNN-short-slug.md
```

Each file documents one decision with:

1. **Context** — what situation forced the decision.
2. **Decision** — what was chosen.
3. **Consequences** — what that commits us to and what it precludes.

Decisions are append-only. Superseding an earlier decision means
adding a new record that references the old one — not editing the old
one in place.

## Index

- [001 — SQLite baked into Docker image](001-sqlite-baked-into-image.md)
- [002 — Local open-weights LLM for extraction](002-local-llm.md)
- [003 — AGPLv3 license](003-agplv3.md)
- [004 — Per-critic z-score with sample-size threshold](004-z-score-normalization.md)
- [005 — Bootstrap percentile CIs](005-bootstrap-ci.md)
- [006 — Multilingual from day one](006-multilingual-launch.md)
- [007 — Single 0–100 score with confidence interval](007-score-display.md)
- [008 — Broad ingestion with tier weighting](008-broad-ingestion.md)
