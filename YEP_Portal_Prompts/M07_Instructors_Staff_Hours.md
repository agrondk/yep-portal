# M07 — Instructors & staff: profiles, availability, sessions taught, monthly pay statements

**Depends on:** M03, M04, M06. **Attach with:** `01_MASTER_CONTEXT.md`, `PROGRESS.md`.

## Goal
Know who can teach what and when, count sessions actually taught per instructor, and produce a monthly
pay statement that flows into the shared ledger as a cost — without hardcoding any compensation figures.

## Scope
**In:** staff profiles, qualifications per program, availability, sessions taught (from M04 delivery records),
substitutions, configurable pay rates, monthly statements with approval, other timesheet entries (training, events, prep).
**Out:** full payroll/tax/social contributions (export only), HR contracts beyond file upload.

## Data model (`apps/api/app/modules/staff/models.py`)
- `staff_profile` (user_id, employment_type: employee | contractor | volunteer, start_date, end_date, phone, iban_enc, contract_file_id)
- `staff_program_qualification` (staff_id, program_id, level: trainee | qualified | trainer, certified_at)
- `availability` (staff_id, weekday, start_time, end_time, valid_from, valid_to) + `unavailability` (staff_id, from, to, reason)
- `pay_rate` (staff_id nullable, program_id nullable, basis: per_session | per_hour | monthly_fixed, amount, currency, valid_from, valid_to) — most specific rate wins
- `timesheet_entry` (staff_id, date, type: session | substitution | training | event | prep | other, session_id nullable, minutes, note, status: draft | submitted | approved | rejected)
- `pay_statement` (staff_id, period_month, status: draft | submitted | approved | paid, total, financial_document_id) — posts a `pay_statement` document in M06 ledger

## Rules
- Onboarding, internal trainings and program certification are handled in M20, which grants and renews `staff_program_qualification`.
- Session entries are generated from `session_delivery` (delivered_by) — instructors don't retype them; substitutions credit the actual instructor.
- Scheduling (M03) warns when assigning an instructor who is unavailable or not qualified for the program.
- Approval: operations_coordinator or owner_admin approves; nobody approves their own statement when separation of duties is on.
- Approved statement creates a `financial_document` (type pay_statement, party = staff) — one per staff per month (unique). Payment recorded in M06 marks it paid.
- Instructors see only their own entries and statements. Finance sees amounts; coordinators see hours but amounts only if permitted.

## API
`/staff` CRUD, `/staff/:id/qualifications|availability|rates`, `/timesheets` (list, submit, approve), `POST /pay-statements/generate?month=` (preview + commit),
`/pay-statements/:id/approve`, `/my/timesheet`, `/my/pay-statements`, export CSV for accountant.

## Screens
Staff register, staff detail (qualifications, availability calendar, rates), monthly hours overview (instructor × sessions),
pay statement review/approve, instructor "my hours" (mobile).

## Audit actions
`staff.created|edited|ended`, `qualification.changed`, `availability.changed`, `rate.changed`, `timesheet.submitted|approved|rejected`, `pay_statement.generated|approved|paid`, `export.payroll`.

## Sub-steps
- **A.** Schema + migration; profiles, qualifications, availability, rates + M03 warnings + tests.
- **B.** Timesheet generation from deliveries, substitutions, approvals + tests.
- **C.** Pay statements → ledger document, screens, export.

## Acceptance tests
- Statement for an instructor with 20 delivered sessions uses the correct rate per program and period; regenerate does not duplicate.
- Instructor cannot view another instructor's statement or rates.
- Self-approval blocked when separation of duties is enabled.
