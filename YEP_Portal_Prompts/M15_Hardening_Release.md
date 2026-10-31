# M15 — Hardening, backups, security review, end-to-end acceptance, release

**Run:** before every production release (at least after Release 1). **Attach with:** `01_MASTER_CONTEXT.md`, `PROGRESS.md`.

## Goal
Prove — with evidence — that the portal is safe to run with real families' data: backups restore, permissions hold,
jobs run, and the critical journeys pass in both languages.

## Scope
**Deployment:** production Docker Compose (api [FastAPI + uvicorn/gunicorn], worker + beat [Celery], redis, web [Next.js], postgres, minio or managed S3, reverse proxy with HTTPS — Caddy),
environment separation (dev/test/prod), secrets in env files outside git, connection-pool limits documented, health checks, log rotation.
**Backups:** nightly `pg_dump` + object storage sync to off-site storage, retention policy, `backup_run` status persisted and shown to admins,
**restore test into an isolated environment** with a consistency check script. Do not claim scheduled backups until the job is configured and has run.
**Security:** dependency audit, OWASP checklist (auth, session fixation, CSRF on cookie auth, XSS, IDOR via scope tests, file upload),
security headers, rate limits, MFA enforced for privileged roles, no superuser app DB role, audit table grants verified,
data-retention and data-subject export/deletion requests workflow (Kosovo personal data protection law — confirm current law number and
obligations with a legal advisor), privacy notice and consent texts reviewed.
**Monitoring:** uptime check, failed-job alerts, DB connectivity alert, error tracking (self-hosted or SaaS — configurable).

## Critical acceptance scenarios (run all that apply to built modules; record evidence in `docs/acceptance-results.md`)
1. Guardian registers, adds two children without emails, applies, receives an offer, accepts, completes requirements, sees enrollment.
2. Another household cannot access those children via pages, APIs, files, exports, searches or activity history.
3. Instructors see only assigned learners; school and sponsor users only their scope; revoked access stops immediately.
4. Users cannot self-assign staff roles; expired invites cannot be redeemed.
5. Two concurrent applicants cannot both get the last seat; repeated acceptance → one enrollment; expiry releases capacity.
6. Free and sponsored enrollments complete without artificial debts.
7. Instructor records attendance and progress; guardian sees only published feedback.
8. Partial payments and one payment across invoices reconcile; retries create no duplicates.
9. School proposal → agreement → cohorts → sessions confirmed by school → monthly institutional invoice at promo then regular price.
10. Equipment purchase received, assigned, transferred, partially returned, adjusted; stock and kit counts reconcile.
11. Recurring electricity bill generated once, approved, partially paid, settled; totals reconcile.
12. Instructor pay statement generated from delivered sessions once, approved, paid.
13. Posted corrections (invoice, refund, expense, stock, attendance) use linked reversing records.
14. Partner/program reports deduplicate children; MTD/YTD use displayed basis.
15. Every successful change has an audit event; denied/failed attempts survive rollback.
16. Data survives restarts; scheduled jobs and notification retries actually run.
17. Isolated backup restore succeeds with consistent records.
18. With AI disabled, all workflows work; with AI enabled, no child personal data leaves the system (M18), and ML outputs are visible only to permitted staff (M17).
19. Marketing: nothing is published, spent or discounted without approval; withdrawn photo consent blocks posts; campaign spend reconciles with expenses (M19).
20. Historical data since June 2022 is imported, reconciled against control totals per year and locked; reports compare years without double counting (M13).
21. New instructor completes the welcome package before leading a cohort (M20); camp check-out only to authorised persons and care data stays restricted (M21).
22. Albanian and English UI, errors, notifications, PDFs and mobile layouts work, including keyboard access.

## Sub-steps
- **A.** Production compose, HTTPS, env/secrets, health checks, monitoring.
- **B.** Backup jobs, status, restore test with evidence.
- **C.** Security review fixes and tests.
- **D.** Run acceptance scenarios, fix failures, write `docs/acceptance-results.md` and release notes; update requirement checklist (implemented / tested / incomplete).

## Deliverables
Installation and start commands, `.env.example`, secure first-admin provisioning, worker/scheduler setup, storage setup,
backup/restore procedure with actual results, requirement checklist, list of remaining external configuration or blockers.
