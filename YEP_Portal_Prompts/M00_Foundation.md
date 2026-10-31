# M00 — Foundation: repo, database, auth, roles & scopes, audit, files, jobs, i18n shell

**Depends on:** nothing. **Attach with:** `01_MASTER_CONTEXT.md`, `PROGRESS.md`.

## Goal
A running monorepo with a real PostgreSQL database and every cross-cutting service the other modules reuse.
No business modules yet. After M00, any module can add permissions, audit events, files and notifications
by calling shared services.

## Scope
**In:** scaffold, Docker Compose, SQLAlchemy + Alembic setup, auth, invitations, roles/scopes, permission + scope guards,
audit service, idempotency, file storage, outbox + Celery worker/beat + job registry, i18n app shell, test harness,
CI scripts, demo-seed command skeleton, staff/user admin screens.
**Out:** any program, family, finance or inventory feature.

## Data model (`apps/api/app/modules/core/models.py`)
- `organization` (single row; name, timezone, default_locale, reporting_year_start_month)
- `location` (name, address, type: center | school | other, active)
- `user` (email unique citext, password_hash nullable, locale, status: invited | active | disabled, mfa_secret_enc, mfa_enabled, last_login_at)
- `session` (token_hash, user_id, expires_at, ip, user_agent, revoked_at)
- `role_assignment` (user_id, role, scope_type: organization | location | partner | program | cohort | initiative | household, scope_id nullable, valid_from, valid_to, granted_by, revoked_at)
- `invitation` (email, role, scope_type, scope_id, token_hash, expires_at, accepted_at, revoked_at, invited_by)
- `verification_token` (user_id, purpose: email_verify | password_reset, token_hash, expires_at, used_at)
- `audit_event` (fields per master §3) — indexes on (occurred_at), (entity_type, entity_id), (actor_id), (outcome)
- `idempotency_key` (key, user_id, route, response_hash, created_at, expires_at; unique key+user+route)
- `file_object` (bucket, object_key, original_name, mime, size, sha256, owner_entity_type, owner_entity_id, uploaded_by, scope refs, created_at, deleted_at)
- `outbox_message` (channel: email | in_app, template_key, locale, recipient_user_id/email, payload jsonb, dedupe_key unique, status: queued | sent | failed | dev_captured, attempts, last_error, sent_at)
- `job_run` (job_name, started_at, finished_at, outcome, detail)
- `setting` (key, value jsonb, updated_by) for organization-level configuration

DB roles: migration role owns schema; app role has no UPDATE/DELETE on `audit_event`.

## Rules
- Public registration creates only a `guardian` user (email verification required before private data access).
- Staff, school, sponsor and student access only via invitation; invitations expire (default 7 days) and single-use.
- Removing/expiring a role assignment takes effect on the next request (no cached permissions beyond the request).
- MFA mandatory for `owner_admin` and `finance_officer` in production (config flag), optional for others.
- Rate-limit login, registration, password reset.
- First administrator created by CLI command `uv run python -m app.cli admin-create` (no fixed demo passwords).

## API (examples)
`POST /auth/register` · `POST /auth/login` · `POST /auth/logout` · `POST /auth/verify-email` ·
`POST /auth/password/forgot|reset` · `POST /auth/mfa/setup|verify` · `GET /me` ·
`GET|POST /admin/users` · `POST /admin/invitations` · `POST /invitations/:token/accept` ·
`POST|DELETE /admin/role-assignments` · `GET /admin/audit-events` (owner_admin only, filtered, paginated) ·
`POST /files` (multipart, type/size validated) · `GET /files/:id/url` (scope-checked presigned URL) ·
`GET /admin/jobs` (job runs)

## Screens
Public: sign in, register (guardian), verify email, forgot/reset password, accept invitation.
Portal shell: role-aware navigation, language switch (sq/en), profile & MFA setup.
Admin: users list, invite user with role + scope, revoke access, basic audit log viewer, job runs, organization settings, locations.

## Audit actions
`auth.login.succeeded|failed`, `auth.logout`, `user.registered`, `user.invited`, `invitation.accepted|expired|revoked`,
`role.granted|revoked`, `mfa.enabled|disabled`, `password.reset`, `file.uploaded|downloaded|deleted`, `setting.changed`, `job.run`.

## Sub-steps
- **A.** Monorepo scaffold (uv + pnpm), Docker Compose (postgres, redis, minio, mailpit), FastAPI app, SQLAlchemy base + Alembic, `core/models.py`, first migration, `.env.example`, lint/test scripts, health endpoint.
- **B.** Auth (register, verify, login, logout, reset, sessions, rate limits, MFA) + tests.
- **C.** Roles, scopes, invitations, `require_permission()` dependency, `ScopeService`, permission-matrix doc generator + boundary tests.
- **D.** Audit service (+ failure path), idempotency middleware, file service, outbox + Celery worker/beat + job registry + tests.
- **E.** OpenAPI → TypeScript client generation; Next.js shell: locales, layout, auth screens, role-aware navigation, admin users/invitations/locations/audit/jobs screens, Playwright smoke test.

## Acceptance tests
- Public registration cannot obtain any role except guardian (API and UI).
- Expired or used invitations cannot be redeemed; revoked access fails on the next request.
- A denied request writes a `denied` audit event that survives transaction rollback.
- App DB role cannot UPDATE or DELETE `audit_event` (test executes and expects error).
- File URL requests outside scope are denied; uploads with disallowed type/size rejected.
- Outbox message with same dedupe key is enqueued once; worker retries then marks failed.
- Data persists across API and database container restarts.
