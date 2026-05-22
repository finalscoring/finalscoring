# 001 — SQLite baked into Docker image

**Status:** Accepted.
**Date:** 2026-05.

## Context

Final Scoring is a read-mostly publication of critical reception.
Reviews land on the order of days; readers consume the same data
hundreds or thousands of times between updates. There is no writable
runtime state (no user accounts, no comments, no ratings — see the
mantras and `docs/scope.md`).

The conventional default for a web service of this shape is Postgres
plus a long-running app server, plus migrations, plus backups, plus a
managed-database bill. For a one-person side project that must
survive months of inattention, every one of those is an operational
liability.

Recommend.Games — the sister project that ships its data and
recommender model in the same way — has used a SQLite + bake-into-image
pattern stably for nearly a decade. The same operational reasoning
applies here, with one additional point in favor: Final Scoring has
*less* live state than Recommend.Games (no recommender model
artefacts), making the fit even tighter.

## Decision

The Final Scoring database is SQLite. It is built at deploy time from
sources (Recommend.Games game import + scraped review JSONL +
versioned override tables) and baked into the runtime Docker image.
There is no live database in production. Builds happen weekly in CI;
each produces a new image.

The schema is materialized from `SQLModel` definitions in
`src/final_scoring/schema/`. There is no migration system — the schema
is whatever the code on the active branch says it is. Schema changes
are deployed by the same mechanism as code changes: a new image with
a freshly-built database.

## Consequences

**Committed to:**
- All editorial state lives in version-controlled files
  (`data/overrides/*.csv`, prompts, scoring config). There is no
  database UI to edit a critic record — you edit the CSV and rebuild.
- Build cadence is the floor on data freshness. Weekly is the
  declared cadence; faster is possible but not free (CI time, build
  host availability).
- Every deploy is atomic and trivially rollback-able.
- Backups are free (every image is a snapshot).
- Open-source distribution is straightforward: the image contains
  everything needed to run a copy.

**Precluded:**
- User accounts and any writable runtime state.
- Real-time updates between builds.
- Multi-writer ingestion (not a problem — ingestion is a build step,
  not a runtime concern).

## Reversibility

Low cost to revisit if scope assumptions change. The SQLModel schema
maps cleanly onto Postgres; switching backends would require
re-deriving the build process but no application code changes. We do
not expect to revisit this.
