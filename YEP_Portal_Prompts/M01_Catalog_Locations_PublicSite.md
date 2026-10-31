# M01 — Program catalog, offerings, rooms, public site, inquiries & trial requests

**Depends on:** M00. **Attach with:** `01_MASTER_CONTEXT.md`, `PROGRESS.md`.

## Goal
Staff can define programs and schedule-able offerings; visitors can browse published offerings in Albanian
and English, filter by age and category, and send an inquiry or trial request that staff track to conversion.

## Scope
**In:** program definitions, offerings, rooms, categories, draft/confirmation workflow, public catalog and detail
pages, FAQ and contact page, inquiries, trial requests and their follow-up.
**Out:** applications and enrollment (M02), recurring sessions (M03), payments (M06).

## Data model (`apps/api/app/modules/catalog/models.py`)
- `program` (code, name_sq, name_en, category: course | camp | workshop | birthday | team_building | inclusive | other,
  description_sq/en, learning_objectives_sq/en, delivery: physical_build | screen_based | mixed, status: draft | confirmed | archived,
  is_proposed bool, confirmed_by, confirmed_at)
- `program_confirmation` flags per field: eligibility_confirmed, duration_confirmed, price_confirmed, availability_confirmed
- `room` (location_id, name, capacity)
- `offering` (program_id, location_id, partner_id nullable [FK added in M05], title override, language: sq | en | mixed,
  age_min, age_max, age_reference_date, start_date, end_date, session_minutes, sessions_planned, capacity,
  fee_model: per_child_term | per_child_month | per_session | group_per_session | free | sponsored, list_price, currency,
  visibility: draft | internal | published, registration_open bool, waitlist_enabled bool)
- `inquiry` (name, email, phone, child_age nullable, program_id nullable, message, source, utm_source/medium/campaign/content nullable, promo_code nullable, heard_about_us nullable, status: new | contacted | trial_booked | converted | closed, assigned_to, closed_reason)
- `trial_booking` (inquiry_id, offering_id, date_time, status: requested | scheduled | attended | no_show | cancelled, outcome_note)
- `faq` (question_sq/en, answer_sq/en, order, published)

Seed program names from master §1 as `draft` with all confirmation flags false. Web Development: `is_proposed = true`.

## Rules
- Camps (summer/winter), birthdays and events have their own workflows in M21; M01 only holds their catalog entries.
- An offering is publicly visible and open for registration only when its program is `confirmed`, the offering is `published`, and the price/eligibility flags are confirmed. Otherwise show nothing publicly.
- Never derive a program's ages from the overall 4–16 range; ages are entered per offering.
- Session length is configurable per offering (no universal 60/75/90).
- Inquiry form is spam-protected (honeypot + rate limit). No account needed to inquire.
- Inquiry and trial status changes follow state machines in `apps/api/app/modules/catalog/state_machines.py` (exposed to the web app via OpenAPI enums).

## API
`GET /public/offerings?age&category&location&language` · `GET /public/offerings/:slug` · `GET /public/faqs` ·
`POST /public/inquiries` · `POST /public/trial-requests` ·
staff: CRUD `/programs`, `/offerings`, `/rooms`, `/faqs`; `POST /programs/:id/confirm`; `/inquiries` list/assign/transition;
`/trial-bookings` schedule/transition.

## Screens
Public: home (intro to YEP, contact), catalog with filters, offering detail (objectives, eligibility, format,
location, language, session length, dates, capacity status, confirmed fee), FAQ, contact, inquiry and trial forms.
Staff: programs register, program editor with confirmation checklist, offerings register, rooms, inquiries board
(new → contacted → trial → converted/closed), trial calendar list.

## Permissions (summary)
owner_admin: all. operations_coordinator: programs view/edit (not confirm price), offerings CRUD, inquiries & trials all.
finance_officer: view programs/offerings, confirm price flag. Others: public views only.

## Audit actions
`program.created|edited|confirmed|archived`, `offering.created|edited|published|unpublished`, `inquiry.received|assigned|transitioned`, `trial.scheduled|transitioned`.

## Sub-steps
- **A.** Schema + migration + seed drafts; programs/offerings/rooms APIs with permissions, audit, tests.
- **B.** Inquiries + trial bookings APIs and state machines + tests.
- **C.** Public pages (sq/en), filters, forms; staff registers and editors; Playwright test: published offering appears, draft does not.

## Acceptance tests
- Draft or unconfirmed offerings never appear in public endpoints or pages.
- Inquiry → trial scheduled → attended → converted is tracked with audit history.
- Coordinator cannot confirm price; finance officer can; both actions audited.
