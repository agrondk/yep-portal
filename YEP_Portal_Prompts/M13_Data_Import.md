# M13 — Historical data migration & file imports (from June 2022)

**Depends on:** the target modules (run the matching sub-step after each target exists). **Attach with:** `01_MASTER_CONTEXT.md`, `PROGRESS.md`,
and a **sample of max 20 rows** (anonymised) of the source file being mapped.

## Goal
Bring YEP's full history into the portal — **from 1 June 2022 to go-live** — so dashboards, year-on-year comparisons, ML forecasts
(M17) and marketing triggers (M19) work from day one. Covers branches/locations, partners, programs, terms and groups, students and
enrollments per program, camps, staff and trainings, income, expenses, investments (equipment) and loans.
Any staff member with import permission can load lists from common file types, safely: preview, validate, confirm — never silent writes.

## Supported file types
| Type | Handling |
| --- | --- |
| `.xlsx`, `.xlsm`, `.xls`, `.ods` | `openpyxl` / `xlrd` / `odfpy` via pandas; user picks the sheet and header row; merged cells and blank title rows handled |
| `.csv`, `.tsv`, `.txt` (delimited) | delimiter auto-detected (`, ; \t |`) with manual override; encoding auto-detected (`charset-normalizer`) — UTF-8, Windows-1250/1252, ISO-8859-2 — so ë/ç are correct |
| `.txt` fixed-width | user defines column widths in the mapping screen |
| `.json`, `.xml` | flattened to rows by a selectable record path |
| `.pdf` (tables) | best-effort table extraction (`pdfplumber`); every row marked "needs review" — never auto-committed |
| `.zip` | several of the above in one upload; each file becomes its own import job |

Locale-aware parsing: dates `dd.mm.yyyy`, `dd/mm/yyyy`, ISO, Excel serial dates; decimal comma or point (`1.234,56` vs `1,234.56`) set per job;
currency symbols stripped; Albanian month names recognised.

## Historical mode (everything imported before go-live)
- Records carry `is_historical = true`, `source = import`, `import_job_id`, `source_file_sha256`, `source_row_key`.
- **No side effects:** no emails, no notifications, no invoices sent, no seat checks, no state-machine notifications; consents are **not** assumed
  (historical children have `consent_status = unknown` until a guardian confirms).
- Historical financial records are posted as historical documents/payments in the shared ledger (M06), flagged and read-only, so year totals are real.
  Opening balances at go-live are entered as dated opening documents.
- After reconciliation, owner_admin can **lock a historical period** (e.g. "Jun 2022 – Aug 2025"); locked periods reject further imports or edits except reversals.

## Detailed vs summary history
Old data may exist only as totals (e.g. "Bricks Challenge, autumn 2022, 3 groups, 48 children, 4,320 € income").
Support both:
- **Detailed import** — individual children, enrollments, payments, expenses, assets.
- **Summary import** into `historical_summary` (period_start, period_end, location_id, partner_id nullable, program_id, groups_count, children_count,
  sessions_delivered, income_amount, expense_amount, notes, source) when individual records do not exist.
Reports (M12) combine both, show a "historical summary" label, and never double count a period that has both detailed and summary data
(detailed wins; overlap warning at import).

## Data model (`apps/api/app/modules/imports/models.py`)
- `import_job` (profile_key, file_id, file_type, sheet_name, header_row, delimiter, encoding, decimal_separator, date_format, uploaded_by,
  status: uploaded | mapped | previewed | committed | partially_committed | failed | cancelled | rolled_back, mapping jsonb, summary jsonb, committed_at, historical bool)
- `import_row` (job_id, row_no, raw jsonb, normalized jsonb, status: valid | warning | error | duplicate | needs_review | committed | skipped, messages jsonb, target_entity, target_id)
- `import_mapping_template` (profile_key, name, column_map jsonb, transforms jsonb, created_by) — save and reuse a mapping for files that repeat yearly
- `value_mapping` (profile_key, field, source_value, target_value) — e.g. "AlgoPlay", "Algo play", "ALGO PLAY" → Algo Play; "Qendra", "Center" → main branch
- `historical_summary` (see above)
- `historical_period_lock` (from, to, locked_by, locked_at, reason)
- `reconciliation_check` (job_id or period, metric, source_total, imported_total, difference, status: ok | mismatch | accepted, accepted_by, note)

## Import profiles (one sub-step each, as target modules become available)
| # | Profile | Target | Notes |
| --- | --- | --- | --- |
| 1 | `branches_locations` | M00 locations, M01 rooms | centers, schools used as venues, opening/closing dates |
| 2 | `partners` (+ contacts, agreements) | M05 | relationship periods; past proposals as **historical**, never activating a partner |
| 3 | `programs` | M01 | normalised names; stay draft until confirmed for future use |
| 4 | `terms_offerings_groups` | M01/M03 | historical offerings and cohorts per term and branch/partner, with instructor names |
| 5 | `students_guardians` | M02 | children without email; guardians as contacts (no accounts created, no invitations sent in historical mode) |
| 6 | `enrollments` | M02/M03 | per program and term, status completed/cancelled, funding (paid/free/sponsored) |
| 7 | `attendance` (optional) | M04 | per session or as per-child totals |
| 8 | `camps` | M21 | camp editions, weeks, participants, activities held |
| 9 | `staff` | M07 | profiles and employment periods; invitations only for current staff, on request |
| 10 | `trainings` | M20 | trainings held, participants, completion |
| 11 | `income` | M06 | invoices and/or payments per family, school or sponsor; or monthly totals per program/branch as summary |
| 12 | `expenses` | M09 | supplier bills/payments by category (rent, utilities, materials, marketing…), or monthly totals |
| 13 | `investments_assets` | M08 | equipment and kits bought since 2022 with cost and date (capital), current condition |
| 14 | `loans` | M14 | loan agreements and repayment history |
| 15 | `inventory_opening` | M08 | stock on hand at go-live |
| 16 | `historical_summary` | M13 | totals-only periods |

Each profile ships a **downloadable Excel/CSV template** (sq/en headers, example rows marked synthetic, field rules on a second sheet).

## Rules
- Workflow: upload → choose profile → map columns (auto-suggested from headers, saved templates) → value mapping → preview → validate →
  resolve duplicates → confirm → commit → reconciliation report.
- Nothing is written until confirmed. Commit in batches inside transactions with resumable state; a failed batch rolls back only itself.
- **Re-import safety:** the same file (hash) or the same source row key cannot create duplicates; a corrected file updates or skips by key, with a diff preview.
- **Undo:** an uncommitted or just-committed job can be rolled back if nothing else references its records yet; otherwise corrections use reversals.
- Duplicate detection is scoped and fuzzy (name + DOB + guardian phone; partner name similarity), shown for decision — never auto-merge on name alone.
- Row-level validation messages in sq/en; downloadable error file with an extra "error" column so the user can fix and re-upload.
- **Reconciliation:** after each finance/enrollment import, compare imported totals with control totals the user enters from the source
  (e.g. "income 2023 = 61,250 €", "children autumn 2023 = 210") — mismatches must be resolved or accepted with a reason.
- Real personal data only in production; development uses synthetic samples. Import files are stored privately and purged after a configurable retention period.
- Import permission: owner_admin (all), finance_officer (finance profiles), operations_coordinator (operational profiles). Every job audited.

## API
`POST /imports/upload` (multi-file, zip) · `GET /imports/profiles` (+ templates download) · `PUT /imports/:job/mapping` · `POST /imports/:job/preview` ·
`GET /imports/:job/rows?status=` · `POST /imports/:job/rows/:row/resolve` · `POST /imports/:job/commit` · `POST /imports/:job/rollback` ·
`GET /imports/:job/errors.xlsx` · `/imports/mapping-templates` · `/imports/value-mappings` · `/imports/reconciliation` · `/imports/period-locks`.

## Screens
Import center (jobs list, status, who, when), upload wizard (file → sheet/header → profile → mapping with auto-suggestions → value mapping →
preview with colour-coded rows → duplicates → confirm), reconciliation page per year (2022/23, 2023/24, 2024/25, 2025/26: children, enrollments
per program, income, expenses, investments — source vs imported), historical period locks, templates download page.

## Audit actions
`import.uploaded|mapped|previewed|committed|rolled_back|failed`, `import.duplicate_resolved`, `import.reconciliation_accepted`, `historical_period.locked|unlocked`, `import.template_changed`.

## Sub-steps
- **A.** Framework: multi-format readers (xlsx/xls/ods/csv/tsv/txt/json/xml/zip, PDF best-effort), encoding/locale detection, mapping, value mapping, preview, validation, commit, rollback, error file + tests with sample files in each format.
- **B.** Historical mode, `historical_summary`, reconciliation checks, period locks + tests.
- **C…** One sub-step per import profile in the table order (combine small ones in one session if tokens allow).

## Acceptance tests
- The same partner list imported as `.xlsx`, `.csv` (semicolon, Windows-1250) and `.txt` (tab) produces identical records with correct ë/ç.
- `1.234,56` and `1,234.56` both parse to 1234.56 when the job's decimal setting matches; a mismatch is flagged, not guessed.
- Re-importing the same file creates no duplicates; a corrected file shows a diff and updates by source key.
- Historical import sends no emails/notifications and creates no new consents.
- Income 2023 imported total equals the entered control total, or the mismatch blocks period lock until accepted with a reason.
- A period with both detailed and summary data is counted once in M12 reports.
- PDF-extracted rows cannot be committed without review.
