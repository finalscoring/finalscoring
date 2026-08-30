# Scraping runtime: one image, one spider per `docker compose` service.
# The extraction / load / scoring stages are not in here — see docs/ARCHITECTURE.md.
FROM python:3.14-slim

ENV PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    PATH=/app/.venv/bin:$PATH

ARG UV_VERSION=0.12.6
RUN pip install --no-cache-dir "uv==${UV_VERSION}"

WORKDIR /app

# Dependencies first, so the layer survives source-only changes.
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src ./src
RUN uv sync --frozen --no-dev

ENTRYPOINT ["python", "-m", "finalscoring.scraping"]
