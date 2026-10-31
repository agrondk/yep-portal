# M12 — Role dashboards, reporting, finance dashboard, activity history UI, sponsor workspace

**Depends on:** M02–M09 and M16 (works with whatever modules are done; hide cards for missing ones). **Attach with:** `01_MASTER_CONTEXT.md`, `PROGRESS.md`.

## Goal
Each role opens the portal and sees what needs attention today; management and finance see trustworthy,
defined, database-backed metrics with MTD/YTD and drill-downs; sponsors see aggregated results of what they fund.

## Scope
**In:** metric definitions registry, role dashboards (management, operations, finance, instructor, guardian, school, sponsor),
reports with filters (period, location, program, partner, initiative), MTD/YTD/custom/comparison, drill-down to source records,
CSV export and printable reports, daily activity dashboard over `audit_event`, sponsor initiatives and workspace.
**Out:** BI tool integration (CSV export is enough for now).

## Data model (`apps/api/app/modules/reporting/models.py`)
- `metric_definition` (key, name_sq/en, numerator, denominator, population, date_basis, exclusions, owner) — shown as tooltip/footnote
- `initiative` (sponsor_party_id, name, scope text, start/end, target_children, target_sessions, budget_amount) + links to cohorts/enrollments/funding
- `saved_report` (user_id, report_key, filters jsonb)
- Use SQL views or materialised views (`reporting.*`) refreshed by a Celery Beat job for heavy aggregates; always show "as of" time.
- Report services live in `app/modules/reporting/service.py` and are the only way to compute metrics — dashboards, exports, M17 features and M18 "ask your data" all call them.

## Dashboards
- **Owner summary (one page, landing page for owner_admin):** one headline number per area for the selected month and year-to-date,
  each with comparison to the previous period and a link to its detailed view:
  | Area | Headline metrics |
  | --- | --- |
  | Enrollment | active unique children, new enrollments, conversion rate, seats filled % |
  | Delivery | sessions delivered, average attendance %, active cohorts, active partner schools |
  | Satisfaction | satisfaction score (1–5) and % satisfied, NPS, response count (M16) |
  | Finance in | invoiced, received, outstanding receivables |
  | Finance out | expenses incurred, expenses paid, upcoming bills and pay statements |
  | Staff | active instructors, sessions taught, staff cost, staff cost per session |
  | Investments | equipment purchased (capital), current equipment value in use, loan principal outstanding (when M14 exists) |
  Cards for modules not yet built are hidden, not shown as zero. When M17/M18/M19 exist, add cards: children at high risk, next-term forecast, invoices at risk, the "Ask your data" box, marketing (open suggestions, spend vs budget, cost per enrollment) and a **program profitability** view (income vs allocated costs per program, date basis labelled).
- **Satisfaction (from M16):** satisfaction score and NPS over time, by program, instructor, school and location; response rates;
  latest comments by tag (praise, complaint, suggestion); open follow-ups. Minimum group size from M16 applies to every breakdown.
- **Staff (from M07, M03, M04):** per instructor — sessions taught, hours (all timesheet types), substitutions, average attendance in their cohorts,
  satisfaction for their cohorts (aggregated, minimum group size), cost and cost per session; totals per program and location;
  workload vs availability (utilisation %). Cost figures visible only to finance_officer and owner_admin.
- **Investments (from M08, M09, M06, M14):** capital purchases by year and category, assets in use / in repair / lost / disposed,
  current book value (cost minus configured straight-line depreciation per category, labelled as an estimate; depreciation rules set by finance),
  kits per program and cost per child served per kit, upcoming maintenance costs, loans outstanding and next installments (when M14 exists).
  Capital spending is shown separately from operating expenses — never added to them.
- **Management:** application funnel & conversion, enrollments vs capacity, waiting lists & expiring offers, attendance & retention, delivered sessions,
  active partners and unique children per program per partner, invoiced / received / outstanding, expenses incurred / paid, upcoming liabilities. MTD + YTD.
- **Operations:** applications needing action, enrollments pending (with reasons), capacity/scheduling conflicts, sessions awaiting school confirmation, upcoming renewals, low stock.
- **Finance (restricted):** invoiced vs received, receivables aging, expenses incurred vs paid, unpaid supplier balances, upcoming recurring bills and pay statements,
  cash in/out by account (labelled "recorded net cash movement" unless opening balance reconciled), budget vs actual by program/location. Never present cash as profit.
- **Instructor:** today's classes, attendance to complete, feedback/follow-ups.
- **Guardian:** each child's status, next session, required actions, balance, new feedback.
- **School coordinator:** cohorts, sessions this month, pending confirmations, attendance summary, invoices.
- **Sponsor (read-only):** initiatives, targets vs actual (clearly separated), planned vs delivered sessions, participation/attendance/completion (aggregated, no child identities, minimum group size to avoid identification), budget vs spent, approved downloadable reports.

## Rules
- **History from June 2022:** all dashboards and reports accept periods back to 1 June 2022 and offer year-on-year comparison by school year
  (Sep–Aug, configurable) and calendar year: 2022/23, 2023/24, 2024/25, 2025/26 …; filters by branch/location, program, partner and camp edition.
  Detailed and `historical_summary` data are combined without double counting and summary figures are labelled.
- Every number shows period, as-of, timezone, population, definition and date basis.
- MTD = 1st of selected month → as-of date; YTD from configured reporting-year start (default calendar year, labelled if fiscal).
- Unique children deduplicated across programs/partners; enrollments counted separately.
- Active partner = relationship_status active and effective dates overlapping the period; show whether it had active cohorts/enrollments.
- Drill-downs and exports respect scope; activity feed never leaks finance or private staff events to less-privileged roles.
- No hardcoded demo totals in production code paths.

## API
`GET /dashboards/:role`, `GET /reports/:key?filters`, `GET /reports/:key/export.csv|pdf`, `/metrics/definitions`,
`/activity?date&actor&action&entity&partner&cohort&outcome` (paginated), `/initiatives` CRUD, `/sponsor/me/*`.

## Sub-steps
- **A.** Metric registry, reporting views, management + operations dashboards + tests for dedupe and MTD/YTD.
- **B.** Finance dashboard + reports with date-basis labels + tests.
- **C.** Role dashboards (instructor, guardian, school), activity history UI with scoped filters and export.
- **D.** Initiatives and sponsor workspace with aggregation thresholds + scope tests.
- **E.** Satisfaction, Staff and Investments dashboards (metric definitions registered, role restrictions on cost data) + tests.
- **F.** Owner summary page with period comparison and drill-down links; hide cards for unbuilt modules + Playwright test.

## Acceptance tests
- Partner/program report deduplicates children; totals across programs ≠ sum of enrollments when children overlap.
- Changing reporting-year start changes YTD and the label.
- Sponsor user cannot retrieve any identifiable child record via dashboards, exports or activity.
- Owner summary numbers equal the totals in each detailed view for the same period (no separately computed figures).
- Capital equipment purchases appear under Investments and are excluded from operating expenses.
- Operations coordinator sees staff hours but not staff cost; finance officer sees both.
- Satisfaction breakdowns below the minimum response count show "not enough responses".
