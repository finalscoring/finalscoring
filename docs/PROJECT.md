# Final Scoring — Project Context

This document records what the project is and what has actually been
decided. It exists so an agent can pick up work without re-deriving
context or inventing choices. Anything not in this file or in
`DECISIONS_OPEN.md` has not been decided — if a task needs it, ask the
maintainer; do not assume.

## What the project is

Final Scoring is a critic-focused review aggregation index for board
games — a "Metacritic for board games". It collects, organises and
summarises critical opinion from board game reviewers, critics and media
sources, giving readers a sense of a game's overall critical reception.

Positioning:

- The product is editorial: it helps players understand whether a game is
  broadly praised, divisive, overlooked, controversial or criticised by
  reviewers.
- It is NOT a replacement for BoardGameGeek, community rating platforms,
  or recommendation engines.
- The distinction between critic/reviewer opinion and community/user
  opinion must be preserved throughout. Do not drift into generic board
  game database, recommendation engine, or social platform concepts
  unless explicitly asked.

Brand:

- Public name: "Final Scoring". This is the definitive brand identity.
- "Metacritic for board games" is positioning shorthand, not the name.
- Domain `https://finalscoring.games/` is secured. A placeholder is
  currently online there; nothing about the placeholder's content,
  numbers, or layout is decided or final.
- Desired brand feel: credible, clear, neutral, board-game-native — a
  trustworthy critical index, transparent about sources, careful with
  summaries, respectful of reviewer nuance.

## Out of scope (confirmed)

Permanently out of scope for the core product: community ratings, user
accounts, social features, recommendation features, and general
collection-management functionality.

## Mantras (confirmed, binding)

1. **Critic opinion, aggregated — nothing else.** (We report what reviewers say: not community ratings, not our own verdicts, not a database, recommender, or social platform.)
2. **100% open source, full transparency.**
3. **No tracking, ever.**

## Confirmed technical decisions

These have been explicitly agreed by the maintainer.

- **Language/runtime:** Python, targeting Python 3.14. This is a project,
  not a library — favour reliability and concreteness over
  generalisation. (See `pyproject.toml`.)
- **License:** AGPLv3 (`AGPL-3.0-or-later`). Applies to the whole
  repository. `LICENSE` file is present.
- **Hosting/VCS:** GitLab. The repository lives on gitlab.com. Do NOT
  introduce GitHub, GitHub Actions, or any GitHub-specific tooling or
  URLs. Do not assume any CI provider, container registry, or hosting
  platform that has not been explicitly chosen.
- **Build/packaging:** hatchling backend, `src/finalscoring` layout, as
  specified in `pyproject.toml`.
- **Tooling:** ruff (lint + format) and ty (type checking), pytest for
  tests, all pinned in `pyproject.toml` dev extras. The package is typed
  (`py.typed` present).
- **Database / distribution pattern:** SQLite, built at deploy time and
  baked into the deployable image, mirroring the maintainer's existing
  Recommend.Games approach (scrape → JSON Lines → merge/dedupe → build a
  full new SQLite file per release, baked into the image). There is no
  live runtime database and no migration system; each build produces a
  fresh database from sources. This pattern is confirmed as the intended
  approach, at least through proof-of-concept, and is considered a good
  fit because the workload is read-mostly and batch-updated.
- **Repository structure:** monorepo. One Python package for the backend;
  the frontend, when it exists, lives in its own top-level directory in
  the same repo.
- **LLM hosting:** local open-weights model, accessed via an
  OpenAI-compatible endpoint. The model is only needed at build/ingestion
  time, not at runtime. The maintainer's existing pipeline already uses a
  configurable OpenAI-compatible client, so the model is a config value.
- **Build cadence:** weekly is sufficient.
- **Score display:** a single 0–100 score, accompanied by a confidence
  interval (e.g. "85, range 67–91") rather than a bare number. The
  maintainer likes showing distribution but wants a simple headline
  number with a CI as the chosen compromise.
- **Score normalization approach:** per-reviewer normalization
  (z-score-style, per critic) so that reviewers with different scoring
  habits are comparable. The maintainer raised this; it is the agreed
  direction. (Exact thresholds/parameters are NOT yet decided — see
  `DECISIONS_OPEN.md`.)
- **Source/critic strategy:** treat this as a data problem — crawl as
  broadly as possible, include every possible reviewer, and assign low
  weight to low-quality sources rather than excluding them. Weighting is
  the mechanism for quality differentiation.
- **Languages:** multilingual and international from the beginning.
  German and English reviews from the start, designed with expansion to
  further languages in mind.

## Existing assets the maintainer already has

- **Recommend.Games** (sister project): comprehensive board game data
  from BGG and other sources (including Luding), covering game data,
  ratings, and user comments. Runs on SQLite, built and baked into a
  Docker image per release. How (or whether) its data and infrastructure
  are reused in Final Scoring is not yet decided (see `DECISIONS_OPEN.md`).
- **Spiel des Jahres project:** an existing, simple, proof-of-concept
  review spider (Scrapy `SitemapSpider`) and an LLM extraction pipeline
  using structured outputs (Pydantic schema via an OpenAI-compatible
  client, with tenacity retries and token accounting). The maintainer
  describes these as proof-of-concept quality. They are a starting point
  to learn from, not a finished component to port wholesale.

## Working method (how to collaborate on this repo)

These are explicit maintainer requirements, learned the hard way:

- Work in small, reviewable chunks. One change set should be what an
  experienced developer who actually wants their code reviewed would put
  into a single commit. Stop after each chunk and let the maintainer
  review.
- Do the literal scope of the request and nothing more. When asked to
  scaffold or create structure, create directories and minimal
  placeholder/stub files only — do NOT implement logic, port code, or
  author extra docs.
- Do not make implementation or design decisions on the maintainer's
  behalf. Propose options and let them decide. Architecture and design
  choices are reserved for the maintainer.
- Do not assume tooling, platforms, or services that were never
  mentioned. When something isn't specified, ask or leave it out.
- Do not fabricate content that must be exact (e.g. license text). If it
  can't be obtained correctly, leave it out and flag it.
