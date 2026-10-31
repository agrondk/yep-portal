# PROGRESS.md — YEP Portal build log

## Current position
- Module: M01 complete
- Next sub-step: M02-A (awaiting owner approval)
- Last updated: 2026-11-01

## Module status
| Module | Status | Sub-steps done | Tests passing | Notes |
| --- | --- | --- | --- | --- |
| M00 Foundation | done | A, B, C, D, E | API health, migrations, Ruff, TypeScript and Next build passing | MinIO registry pull remains external blocker |
| M01 Catalog & public site | done | A, B, C | 20 API tests, 2 Playwright tests, Ruff, mypy, TypeScript and Next build passing | Public catalog and staff workflows complete |
| M02–M21 | todo | | | See `YEP_Portal_Prompts/00_README_HOW_TO_USE.md` |

## Key files
- Models: `apps/api/app/modules/core/models.py`
- Migration: `apps/api/alembic/versions/20261025_0001_m00_foundation.py`
- Permission matrix: `docs/permission-matrix.md`
- Audit actions: `docs/audit-actions.md`

## Decisions
- 2026-10-25: Used the master defaults: one EU VPS, portal subdomain, manual launch payments, configurable SMTP, Europe/Belgrade timezone, Albanian default locale.
- 2026-10-25: Added a separate ephemeral PostgreSQL service on port 5433 for integration tests.
- 2026-10-25: Verification and password-reset tokens are returned only in development until M00-D supplies the outbox mail adapter.
- 2026-10-25: Added a process-local application rate limiter; production must also enforce limits at the reverse proxy because multi-process counters are not shared.
- 2026-10-26: User explicitly approved proceeding through M00-D, M00-E and into M01.
- 2026-10-26: M00 permissions are declared in code and the documentation is generated from that declaration.
- 2026-10-31: M01 catalog records are seeded as drafts with all confirmation flags false; Web Development is explicitly proposed.
- 2026-11-01: Public inquiry/trial submissions use honeypot and per-IP rate limits; staff workflows use explicit one-way state machines and audit every assignment, schedule and transition.
- 2026-11-01: M01 public pages are bilingual and only consume publication-gated offerings; staff screens include catalog registers, a bilingual program editor, confirmation checklist, inquiry board and trial board.

## Incomplete / known gaps
- Official MinIO images currently return a registry `401`; private-file unit behavior is verified, but the MinIO container is not running.
- Full authorization journeys still need dedicated PostgreSQL integration coverage beyond the current unit/smoke checks.

## Verification evidence
- 2026-10-25: `python -m compileall -q apps/api/app apps/api/tests apps/api/alembic` passed.
- 2026-10-25: Re-ran the compile check after M00-B; all auth source, tests and migrations passed syntax compilation.
- 2026-10-26: M00-C source, tests and scripts passed Python syntax compilation; runtime authorization tests remain blocked by the missing toolchain.
- 2026-10-31: Python 3.12 environment resolved with `uv`; all 11 collected unit tests reached 100% and Ruff passed. The pytest process did not return its final exit summary before the runner timeout; PostgreSQL integration checks remain pending Docker health.
- 2026-10-31: Docker/WSL healthy; PostgreSQL 16, test PostgreSQL, Redis and Mailpit started; Alembic reached `20261031_0003 (head)`; `/health/live` and `/health/ready` returned `ok`.
- 2026-10-31: M00-E generated the OpenAPI TypeScript contract, passed strict TypeScript checking, produced a successful Next.js 15 production build, and served `/sq/login` with HTTP 200.
- 2026-10-31: M01-A passed Ruff and strict mypy; three catalog rule tests passed; Alembic reached `20261031_0004 (head)`; seven draft programs were verified in PostgreSQL; the regenerated TypeScript contract contains the catalog routes; the public endpoint returned zero offerings, confirming drafts are hidden.
- 2026-11-01: M01-B passed all 20 API tests, Ruff and strict mypy; Alembic reached `20261031_0005 (head)`; eight inquiry/trial routes were verified in OpenAPI; the TypeScript contract was regenerated and the Next.js production build passed.
- 2026-11-01: M01-C added migration `20261101_0006`, FAQ and filtered public offering APIs, bilingual public and staff pages, inquiry/trial forms and workflow boards. Next production build passed and both Playwright tests passed in system Chrome, including published-visible/draft-hidden catalog behavior.

## Blockers needing the owner
- None for M01. Resolve the external MinIO registry access before exercising live file uploads.

## Commands
- Start infra: `docker compose up -d`
- API setup: `cd apps/api && uv sync --all-groups`
- Migrate: `cd apps/api && uv run alembic upgrade head`
- API: `cd apps/api && uv run uvicorn app.main:app --reload`
- Test: `cd apps/api && uv run pytest`
- Quality: `cd apps/api && uv run ruff format --check . && uv run ruff check . && uv run mypy app`
