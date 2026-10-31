# YEP Portal

Integrated management portal for Young Engineers Prishtina.

## Requirements

- Python 3.12 and [uv](https://docs.astral.sh/uv/)
- Node.js 22 LTS and pnpm
- Docker with Compose

## Start the foundation

1. Copy `.env.example` to `.env` and replace development secrets.
2. Run `docker compose up -d`.
3. Run `cd apps/api && uv sync --all-groups`.
4. Run `uv run alembic upgrade head`.
5. Run `uv run uvicorn app.main:app --reload`.

The health endpoints are `GET /health/live` and `GET /health/ready`.

## Quality checks

From `apps/api`:

```text
uv run ruff format --check .
uv run ruff check .
uv run mypy app
uv run pytest
```

