# M05 — Schools & partners: CRM pipeline, proposals/quotes, agreements, session confirmation, school workspace

**Depends on:** M01, M03 (M06 for invoicing hook). **Attach with:** `01_MASTER_CONTEXT.md`, `PROGRESS.md`.

## Goal
Model how YEP actually sells to institutions. Example: an offer to a primary school for 13 class groups
(grades I–III), one 90-minute session per group per week, priced **per group per session** with a
**promotional starting price** (e.g. 40 € instead of the regular 60 €), invoiced **monthly by sessions delivered
and confirmed by the school**. The module must support this end to end, without hardcoding any of those numbers.

## Scope
**In:** partner register (schools, kindergartens, NGOs, companies, sponsors), contacts, pipeline stages,
proposals/quotes with options and pricing, promotional pricing with end date, PDF proposal export (sq/en),
agreements, conversion of an accepted proposal into offerings + cohorts, bulk institutional roster import,
school confirmation of delivered sessions, school coordinator workspace.
**Out:** invoice generation itself (M06 consumes confirmed sessions), sponsor dashboards (M12).

## Data model (`apps/api/app/modules/partners/models.py`)
- `partner` (name, type: public_school | private_school | kindergarten | ngo | company | sponsor | other, website, address, municipality,
  relationship_status: lead | contacted | proposal_sent | negotiating | active | paused | ended | lost, effective_from, effective_to, notes)
- `partner_contact` (partner_id, name, role, email, phone, is_primary)
- `partner_activity` (partner_id, type: call | meeting | email | visit | note, date, summary, next_step, next_step_date, owner_id)
- `proposal` (partner_id, number, title, language, status: draft | sent | accepted | rejected | expired | superseded, valid_until, sent_at, decided_at, prepared_by, version, supersedes_id)
- `proposal_option` (proposal_id, label e.g. "Option A – 90 min", program_id, session_minutes, sessions_per_week_per_group, groups_count, weeks_planned,
  regular_price_per_session, promo_price_per_session nullable, promo_valid_until nullable or promo_sessions_limit, price_basis: per_group_session | per_child_month | lump_sum, vat_mode: excluded | included | not_applicable, chosen bool)
- `proposal_group` (proposal_option_id, grade, label e.g. "I A", expected_children)
- `proposal_section` (proposal_id, key: intro | about_us | program | session_flow | schedule | responsibilities | investment | terms | next_steps, body_sq, body_en, order) — editable text blocks with defaults from templates
- `agreement` (partner_id, proposal_id nullable, number, start_date, end_date, billing_cycle: monthly, payment_terms_days, signed_at, file_id, status: draft | signed | active | ended)
- `agreement_price` (agreement_id, program_id, price_basis, regular_price, promo_price, promo_valid_until, vat_mode)
- `session_confirmation` (session_id, partner_id, status: pending | confirmed | disputed, confirmed_by (school coordinator user), confirmed_at, dispute_reason)

## Rules
- Proposal totals are computed, never typed: weekly = groups × sessions/week × price; projections for N weeks; savings = (regular − promo) × sessions. Show both regular and promotional figures when a promo exists.
- Proposal PDF follows the YEP offer structure: cover band, key figures strip, intro letter, sections 01–08 (offer at a glance, about us, program, session flow, timetable, responsibilities, investment, terms & next steps), signature block. Brand colours from master; logo from uploaded asset.
- "About us / experience" content comes from a maintained reference list (`partner.relationship_status = active` with a "can be cited" flag) — never auto-generated claims.
- Accepting a proposal (chosen option) creates an agreement draft, and on agreement activation creates offerings (fee_model `group_per_session`) and cohorts per proposal group, without duplicating if repeated.
- A historical or rejected proposal never makes a partner `active`.
- Bulk roster import for a cohort: CSV/XLSX upload → preview → row-level validation and duplicate check within partner scope → explicit confirm. Never auto-merge children by name; institutional children may have no guardian account (created as institution-managed records with minimal data).
- Delivered sessions at partner schools need confirmation by the school coordinator (or by staff with reason when school confirms offline). Only confirmed sessions are billable (M06).
- School coordinator sees only their partner's cohorts, timetable, aggregate attendance, confirmations and institutional invoices — never household data.

## API
`/partners` CRUD + `/partners/:id/contacts|activities`, `/pipeline` (board), `/proposals` CRUD, `POST /proposals/:id/send|accept|reject|new-version`,
`GET /proposals/:id/pdf?lang=sq`, `/agreements` CRUD + `POST /agreements/:id/activate`, `POST /cohorts/:id/roster-import` (preview) + `/confirm`,
`/session-confirmations` (list pending, confirm, dispute), school workspace: `/school/me/cohorts|timetable|attendance-summary|confirmations|invoices`.

## Screens
Staff: partner register, partner detail (contacts, activity log, proposals, agreements, cohorts), pipeline board,
proposal builder (options side by side, live totals, promo toggle, timetable editor, section texts, PDF preview),
agreement editor, roster import wizard, confirmations queue.
School coordinator: dashboard (cohorts, this month's sessions, pending confirmations), timetable, attendance summary, invoices.

## Audit actions
`partner.created|status_changed`, `partner.activity_logged`, `proposal.created|sent|accepted|rejected|versioned|pdf_generated`,
`agreement.created|signed|activated|ended`, `roster.import_previewed|committed`, `session.confirmed|disputed|confirmed_by_staff`.

## Sub-steps
- **A.** Schema + migration; partners, contacts, activities, pipeline + tests.
- **B.** Proposals with options, groups, sections, computed totals, versioning + tests (totals for 13 groups × 40 € and promo/regular comparison).
- **C.** Proposal PDF (sq/en) using the section structure; agreement + activation creating offerings/cohorts idempotently.
- **D.** Roster import wizard; session confirmation flow; school coordinator workspace + scope tests.

## Acceptance tests
- Proposal for 13 groups, 1 session/week, regular 60 €, promo 40 € → weekly 520 € (regular 780 €), savings 260 €/week; changing promo recalculates everything.
- Two options (e.g. 90 min @ 40 € vs 60 min @ 25 €) render side by side; only the chosen option becomes the agreement.
- Activating the same agreement twice creates cohorts once.
- School coordinator of School X cannot see School Y or any household data.
- Unconfirmed sessions are not billable.
