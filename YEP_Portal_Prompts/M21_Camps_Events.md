# M21 — Summer/winter camps & events (parent information, daily activities, participants)

**Depends on:** M01, M02, M03, M04, M06, M10 (M16 surveys, M19 marketing optional). **Attach with:** `01_MASTER_CONTEXT.md`, `PROGRESS.md`.

## Goal
Run YEP's **summer and winter camps** (and similar short programs: holiday workshops, birthdays, team-building events) end to end:
publish camp weeks, register children, give parents all the information they need, plan and record the daily activities, check
children in and out safely, keep parents updated, and report who participated and what was done — including camps since 2022 (via M13).

## Scope
**In:** camp editions and weeks, themes, daily schedule, per-week/per-day registration with options (full day / half day, early drop-off, late pick-up),
camp pricing (early-bird, sibling, multi-week — via M06 discounts), parent information pack (sq/en PDF + page), required forms
(authorised pick-up persons, care information, photo consent), staff and ratio planning, daily activity log, check-in/check-out,
daily parent updates with photos (consent-checked), incidents, end-of-camp certificates and showcase, camp reports, birthdays and events booking.
**Out:** transport/catering suppliers management beyond expenses (M09).

## Data model (`apps/api/app/modules/camps/models.py`)
- `camp_edition` (name e.g. "Summer Camp 2026", season: summer | winter | spring | autumn | other, year, location_id, age_min, age_max, status: draft | published | running | finished, is_historical)
- `camp_week` (edition_id, offering_id (M01, fee model per week), week_no, start_date, end_date, theme_sq/en, capacity, daily_start, daily_end, half_day_allowed)
- `camp_option` (edition_id, key: early_dropoff | late_pickup | lunch | other, price, capacity nullable)
- `camp_registration` (enrollment_id (M02), camp_week_id, days jsonb (all or selected days), options[], status mirrors enrollment)
- `camp_day_plan` (camp_week_id, date, theme, blocks jsonb: [{time, activity, program/models, materials, staff}]) — the planned day
- `camp_day_log` (camp_week_id, date, delivered_blocks jsonb, highlights_sq/en, photos file_ids[], recorded_by) — what actually happened
- `authorised_pickup` (child_id, name, relationship, phone, id_document_note, valid_from, valid_to, added_by_guardian) — restricted
- `care_information` (child_id, allergies_and_dietary_needs, medication_note, emergency_instructions, updated_by_guardian, updated_at) — **restricted**: visible only to camp staff on duty and owner/operations; minimum necessary; retention ends after the camp + configured days
- `check_event` (child_id, camp_week_id, date, type: check_in | check_out, at, by_staff_id, picked_up_by_pickup_id nullable, note)
- `incident_report` (child_id, date, time, description, action_taken, guardian_informed_at, reported_by) — restricted
- `camp_staffing` (camp_week_id, staff_id, role: lead | instructor | assistant, days) + `ratio_setting` (age band, max_children_per_staff)
- `event_booking` (type: birthday | workshop | team_building, contact party, date, time, location, participants_count, age_range, package, price, status, notes) — for birthdays/events without individual enrollment

## Parent information pack (generated from data, sq/en, page + PDF, sent on confirmation and again 3 days before start)
Dates, daily hours, location and map link, drop-off and pick-up rules (only authorised persons, ID check), what to bring (configurable list),
food and snacks arrangement, daily theme and schedule overview, contact on duty, what to do in case of absence, photo policy, payment status and balance,
link to complete missing forms. Missing required forms (authorised pick-up, care information confirmation) appear as enrollment pending reasons (M02).

## Rules
- Registration, offers, waiting lists, payments and discounts reuse M02 and M06 — camps do not get a separate billing system.
- Capacity per week and per option; staff-to-child ratio checked per day — over-ratio days are flagged before more registrations are accepted.
- Check-out only to a guardian or an `authorised_pickup` valid on that date; any other person → blocked in the app with instruction to call the guardian; every check event audited.
- Daily parent update (in-app + email via M10) built from the day log; photos included only if every identifiable child in them has valid photo consent.
- Care information is guardian-entered, restricted, never sent to AI (M18) or marketing (M19), and purged after the retention period.
- End-of-camp: participation certificate per child (M04 certificate wording rules), optional showcase, satisfaction survey (M16) sent automatically.
- Camp report: participants (unique children, by age and week), attendance per day, activities and themes delivered, staff, incidents count (no details for non-authorised roles), income and costs (M06/M09), satisfaction results.
- Historical camps since 2022 imported via M13 profile `camps` (editions, weeks, participant lists or counts, activities held) with `is_historical = true`.

## API
`/camps/editions` CRUD + publish, `/camps/weeks`, `/camps/options`, `/camps/:week/day-plans`, `/camps/:week/day-logs`, `/camps/:week/roster`,
`POST /camps/:week/check-in|check-out`, `/camps/incidents`, `/camps/:week/staffing`, `GET /camps/:edition/info-pack.pdf?lang=`, `GET /camps/:edition/report`,
guardian: `/me/camps` (registrations, info pack, forms: pickup persons, care info), `/me/camps/updates`; `/events/bookings` CRUD.

## Screens
Public: camp page with weeks, themes, prices, availability, register button. Guardian: camp registration (choose weeks/days/options), info pack,
forms, daily updates feed. Staff (tablet/mobile): today's camp roster with check-in/out, authorised pick-up verification, day plan and day log, incident form.
Office: camp planner (weeks × themes × staff, ratio warnings), registrations board, camp report, birthdays/events calendar.

## Dashboard (adds to M12)
Camp registrations vs capacity per week, unique campers per edition and year (2022 → today), repeat campers, income vs costs per edition, satisfaction score.

## Audit actions
`camp.edition_created|published|finished`, `camp.registration_*` (via M02), `camp.dayplan_changed`, `camp.daylog_recorded`, `camp.checked_in|checked_out|checkout_blocked`,
`camp.pickup_person_added|removed`, `camp.care_info_updated|viewed`, `camp.incident_reported`, `camp.info_pack_sent`, `event.booking_*`.

## Sub-steps
- **A.** Schema + migration; editions, weeks, options linked to M01/M02/M06; public camp page and registration + tests.
- **B.** Parent info pack (page + PDF sq/en), forms (pick-up persons, care info), pending reasons, automatic sending via M10.
- **C.** Day plans/logs, staffing and ratios, check-in/out with pick-up verification, incidents + scope tests for restricted data.
- **D.** Daily parent updates (consent-checked photos), certificates, survey trigger, camp report, events/birthday bookings, dashboard cards.

## Acceptance tests
- A child registered for weeks 1 and 3 with late pick-up gets one invoice with correct lines and sibling discount.
- Missing authorised pick-up form keeps the registration pending and appears in the info pack reminder.
- Check-out to a non-authorised person is blocked and audited.
- Daily update excludes a photo showing a child without photo consent.
- Care information is not visible to an instructor not staffed on that camp week, and is purged after retention.
- Camp report for Summer 2024 (imported) and Summer 2026 (live) shows unique campers, activities held and participants per week side by side.
