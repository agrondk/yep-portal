# PROGRESS.md — YEP Portal build log

> Copy this file to the repo root as `PROGRESS.md`. The assistant updates it at the end of every sub-step.
> Keep it short: it is attached to every session.

## Current position
- Module: M00
- Next sub-step: A
- Last updated: YYYY-MM-DD

## Module status
| Module | Status (todo / in progress / done) | Sub-steps done | Tests passing | Notes |
| --- | --- | --- | --- | --- |
| M00 Foundation | todo | | | |
| M01 Catalog & public site | todo | | | |
| M02 Families, applications, enrollment | todo | | | |
| M03 Scheduling & classes | todo | | | |
| M04 Attendance, progress, certificates | todo | | | |
| M05 Schools, partners, proposals | todo | | | |
| M06 Billing, payments, ledger | todo | | | |
| M07 Instructors & staff hours | todo | | | |
| M08 Inventory & assets | todo | | | |
| M09 Expenses, suppliers, budgets | todo | | | |
| M10 Communications | todo | | | |
| M11 Franchise reporting | todo | | | |
| M12 Dashboards, reporting, sponsors | todo | | | |
| M13 Historical data & imports (since Jun 2022) | todo | | | |
| M14 Loans & cash accounts (deferred) | todo | | | |
| M15 Hardening & release | todo | | | |
| M16 Feedback & surveys | todo | | | |
| M17 ML predictions | todo | | | |
| M18 AI assistant | todo | | | |
| M19 Marketing & social media | todo | | | |
| M20 Staff training & onboarding | todo | | | |
| M21 Camps & events | todo | | | |

## Key files (update as they are created)
- Models: `apps/api/app/modules/<module>/models.py`, migrations in `apps/api/alembic/versions/`
- Permission matrix: `docs/permission-matrix.md`
- Audit actions: `docs/audit-actions.md`
- Job registry: `apps/api/app/jobs/registry.py`

## Decisions (assumptions made, with date)
- 

## Incomplete / known gaps
- 

## Blockers needing the owner
- 

## Commands
- Start infra: `docker compose up -d`
- API: `cd apps/api && uv run uvicorn app.main:app --reload` · worker: `uv run celery -A app.worker worker -B`
- Web: `cd apps/web && pnpm dev` · regenerate API client: `pnpm gen:api`
- Migrate: `cd apps/api && uv run alembic upgrade head` (new: `uv run alembic revision --autogenerate -m "<module>"`)
- Seed demo: `uv run python -m app.cli seed-demo`
- Test: `uv run pytest` (API) · `pnpm test` and `pnpm e2e` (web)
