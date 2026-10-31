# M06 — Shared financial ledger, invoicing (family + institutional), payments, credits, refunds

**Depends on:** M02, M05. **Attach with:** `01_MASTER_CONTEXT.md`, `PROGRESS.md`.

## Goal
Build the **one** financial ledger the whole portal uses (master §3), then family and institutional billing on top:
per-child fees, installments, free and sponsored places, and monthly institutional invoices from school-confirmed sessions.

## Scope
**In:** ledger tables, cash/bank accounts (basic), invoice numbering, VAT (TVSH) configuration, family invoices and
installments, institutional monthly invoices, discounts/scholarships/promos, sponsorship allocation, manual payments
(cash, bank transfer), allocations, credits, refunds, reversals, receivables and overdue, PDF invoices/receipts,
payment-provider adapter interface (test adapter only), enrollment payment-requirement hook for M02.
**Out:** supplier bills (M09), staff pay (M07), loans (M14), finance dashboard (M12).

## Data model (`apps/api/app/modules/finance/models.py`)
- `cash_account` (name, type: cash | bank, iban nullable, currency, opening_balance, opening_date, active)
- `party` (type: household | partner | supplier | staff | lender | franchisor, ref_id, display_name, billing_email, tax_no) — one counterparty table for all modules
- `financial_document` (type: customer_invoice | supplier_bill | credit_note | refund | pay_statement, number unique per type+year, party_id,
  issue_date, due_date, currency, status: draft | issued | partially_paid | paid | overdue | void, voided_by_document_id, source_type, source_id, notes)
- `document_line` (document_id, description, quantity, unit_price, discount_amount, tax_rate, tax_amount, line_total, account_category,
  dims: location_id, program_id, partner_id, initiative_id, cohort_id, enrollment_id, session_ids[]; price_snapshot jsonb)
- `installment` (document_id, due_date, amount, sequence)
- `payment` (direction: in | out, party_id, cash_account_id, method: cash | bank_transfer | card_provider | other, amount, currency, paid_at, reference, provider_event_id unique nullable, recorded_by, reversed_by_payment_id)
- `payment_allocation` (payment_id, document_id, installment_id nullable, amount) — sum per payment ≤ payment amount; remainder = unallocated credit
- `account_transfer` (from_account_id, to_account_id, amount, date, reference)
- `fee_schedule` (offering_id, fee_model, amount, installments_plan jsonb, valid_from) — catalog price; invoices snapshot it
- `discount_rule` (code, type: percent | fixed | promo_price, value, applies_to, valid_from, valid_to, max_uses, requires_approval)
- `funding_commitment` (initiative/partner, amount, period) and `funding_receipt` (payment link) — used by sponsored seats
- `tax_setting` (name, rate, active, confirmed_by_finance bool) — TVSH rates configurable; disabled until finance confirms
- `numbering_sequence` (doc_type, year, prefix, next_value) — gap-free with row lock

## Rules
- Documents in `draft` are editable; once `issued` they are immutable — corrections via credit note / void with reversal.
- Status `partially_paid | paid | overdue` is derived from allocations and due dates (job updates overdue daily), never set by hand.
- Family invoice from enrollment: snapshot price, discounts and installments; free/sponsored enrollments create no customer debt (sponsored creates a line against the sponsor party or initiative allocation).
- **Institutional monthly invoice job/command:** for each active agreement, collect `session_confirmation.status = confirmed` sessions in the month not yet billed; price per agreement (promo price while `promo_valid_until` not passed, else regular); one line per program/grade with session count; link `session_ids`. Re-running never double-bills (unique billed session).
- One payment may settle several invoices; one invoice may receive several payments; over-payment stays as unallocated credit.
- Refunds are documents + outgoing payments linked to the original; require `finance_officer` approval.
- Online payment provider: Python `Protocol` `PaymentProvider` with `TestPaymentProvider` (clearly labelled); verify signatures and dedupe `provider_event_id` when a real provider is added. Never simulate real successful payments.
- No fiscal-certification or tax-compliance claims; tax treatment must be confirmed by finance.
- Expose `billing_hooks.is_payment_requirement_satisfied(session, enrollment_id)` for M02 pending reasons.

## API
`/finance/accounts`, `/finance/parties`, `/finance/documents` (create draft, issue, void, credit note, PDF), `/finance/payments` (record, allocate, reverse; Idempotency-Key required),
`/finance/receivables` (aging), `/finance/discounts`, `/finance/tax-settings`, `POST /finance/institutional-invoices/run?month=` (preview + commit),
guardian: `/me/invoices`, `/me/payments`; school coordinator: `/school/me/invoices`.

## Screens
Finance: documents register (filters by type/status/party/period), invoice editor, payment recording with allocation helper, receivables aging,
institutional invoicing run (preview per partner: sessions, price, totals → commit), discounts, tax settings, accounts.
Guardian: invoices, balances, payment history, PDF download. School: institutional invoices.

## Audit actions
`document.created|issued|voided|credited`, `payment.recorded|allocated|reversed`, `refund.requested|approved|paid`,
`discount.applied|approved`, `institutional_billing.previewed|committed`, `tax_setting.changed`, `numbering.reserved`.

## Sub-steps
- **A.** Schema + migration; parties, accounts, numbering, documents/lines/installments with immutability + tests.
- **B.** Payments, allocations, credits, reversals, refunds, idempotency + tests.
- **C.** Family billing from enrollments (fee schedules, discounts, sponsored/free) + M02 hook.
- **D.** Institutional monthly invoicing from confirmed sessions (promo vs regular) + tests.
- **E.** PDFs (sq/en), finance screens, guardian and school views.

## Acceptance tests
- Partial payments on one invoice and one payment across two invoices reconcile; retry with same Idempotency-Key creates nothing new.
- Issued invoice cannot be edited; credit note reverses it with history kept.
- Institutional run for a month with 52 confirmed sessions at promo 40 € → 2,080 €; second run adds nothing; session 1 day after promo end billed at regular price.
- Free and sponsored enrollments produce no guardian debt.
