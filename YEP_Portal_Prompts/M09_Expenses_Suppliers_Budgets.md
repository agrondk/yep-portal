# M09 — Expenses, suppliers, approvals, recurring bills, budgets

**Depends on:** M06. **Attach with:** `01_MASTER_CONTEXT.md`, `PROGRESS.md`.

## Goal
Record every operating cost (rent, electricity, internet, materials, franchise fees…) as supplier bills in the shared
ledger, with approvals, partial payments, recurring templates and budget vs actual — without double counting purchases
that also appear in inventory.

## Scope
**In:** suppliers (as `party`), expense categories, supplier bills with lines and allocations, attachments, approval
workflow with thresholds and delegation, recurring bill templates, partial payments (M06 payments, direction out),
supplier refunds/corrections, budgets by category/location/program, monthly/annual summaries, payment reminders.
**Out:** loans (M14), staff pay (M07 produces its own documents), franchise fee calculation (M11).

## Data model (`apps/api/app/modules/expenses/models.py` — reuses M06 tables)
- `expense_category` (name_sq/en, parent_id, kind: operating | capital | financing, active) — seed: Rent, Electricity, Water, Heating, Internet & telephone,
  Office materials & stationery, Cleaning, Instructor & staff costs, Transport & fuel, Equipment purchases, Maintenance & repairs, Software subscriptions,
  Franchise fees, Marketing, Insurance, Bank charges, Other
- Supplier bills = `financial_document(type = supplier_bill)` + `document_line` (category, dims, tax), attachment via `file_object`
- `approval_policy` (min_amount, max_amount, approver_role, allow_self_approval bool, delegate_user_id nullable)
- `approval_record` (document_id, step, approver_id, decision: approved | rejected, reason, decided_at)
- `expense_workflow` on the document: draft → submitted → approved | rejected; cancelled (before approval)
- `recurring_bill_template` (supplier_party_id, category_id, amount nullable (variable), frequency: monthly | quarterly | yearly, day_of_month, next_run_date, active)
- `recurring_bill_run` (template_id, period, document_id) unique (template_id, period)
- `budget` (year, category_id, location_id nullable, program_id nullable, month nullable, amount)

## Rules
- Approval status (draft/submitted/approved/rejected/cancelled) and payment status (unpaid/partially_paid/paid/overdue) are separate fields; payment status derived from allocations (M06).
- Approval route chosen by amount threshold; self-approval blocked unless the policy allows it.
- Recurring job creates at most one bill per template per period (unique run); variable-amount bills are created as drafts awaiting the actual amount.
- Split a bill across categories/programs/locations via lines; never duplicate the original amount.
- Lines with `kind = capital` link to inventory receipts/assets (M08) — reported as asset acquisition, not operating expense.
- Supplier refunds and corrections are linked adjusting documents.
- Marketing bills can link to an M19 campaign (`campaign_id` dimension) so campaign spend and ROI reconcile with the ledger.
- Reports state the date basis: incurred (issue date) vs paid (payment date) — never mixed under one label.
- Staff with `expense.submit` can submit their own claims (instructors when enabled); they cannot see others' claims.

## API
`/suppliers` (parties), `/expense-categories`, `/bills` (draft, submit, approve, reject, cancel, attach), `/approval-policies`,
`/recurring-bills` (templates, run history, `POST /recurring-bills/run?period=`), `/budgets`, `GET /expenses/summary?period&basis=incurred|paid&groupBy=`,
`GET /suppliers/:id/balance`, `/my/expense-claims`.

## Screens
Bills register (approval status + payment status columns), bill editor with lines and attachment, approvals inbox,
recurring templates with next run, supplier list with balances, budgets grid (category × month) with actual vs budget, monthly/annual summary, my claims.

## Audit actions
`bill.created|submitted|approved|rejected|cancelled`, `bill.paid` (via M06), `recurring.generated`, `budget.changed`, `approval_policy.changed`, `supplier.created|edited`.

## Sub-steps
- **A.** Categories seed, supplier bills on ledger, lines/allocations, attachments + tests.
- **B.** Approval policies & workflow, self-approval rules, claims + tests.
- **C.** Recurring templates & idempotent job, budgets, summaries (incurred vs paid), screens.

## Acceptance tests
- Recurring electricity bill generated once for the month (job retried twice), approved, paid in two parts, settled; expense and cash totals reconcile without duplication.
- Equipment bought (capital line) + received in M08 + paid in M06 counts once as asset acquisition and once as cash out — never as operating expense.
