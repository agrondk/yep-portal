# M14 — Loans & cash account reconciliation (DEFERRED phase — build only when needed)

**Depends on:** M06, M09, M12. **Attach with:** `01_MASTER_CONTEXT.md`, `PROGRESS.md`.

## Goal
Track organizational borrowing and reconcile bank/cash accounts, using the shared ledger, so debt repayment is
separated from operating costs and account balances can be shown as real balances.

## Scope
**In:** lenders (as `party`), loan accounts, disbursements, versioned repayment schedules (manual or imported),
installments, repayments split into principal/interest/fees, early repayment, schedule revisions, reconciliation to
lender statements, reminders, balances and forecasts; bank statement import and reconciliation for `cash_account`.
**Out:** automatic interest calculation when terms are incomplete.

## Data model (`apps/api/app/modules/loans/models.py`)
- `loan` (lender_party_id, reference, principal, currency, disbursement_date, interest_terms text, rate nullable, fees_terms, frequency, maturity_date, status, agreement_file_id)
- `loan_schedule_version` (loan_id, version, source: manual | imported | revised, effective_from, created_by) + `loan_installment` (version_id, due_date, principal_due, interest_due, fees_due)
- `loan_transaction` (loan_id, type: disbursement | principal_repayment | interest | fee | adjustment | reversal, amount, date, payment_id, reverses_id)
- `bank_statement_line` (cash_account_id, date, amount, description, reference, matched_payment_id nullable, status)

## Rules
- Outstanding principal = disbursements − principal repayments ± adjustments from posted `loan_transaction`s; never an editable field or the sum of future installments.
- Forecast schedule (versions) and actual paid amounts stay distinct; revisions keep prior versions.
- Interest and fees post to finance reports via shared references — never re-entered as unrelated expenses.
- If terms are incomplete, show schedule as entered and do not compute interest.
- Account balance displayed as "balance" only when opening balance is reconciled; otherwise "recorded net cash movement".
- Internal transfers never count as income or expense.
- UI clearly distinguishes "financial loans" from "equipment checkout" (M08).

## Sub-steps
- **A.** Loans, schedules, transactions, outstanding principal + tests.
- **B.** Reminders, reconciliation to lender statements, forecasts.
- **C.** Bank statement import + matching to payments, reconciled balances.

## Acceptance tests
- Disbursement + one installment updates principal, interest, fees, cash movement and future due amounts; reversal retains history.
- Unreconciled account is labelled as net movement, not balance.
