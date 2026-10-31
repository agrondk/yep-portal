# YEP Portal — Master Context (attach to EVERY session)

Act as a senior software architect and full-stack engineer. You are building, module by module,
a single integrated management portal for **Young Engineers Prishtina (YEP)**. This file holds the
facts, stack, and conventions every module must follow. The module prompt says *what* to build now;
this file says *how*. If the two conflict, this file wins unless the module prompt explicitly overrides it.

---

## 1. Organization facts (do not invent beyond these)

- YEP is a STEM education provider in Prishtina, Kosovo, a franchise of the international **e2 Young Engineers** network.
- Overall audience: children aged 4–16. Each program has its own configurable eligibility.
- Teaching through hands-on construction, engineering, robotics and coding, delivered at the learning
  center, at partner schools and kindergartens, and through sponsor-funded community initiatives.
- Programs (seed as **draft** catalog records, details unconfirmed): Big Builders, AlgoBuddy,
  Bricks Challenge, Algo Play (normalise "AlgoPlay" to this), Galileo Technic, Young Coders,
  Web Development with HTML & CSS (proposed — never shown as open without admin confirmation).
- Other activities: educational birthdays, holiday camps, workshops, inclusive learning activities,
  organizational team building.
- Contact: +383 48 108 128 · yep_info@youngengineers.org · yep_support@youngengineers.org ·
  https://prishtina.youngengineers.org/ · facebook.com/yeprishtina · instagram.com/yeprishtina

**Factual guardrails**
- Never invent enrollment figures, testimonials, accreditations, results, prices, or partners.
- A historical proposal is not an active partnership or active program.
- Do not imply LEGO® sponsors or endorses YEP. Do not call certificates "accredited" unless an admin supplies verified wording.
- All demo data is synthetic, flagged `is_demo = true`, and visibly labelled in the UI. No real child data in seeds, fixtures or logs.

---

## 2. Fixed technology stack — **TypeScript front end, Python back end** (do not substitute)

### Back end (Python)
| Concern | Choice |
| --- | --- |
| Language | **Python 3.12**, fully type-hinted, `mypy --strict` on app code |
| Package manager | **uv** (`pyproject.toml`, `uv.lock`) |
| Web framework | **FastAPI** REST API under `/api/v1`; OpenAPI generated automatically |
| Validation / schemas | **Pydantic v2** — the single source of truth for request/response shapes |
| Database | **PostgreSQL 16** |
| ORM / migrations | **SQLAlchemy 2.0** (typed `Mapped[...]` models, sync sessions via `psycopg` 3) + **Alembic** migrations (one revision per module step) |
| Background jobs | **Celery 5** worker + **Celery Beat** scheduler, **Redis** as broker only (business data never lives in Redis) |
| Auth | Own implementation: `argon2-cffi` password hashing, httpOnly secure session cookie stored in DB, CSRF token for cookie auth, TOTP MFA (`pyotp`) for privileged roles, hashed expiring verification/reset tokens |
| Files | S3-compatible storage via `boto3` (MinIO in dev), private buckets, presigned expiring URLs |
| Email | SMTP via `aiosmtplib`/`smtplib` from env; dev "outbox only" adapter when SMTP unset |
| PDF | **WeasyPrint** (HTML/Jinja2 templates → PDF; correct Albanian characters) |
| Spreadsheets | `openpyxl` / `pandas` for import and export |
| Money | `decimal.Decimal` + `Numeric(12,2)` columns. Never `float` for money |
| Tests | **pytest** + `httpx` TestClient against a real Postgres test database; `factory_boy` for synthetic data |
| Lint/format | **ruff** (lint + format), mypy |
| ML / AI (M17–M18) | **pandas, scikit-learn, statsmodels, joblib**; LLM access through a provider adapter (default: Anthropic Claude API, configurable) |

### Front end (TypeScript)
| Concern | Choice |
| --- | --- |
| Language | **TypeScript** (strict), Node.js 22 LTS, pnpm |
| Framework | **Next.js 15** (App Router, React 19) — UI only; all business rules live in the Python API |
| API client | **Generated from the FastAPI OpenAPI schema** with `openapi-typescript` + `openapi-fetch` (`pnpm gen:api`); never hand-write API types |
| UI | Tailwind CSS + shadcn/ui, lucide icons, React Hook Form (+ Zod only for client-side form UX, mirroring Pydantic rules), TanStack Query |
| Charts | Recharts for dashboards |
| i18n | `next-intl`, locales `sq` (default) and `en`; messages in `apps/web/messages/{sq,en}/<module>.json` |
| Tests | Vitest (components/utilities), **Playwright** (critical end-to-end journeys) |

### Dev infra
Docker Compose: postgres, redis, minio, mailpit (SMTP capture). Same images used in production (M15).

### Repository layout
```
yep-portal/
  apps/api/                       Python back end (uv project)
    app/main.py                   FastAPI app, router registration
    app/core/                     config, db session, security, permissions, scope, audit, outbox, files, idempotency, i18n of errors
    app/modules/<module>/         models.py · schemas.py (Pydantic) · service.py · router.py · permissions.py · audit.py · state_machines.py · tasks.py
    app/jobs/registry.py          Celery Beat schedule (all scheduled jobs in one place)
    app/ml/  app/ai/              added in M17 / M18
    app/templates/                Jinja2 templates for emails and PDFs
    alembic/versions/             migrations
    tests/<module>/
  apps/web/                       Next.js TypeScript front end
    app/[locale]/(public|portal)/…  components/  lib/api/ (generated client)  messages/
  docker-compose.yml  .env.example  PROGRESS.md  docs/
```

---

## 3. Cross-cutting conventions (built in M00, reused everywhere)

**IDs & time** — UUID primary keys. All timestamps `timestamptz`, stored UTC (`datetime` with tzinfo). Display timezone
configurable, default `Europe/Belgrade` (Kosovo's IANA zone), using `zoneinfo`. Calendar dates (birth date, session date) use `date`.
Never hardcode UTC offsets.

**Money** — `Numeric(12,2)` + `currency CHAR(3)` default `EUR`; `Decimal` with `ROUND_HALF_UP` to 2 dp at line level.
Never sum different currencies. API returns money as strings to avoid float errors in the browser.

**Roles** (one person may hold several; privileged roles are invitation-only):
`owner_admin`, `operations_coordinator`, `instructor`, `finance_officer`, `marketing_coordinator` (added in M19), `guardian`, `student` (optional,
guardian-enabled), `school_coordinator`, `sponsor` (optional, read-only). Public signup can only create `guardian`.

**Scopes** — role assignments carry scope: organization, location, school/partner, program, cohort, initiative,
household. Authorization = action permission **and** record scope, checked on the server for every endpoint,
nested resource, file, export and search. Hiding UI is not authorization.
- FastAPI dependency: `Depends(require_permission("<module>.<entity>.<action>"))`
- Scope: list queries go through `ScopeService.filter(user, select_stmt, Entity)`; single records via `ScopeService.assert_can(user, record)`.
- Actions vocabulary: `view, create, edit, submit, approve, cancel, export, admin`.
- Each module defines its rows in `permissions.py` and appends them to `docs/permission-matrix.md`.

**State machines** — status fields change only through named transitions defined in the module's
`state_machines.py` (`from`, `action`, `to`, `guard`). No arbitrary status edits. The API exposes permitted next
actions per record (`allowed_actions` field) so the UI never re-implements the rules.

**Audit** — `audit.record(session, event)` inside the same DB transaction as the business change.
Event: id, occurred_at, actor_id, actor_type (user|system|integration), role, scope refs, action, entity_type,
entity_id, subject refs (child/cohort/initiative), outcome (succeeded|failed|denied), reason, changed fields with
redacted before/after, correlation_id (request ID middleware). Denied/failed attempts via `audit.record_failure()`
on a separate connection so rollback can't erase them. Table is append-only for the app DB role (no UPDATE/DELETE grant).
Never log passwords, tokens, card data, private notes, or document contents. Each module lists its audit actions.

**Transactions & concurrency** — one SQLAlchemy session/transaction per request (`with session.begin():`).
Capacity and "last seat" use `SELECT … FOR UPDATE` (`with_for_update()`) or serializable retries. Unique constraints for duplicates.

**Idempotency** — state-changing POSTs that create money, enrollments or messages accept an `Idempotency-Key`
header stored in `idempotency_key` (key, user, route, response hash, expiry).

**Outbox & jobs** — notifications: `outbox.enqueue(session, template_key, recipient, locale, payload, dedupe_key)`
inside the transaction; a Celery task sends with retry limits. Every scheduled job is declared in `app/jobs/registry.py`,
runs as `actor_type = system`, and writes a `job_run` row (visible to admins). Tasks must be idempotent.

**Historical data** — records imported for the period from 1 June 2022 to go-live carry `is_historical = true` and their import job reference;
they trigger no notifications, invoices or consents, and are read-only once their period is locked (M13). Every report and dashboard
supports periods back to June 2022 and labels historical summary figures.

**Restricted care data** — allergies, medication notes, incidents and authorised pick-up persons (M21) are visible only to staff on duty
for that child and to owner/operations, never sent to AI or marketing, and purged after their retention period.

**Corrections** — posted financial, stock and attendance records are never edited or deleted; corrections are
linked reversing/adjusting records with actor, time and reason.

**Shared finance ledger (defined in M06, reused by M07, M09, M11, M14)** — one set of tables, no per-module
ledgers: `financial_document` (type: customer_invoice | supplier_bill | credit_note | refund | pay_statement),
`document_line` (with allocation dimensions: location, program, partner, initiative, cohort), `payment`
(direction in|out, method, date, account), `payment_allocation`, `cash_account`, `account_transfer`.

**API style** — REST, plural nouns, `GET /api/v1/<resource>?page&page_size&sort&filter`, errors as
`{ "code", "message", "details" }` where `code` is a stable key the web app translates. Every router has
OpenAPI tags and response models so the TypeScript client is generated correctly.

**UI** — mobile-first for guardians and instructors; desktop-first registers for staff. Accessible forms,
keyboard navigation, readable contrast, clear empty/loading/error states, correct Albanian characters.
Provisional brand theme (blue `#1B6FB5`, green `#3AA335`) until official assets are supplied; never invent logos.
Language switch visible; user's language remembered. Translate validation, statuses, emails and PDFs too.

**Reports** — every metric shows as-of date, period, timezone, population and definition. Unique children are
deduplicated across programs. Financial figures state their date basis (document date, due date, or payment date).

**ML & AI (M17–M19)** — advisory only: predictions, campaign suggestions and AI drafts support staff, they never take decisions about
children, admissions, prices or money on their own, and nothing is published or spent without approval. Every AI output a person will send is reviewed first.

---

## 4. Working rules for the assistant (token economy)

1. Read `PROGRESS.md` first. Do not re-implement anything marked done.
2. Work on **one sub-step** of the current module per reply; then stop.
3. Inspect only the files you need; do not list or read the whole repo.
4. Output only new or changed files (full content for new files, focused diffs for edits). Never reprint unchanged files.
5. Do not paste all models; only the current module's `models.py` and its Alembic revision.
6. After API changes, regenerate the TypeScript client (`pnpm gen:api`) instead of writing types by hand.
7. Keep explanations short. No restating of these instructions.
8. After each sub-step: migration created, tests added, commands to run, `PROGRESS.md` updated
   (done / tested / incomplete / decisions / blockers).
9. Ask a question only if the answer changes architecture or blocks a core workflow; otherwise choose a
   configurable default and record it under "Decisions" in `PROGRESS.md`.
10. Never claim a test, integration, backup or feature works without evidence (test output or command result).
11. Integrations without credentials use clearly labelled dev adapters; never report them as live.

---

## 5. Definition of done (per module)

- SQLAlchemy models + Alembic migration, constraints and indexes.
- FastAPI routers with Pydantic schemas, permission + scope enforcement and audit events.
- Regenerated TypeScript client; web screens in `sq` and `en`, with empty/loading/error states.
- pytest integration tests for the module's workflows **and** its authorization boundaries; Playwright test for its main journey.
- Permission rows appended to `docs/permission-matrix.md`; audit actions appended to `docs/audit-actions.md`.
- `PROGRESS.md` updated.
