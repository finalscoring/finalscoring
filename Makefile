.PHONY: db-up db-down migrate api worker web test lint

db-up:
	docker compose up -d db

db-down:
	docker compose down

migrate:
	cd packages/py/finalscoring && uv run alembic upgrade head

api:
	cd apps/api && uv run uvicorn finalscoring_api.main:app --reload

worker:
	cd apps/worker && uv run python -m finalscoring_worker.cli --help

web:
	cd apps/web && pnpm dev

test:
	cd packages/py/finalscoring && uv run pytest
	cd apps/api && uv run pytest
	cd apps/worker && uv run pytest

lint:
	cd packages/py/finalscoring && uv run ruff check . && uv run ruff format --check .
	cd apps/api && uv run ruff check . && uv run ruff format --check .
	cd apps/worker && uv run ruff check . && uv run ruff format --check .
