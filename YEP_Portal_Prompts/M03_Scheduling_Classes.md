# M03 — Cohorts, recurring sessions, holidays, conflicts, calendars

**Depends on:** M00, M01, M02. **Attach with:** `01_MASTER_CONTEXT.md`, `PROGRESS.md`.

## Goal
Turn offerings into real classes: cohorts with instructors, rooms and recurring sessions; handle holidays,
cancellations and replacements; detect conflicts; show calendars per role; notify families of changes.

## Scope
**In:** cohorts, instructor assignment to cohorts, recurrence rules, session generation, holiday calendar,
exceptions (cancel, move, replace), conflict detection, class assignment and transfer of enrollments, calendars,
equipment requirement notes per cohort.
**Out:** attendance (M04), staff pay (M07), inventory reservations (M08 links later).

## Data model (`apps/api/app/modules/scheduling/models.py`)
- `cohort` (offering_id, code e.g. "III B", location_id, room_id nullable, partner_id nullable, capacity, status: planned | running | finished | cancelled, equipment_notes)
- `cohort_instructor` (cohort_id, user_id, role: lead | assistant, valid_from, valid_to) — also creates scoped role assignment (scope = cohort)
- `cohort_enrollment` (cohort_id, enrollment_id, joined_on, left_on) — learners can join mid-course
- `recurrence_rule` (cohort_id, weekday, start_time, end_time, timezone, valid_from, valid_to)
- `holiday` (date, name_sq/en, location_id nullable, partner_id nullable) — org-wide or per school
- `session` (cohort_id, date, start_at, end_at, room_id, status: scheduled | delivered | cancelled | moved, cancel_reason, replaces_session_id nullable, generated_from_rule_id)
  - unique (cohort_id, start_at)

## Rules
- Sessions are generated from rules for a date window by a job/command; generation is idempotent (unique key), skips holidays.
- Changing a rule regenerates only future, not-yet-delivered sessions; delivered sessions are immutable.
- Conflict detection on create/move: same instructor or same room overlapping in time → block with explanation (owner_admin may override with reason + audit).
- Teaching-session counts (sessions delivered) are separate from learner attendance counts (M04).
- Session changes within N days (setting) enqueue notifications to affected guardians and school coordinators.
- Instructors see only cohorts they are assigned to.

## API
`/cohorts` CRUD, `/cohorts/:id/instructors`, `/cohorts/:id/learners` (assign/transfer), `/cohorts/:id/rules`,
`POST /cohorts/:id/generate-sessions?from&to`, `/sessions` (list by range/filters, cancel, move, replace),
`/holidays` CRUD, `GET /calendar?view=family|instructor|location|school&from&to`.

## Screens
Staff: cohort register, cohort detail (learners, instructors, rules, sessions list), weekly timetable grid by location
(like the school timetables in YEP offers: rows = days, columns = time slots), conflict warnings, holiday calendar.
Instructor (mobile): my week. Guardian: my children's upcoming sessions. School coordinator: school timetable (scope only).

## Audit actions
`cohort.created|edited|cancelled`, `cohort.instructor_assigned|removed`, `learner.assigned|transferred|left`,
`rule.created|changed`, `sessions.generated`, `session.cancelled|moved|replaced`, `conflict.overridden`, `holiday.changed`.

## Sub-steps
- **A.** Schema + migration; cohorts, instructors (with scoped role), learner assignment + tests.
- **B.** Recurrence, holidays, idempotent session generation, exceptions, conflict detection + tests.
- **C.** Calendar endpoints and screens (timetable grid, my week, family view) + change notifications.

## Acceptance tests
- Generating sessions twice creates no duplicates; holidays skipped.
- Instructor double-booking is blocked; override requires reason and is audited.
- Instructor A cannot see cohort or learners of instructor B.
- Moving a session notifies affected guardians once (dedupe).
