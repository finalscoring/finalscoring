# syntax=docker/dockerfile:1.6
#
# Final Scoring image.
#
# This image bakes the SQLite database into the artifact. The build runs:
#   1. Install Python deps.
#   2. Import Recommend.Games game data (if RECOMMEND_GAMES_IMPORT is set).
#   3. Replay scraped review JSONL into the database.
#   4. Compute aggregates and confidence intervals.
#   5. Materialize a read-only SQLite file at /app/data/final_scoring.db.
#
# The runtime stage carries only Python + the built database + the frontend.
# There is no live writer in production; rebuilds happen elsewhere and
# produce a new image.

# ─────────────────────────────────────────────────────────────────────────
# Stage 1: builder — heavy deps, build SQLite from JSONL inputs
# ─────────────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# System deps for lxml, scrapy, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libxml2-dev \
        libxslt1-dev \
        sqlite3 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src/ ./src/
COPY prompts/ ./prompts/

RUN pip install --no-cache-dir .

# Inputs to the build: scraped JSONL, override tables, optional RG import.
# These are mounted or copied in by the CI / local build invocation.
COPY data/ ./data/

# Run the build. Produces /build/data/final_scoring.db.
# The build script reads from data/results/*.jl and writes the SQLite file.
RUN fs build --db-path /build/data/final_scoring.db --strict

# ─────────────────────────────────────────────────────────────────────────
# Stage 2: runtime — minimal image carrying the baked DB and the frontend
# ─────────────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        sqlite3 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash fs

# Copy just the runtime parts. We do not need scrapy or the LLM client
# at runtime — the database has already been built.
COPY --from=builder /build/data/final_scoring.db /app/data/final_scoring.db
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/fs /usr/local/bin/fs

# Frontend assets (when frontend/ is built — placeholder for now).
# COPY --from=frontend-builder /frontend/out /app/frontend

USER fs

ENV FS_DB_PATH=/app/data/final_scoring.db \
    PYTHONUNBUFFERED=1

EXPOSE 8000

# Replace with the real frontend server once it exists.
CMD ["fs", "serve", "--host", "0.0.0.0", "--port", "8000"]
