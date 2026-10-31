# M11 — Franchise reporting (e2 Young Engineers)

**Depends on:** M04, M06, M09. **Attach with:** `01_MASTER_CONTEXT.md`, `PROGRESS.md`.

## Goal
Produce the periodic figures YEP owes its franchisor and record franchise fees as supplier bills —
using configurable rules, because the actual franchise terms must be entered by the owner, not assumed.

## Scope
**In:** franchise agreement terms (configurable), reporting periods, fee calculation preview, report snapshot (students,
groups, sessions, revenue basis), export (CSV/PDF/XLSX), fee bill creation in M09/M06, curriculum/licence material register (optional list).
**Out:** any direct integration with e2 systems (export files only).

## Data model (`apps/api/app/modules/franchise/models.py`)
- `franchise_agreement` (franchisor_party_id, start_date, end_date, currency, notes, file_id)
- `franchise_fee_rule` (agreement_id, type: fixed_periodic | percent_of_revenue | per_student | per_group | per_kit | other, rate_or_amount, basis_definition text, period: monthly | quarterly | yearly, valid_from, valid_to)
- `franchise_report` (agreement_id, period_start, period_end, status: draft | final | submitted, snapshot jsonb, generated_by, submitted_at, file_id)
- `franchise_fee_calculation` (report_id, rule_id, basis_value, amount, financial_document_id nullable)

## Rules
- No default fee values are seeded; the module refuses to calculate until the owner enters rules (show "terms not configured").
- Snapshot metrics with explicit definitions: unique active children in period (deduplicated), enrollments, active groups/cohorts, delivered sessions, revenue basis (invoiced or paid — chosen per rule and labelled), by program and by partner type (center / school / kindergarten / sponsor).
- Finalising a report freezes the snapshot; regenerating creates a new version.
- Creating the fee bill produces a draft supplier bill (category "Franchise fees") linked to the calculation — submitted through M09 approval.

## API
`/franchise/agreements|rules`, `POST /franchise/reports/generate?from&to` (preview), `POST /franchise/reports/:id/finalize|submit`, `GET /franchise/reports/:id/export?format=`, `POST /franchise/reports/:id/create-fee-bill`.

## Screens
Agreement & rules setup, report generator with metric definitions, history of submitted reports, fee calculation detail.

## Audit actions
`franchise.rule_changed`, `franchise.report_generated|finalized|submitted|exported`, `franchise.fee_bill_created`.

## Sub-steps
- **A.** Schema, rules, snapshot metrics with dedupe + tests.
- **B.** Fee calculation, export, fee bill link, screens.

## Acceptance tests
- A child enrolled in two programs counts once in "unique children" and twice in "enrollments".
- Without configured rules, no fee is calculated and the UI says so.
