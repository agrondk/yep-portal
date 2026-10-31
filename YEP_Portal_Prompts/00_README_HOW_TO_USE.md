# YEP Portal — Prompt Pack: How to Use

This pack replaces the single consolidated prompt (`YepAllInOneAppPrompt_Consolidated.txt`).
It splits the portal into one prompt per module so an AI coding assistant can build it
in small, bounded sessions without running out of context or credits.

**Stack:** TypeScript front end (Next.js) · Python back end (FastAPI, SQLAlchemy, Alembic, Celery) · PostgreSQL ·
ML with scikit-learn/statsmodels and an AI assistant through an LLM provider adapter. Details in `01_MASTER_CONTEXT.md` §2.

## Files

| File | Purpose | Attach when |
| --- | --- | --- |
| `01_MASTER_CONTEXT.md` | Organization facts, fixed tech stack, conventions, shared rules | **Every session** |
| `02_PROGRESS_TEMPLATE.md` | Running build log the assistant updates | **Every session** (as `PROGRESS.md` in the repo) |
| `M00_Foundation.md` | Repo, database, auth, roles/scopes, audit, files, jobs, i18n shell | Session 1 |
| `M01_Catalog_Locations_PublicSite.md` | Programs, offerings, locations, public catalog, inquiries, trials | After M00 |
| `M02_Families_Applications_Enrollment.md` | Households, children, applications, offers, waiting list, enrollment, consent | After M01 |
| `M03_Scheduling_Classes.md` | Cohorts, recurring sessions, holidays, conflicts, calendars | After M02 |
| `M04_Attendance_Progress_Certificates.md` | Attendance, lesson delivery, progress, feedback, certificates | After M03 |
| `M05_Schools_Partners_Proposals.md` | Partner CRM, school offers/quotes, agreements, session confirmation, school workspace | After M03 |
| `M06_Billing_Payments_Ledger.md` | Shared financial ledger, invoices (family + institutional), payments, refunds | After M02 + M05 |
| `M07_Instructors_Staff_Hours.md` | Staff profiles, availability, sessions taught, monthly pay statements | After M04 + M06 |
| `M08_Inventory_Assets.md` | Kits, assets, stock movements, assignments, maintenance | After M00 (finance links after M06) |
| `M09_Expenses_Suppliers_Budgets.md` | Supplier bills, approvals, recurring bills, budgets | After M06 |
| `M10_Communications_Messaging.md` | Templates, announcements, parent–staff messages, preferences | After M02 |
| `M11_Franchise_Reporting.md` | e2 Young Engineers fees and periodic franchise reports | After M06 + M04 |
| `M12_Dashboards_Reporting_Sponsors.md` | Owner summary, role dashboards (enrollment, finance, satisfaction, staff, investments), MTD/YTD reports, sponsor workspace, activity history UI | After M04–M09, M16 |
| `M13_Data_Import.md` | Historical migration since June 2022 + imports from xlsx/xls/ods/csv/txt/json/xml/zip (PDF best-effort): branches, partners, programs, students, enrollments, camps, staff, trainings, income, expenses, investments, loans | Framework early; one profile after each target module |
| `M14_Loans_Cash_Accounts.md` | Loans and bank/cash account balances — **deferred phase** | Only when needed |
| `M15_Hardening_Release.md` | Backups, restore test, security review, all acceptance scenarios | Last |
| `M16_Feedback_Surveys.md` | Parent/school satisfaction surveys, NPS, comments, follow-ups | After M04 + M10 (before M12 step E) |
| `M17_ML_Predictions.md` | Dropout risk, demand forecast, late-payment risk (advisory) | After ≥ 2 terms of real data |
| `M20_Staff_Training_Onboarding.md` | Welcome package, internal trainings, program certification, shadowing, expiry reminders | After M07 |
| `M21_Camps_Events.md` | Summer/winter camps, parent info pack, daily activities, check-in/out, participants, birthdays & events | After M02, M04, M06, M10 |
| `M19_Marketing_Social_Media.md` | Campaigns, Facebook/Instagram posts, tracking & ROI, ML/rule triggers, AI-generated campaign drafts | Basics after M10/M12; triggers + AI after M17/M18 |
| `M18_AI_Assistant.md` | AI drafting, survey comment analysis, "ask your data", translation | Drafting after M05/M10; rest after M12/M16 |

## Recommended release plan

- **Release 1 (go-live minimum):** M00, M01, M02, M03, M04, M05, M06, M10, M13 (framework + historical profiles for the modules above, reconciled before go-live)
- **Release 2 (operations & insight):** M07, M20, M21 (before the next summer camp), M08, M09, M11, M16, M12, remaining M13 profiles, M19 steps A–C (campaigns, tracking, publishing)
- **Release 3 (optional finance depth):** M14
- **Release 4 (intelligence):** M18 drafting/translation can come earlier; M17, the rest of M18 and M19 steps D–F (smart triggers, AI campaigns, marketing ROI) once enough history exists
- **Before every production release:** M15

## How to run a session (token-saving rules)

1. **Start a new chat for each module.** Do not continue a long chat into the next module.
2. Attach only three things: `01_MASTER_CONTEXT.md`, the module prompt, and the repo's current `PROGRESS.md`.
   Do not paste the old consolidated prompt or other module prompts.
3. Each module prompt is split into **sub-steps (A, B, C…)**. Ask the assistant to do **one sub-step per reply**,
   then stop, summarise, and update `PROGRESS.md`. Continue with "Proceed with step B".
4. If a module is still too large, start a fresh chat at the next unfinished sub-step —
   `PROGRESS.md` carries the state forward.
5. Tell the assistant to show **only changed or new files** (or diffs), never reprint unchanged files,
   and never dump the full database schema.
6. Run the tests locally after each sub-step and paste back **only failing output**.

## Opening message to paste in each session

```
You are continuing the YEP Portal build. Read 01_MASTER_CONTEXT.md and PROGRESS.md first,
then implement module <MXX>, sub-step <A>. Follow the master conventions exactly.
Inspect only the files you need. Output only new/changed files. When the sub-step is done:
run/describe the tests, update PROGRESS.md, list anything incomplete, and stop.
```

## Decisions to confirm before starting (defaults are already in the master context)

| Decision | Default chosen | Change if… |
| --- | --- | --- |
| Hosting | One EU VPS (e.g. Hetzner) with Docker Compose | You prefer a managed platform |
| Public website | Portal at `portal.` subdomain; existing site links to the catalog | You want the portal to replace the site |
| Online card payments | Off at launch (cash + bank transfer recorded manually) | A Kosovo payment provider is contracted |
| Email | SMTP provider via environment config; dev outbox otherwise | — |
| SMS / Viber | Not in Release 1 | Parents need it |
| VAT (TVSH) | Configurable rates, off until finance confirms | Accountant confirms treatment |
| Social media | Manual posting adapter until a Meta app is approved for Facebook/Instagram publishing | Meta app review done |
| AI provider | Anthropic Claude API via adapter, budget cap, no child personal data sent | You prefer another provider |
| Expected scale | ≤ 3,000 learners, ≤ 50 staff, 1 organization, several locations | Much larger |
