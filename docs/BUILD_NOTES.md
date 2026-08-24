# Build Notes — A Possible Sequence of Reviewable Chunks

This is a memo, not a plan of record. It sketches how the work *could*
be broken into small commits, each reviewable on its own, each leaving
the repo green. It is the brainstorming behind the build, written down
so it isn't lost — not a script to execute. Reorder, merge, split, or
skip as judgement dictates. Anything in `DECISIONS_OPEN.md` must be
settled with the maintainer before the relevant chunk, not assumed here.

Guiding test for each chunk: *what would an experienced developer who
wants their code reviewed put into a single change set?* One concern,
small diff, tests where they make sense, repo stays installable and
green.

---

## Phase A — Foundation

### A1. Project skeleton (done)
`pyproject.toml`, `src/finalscoring/__init__.py`, `py.typed`,
`README.md`, `LICENSE`, `.gitignore`, empty `tests/`. The repo installs,
ruff/ty/pytest run green on an empty tree. Already in place.

### A2. Settings/config object
A single typed config (env-driven) for the values the rest of the code
will need: LLM endpoint/model, scraper politeness, DB output path.
Plus a `.env.example` documenting them.
Small, no logic, easy to review. Nothing imports it yet — that's fine;
it lands before the code that needs it so later diffs stay focused.
*Decision needed first:* none beyond what's already agreed, but keep it
minimal — only add a setting when a later chunk will actually read it.

---

## Phase B — Schema (one entity per chunk)

The data model is the spine; every later component depends on it. The
mistake to avoid is landing all tables in one diff. One entity per
commit, each with its own focused test.

*Settled since this memo was written:* the data-access choice is SQLModel
and the game record came first — see `PROJECT.md`. Phase B is built; the
chunks below stand as the record of how it was sequenced.

### B1. DB bootstrap
The minimal "create an empty database file with no tables" helper plus
its test. Establishes where the SQLite file lives and how the schema
gets materialised, without committing to any table yet. Path sketch:
`src/finalscoring/db.py` (or a `schema/` package — maintainer's call).

### B2. First entity: the game record
Likely thin: a BGG id as the canonical key plus a handful of metadata
fields. One model, one round-trip test (insert, read back). No import
logic yet — just the shape.
*Decision needed first:* where game data comes from (D1 / Recommend.Games
integration) is open; this chunk defines only the shape, not the source.

### B3. Critic/source record
The reviewer or outlet. Fields likely include identity, language,
medium, and a quality-weight. The weight field is where the
"broad-crawl-with-weighting" strategy lives, so its presence is a real
review point.

*As built:* this became two entities and two chunks — `outlets` (slug,
name, url, medium, weight) and `critics` (id, name, weight) — leaving
two weight fields whose interaction is still open, and no language on
either. See `DECISIONS_OPEN.md`.

### B4. Review record
One critic's verdict on one game — the heart of the model. This is where
the declared-vs-inferred score distinction, the short attributed quote,
the language, and the provenance (url, date) all live. Worth its own
careful review; arguably the most important diff in the project.

### B5. Aggregate/derived record
The computed per-game result (score, confidence interval, distribution,
review count). Derived, rebuilt each build. Lands after the inputs it
summarises exist.

(Override/alias tables — manual game-match fixes, critic-name aliases —
can each be their own small chunk if and when matching needs them.
Don't pre-build them.)

---

## Phase C — Ingestion

The existing SdJ spider + LLM pipeline is proof-of-concept to learn
from, not to port wholesale. Rebuild deliberately.

### C1. Raw item shape
Define the single record shape every source produces (url, source id,
raw text, basic metadata). This is the contract between scraping and
extraction. Tiny, no fetching yet.

### C2. LLM extraction — schema only
The Pydantic structured-output schema for an extracted review, plus a
versioned prompt living as a file (not a string literal), plus a unit
test that the schema validates expected shapes. No network call yet.
*Decision needed first:* the extracted-review field set overlaps the
Review entity (B4); keep them consistent. Quote length is capped at 300
characters at the schema level for copyright safety — settled, see
`PROJECT.md`. The reasoning, and the practices that matter more than the
number, are in `QUOTATION_POLICY.md`.

### C3. LLM extraction — the call
Wire the schema to the OpenAI-compatible client with retries. Testable
against a stub/mock so it stays green without a live model.
*Decision needed first:* model + serving stack are open.

### C4. First spider
One concrete source end-to-end producing raw items. Start with the
source whose structure is best understood. Output to JSON Lines, matching
the Recommend.Games pattern. Run manually, eyeball output, iterate.

### C5. Generalise the spider pattern
Only after 2–3 concrete spiders exist, extract whatever base/shared
pieces are genuinely common. Resist abstracting before there's evidence
of the right abstraction.

---

## Phase D — Resolution & load

### D1. Game-title → BGG id resolution
Build the logic that maps a game title (and other metadata) to a
canonical BGG id, using R.G.'s BGG game data as the lookup. Expect a
manual override path for the inevitable misses.
*Decision needed first:* how to access R.G.'s game data is open and
blocks this chunk. See `DECISIONS_OPEN.md`.

### D2. JSON Lines → SQLite load
Read extracted reviews, resolve game + critic, dedupe, insert. The step
that turns intermediate files into the queryable database.
*Decisions needed first:* the stream layout, the `ExtractedReview` →
`Review` field mapping, how `raw_score` is parsed onto the 0–100 scale,
and the dedupe key with its which-one-wins rule — the schema carries no
uniqueness constraint, so this step is the only thing standing between a
twice-cited critic and a skewed aggregate. See `DECISIONS_OPEN.md`.

---

## Phase E — Scoring

Pure functions, highly testable, no I/O. Each sub-step is its own chunk
with its own tests.

*Decision needed first (blocking E):* normalization thresholds, weighting
scheme, and CI method are open. The *shape* (per-critic normalization +
tier weighting + bootstrap-or-other CI) is agreed; the parameters are
not.

### E1. Per-critic normalization
Adjust each review's score against its critic's own distribution.
Property-style tests (an inflated critic's scores move toward the mean,
outputs stay in range). The map from the extractor's 1–10 rating onto the
0–100 scale is *not* here — `reviews.declared_score`/`inferred_score` are
already 0–100, so that conversion belongs to D2. See
`SCORING_SKETCH.md`.

### E2. Per-game aggregation with weights
Tier-weighted combine into a single 0–100 score. Honour the minimum
review threshold (games below it get no aggregate).

### E3. Confidence interval
Compute the CI shown alongside the score. Reproducible (seeded if
bootstrap). Tests: agreement narrows it, disagreement widens it, single
review degenerates cleanly.

---

## Phase F — Build orchestration

### F1. Build entry point
A single command that runs the pipeline end-to-end: init schema → import
games → load reviews → score → finalise the SQLite file. Each step a
small, logged, idempotent function. Build green against an empty
workspace first (produces a valid empty DB), then against real inputs.

### F2. Bake into image
Package the built SQLite file into the deployable artifact, mirroring the
Recommend.Games approach.
*Decision needed first:* container/build tooling and registry are
unspecified — do not assume. GitLab is the VCS; CI specifics are open.

---

## Phase G — Frontend
Deferred entirely. Stack undecided. Design against real data, not
imagined data — i.e. not before Phase E produces meaningful output.

---

## Cross-cutting reminders

- One concern per chunk; repo stays installable and green after each.
- Tests live with the code they cover; pure logic (Phase E) deserves the
  most.
- Prompts and scoring parameters are versioned artefacts — when they
  change, the change is itself a reviewable, documented diff.
- Settle the relevant `DECISIONS_OPEN.md` item *before* the chunk that
  depends on it. If a decision is missing, the chunk is "ask the
  maintainer", not "guess".
- The SdJ spider and LLM pipeline are reference material, not components
  to copy in.
