# M04 — Attendance, lesson delivery, learning progress, feedback, projects, certificates

**Depends on:** M03. **Attach with:** `01_MASTER_CONTEXT.md`, `PROGRESS.md`.

## Goal
Instructors run a session from their phone: open roster, mark attendance, record what was delivered,
note progress, and publish selected feedback to guardians. Staff issue certificates on completion.

## Scope
**In:** attendance, attendance corrections, lesson plans vs delivered record, program objectives, progress
assessments, private notes vs published feedback, follow-up flags, projects with protected uploads,
completion criteria, certificates with verification and revocation, monthly program reports per cohort.
**Out:** instructor pay (M07), dashboards (M12).

## Data model (`apps/api/app/modules/learning/models.py`)
- `lesson_plan` (program_id, sequence, title_sq/en, model_name, principles, objectives_ids) — the planned curriculum (e.g. Bricks Challenge models: Race Car, Rescue Winch, Conveyor Belt…)
- `session_delivery` (session_id unique, delivered_by, lesson_plan_id nullable, topic, activities, extra_activity, observations, delivered_at)
- `attendance` (session_id, child_id, status: present | absent | late | excused, recorded_by, recorded_at) unique (session_id, child_id)
- `attendance_correction` (attendance_id, old_status, new_status, reason, corrected_by, corrected_at)
- `learning_objective` (program_id, code, text_sq/en)
- `progress_record` (child_id, cohort_id, objective_id, level: not_started | developing | achieved | exceeded, note, recorded_by, session_id nullable)
- `staff_note` (child_id, cohort_id, text, created_by) — private, never shown to guardians
- `feedback` (child_id, cohort_id, text_sq/en, status: draft | published | withdrawn, published_by, published_at)
- `follow_up_flag` (child_id, raised_by, reason, assigned_to, status: open | resolved)
- `project` (child_id, cohort_id, title, description, file_ids[], visibility: staff | guardian)
- `completion_rule` (offering_id, min_attendance_pct, required_objectives, other)
- `certificate` (child_id, enrollment_id, certificate_no unique, issued_by, issued_at, wording_key, revoked_at, revoke_reason, verification_code)

## Rules
- Attendance can be recorded by the cohort's assigned instructors; after a configurable lock period, changes require an `attendance_correction` with reason.
- Attendance-rate definition (document it in UI): numerator = present + late; denominator = delivered sessions while the learner was in the cohort (from `joined_on`); cancelled sessions excluded; excused counted as setting (default: excluded from denominator).
- Lesson plans (what should happen) are separate from session_delivery (what happened).
- Guardians see only published feedback, their own child's attendance and guardian-visible projects. Never staff notes.
- Certificates only by owner_admin/operations_coordinator; wording comes from an admin-maintained template; never say "accredited/internationally recognised" unless admin-supplied verified wording exists.
- Public `GET /public/certificates/verify/:code` returns only name initials, program and issue date.
- Monthly cohort report (PDF, sq): period, participants, sessions with models and principles taught, attendance %, highlights — like YEP's existing monthly program reports for partner schools.

## API
Instructor: `GET /my/sessions/today`, `GET /sessions/:id/roster`, `PUT /sessions/:id/attendance` (bulk), `PUT /sessions/:id/delivery`,
`POST /progress`, `POST /feedback` (draft), `POST /feedback/:id/publish`, `POST /follow-ups`, `/projects`.
Staff: `/attendance/corrections`, `/objectives`, `/lesson-plans`, `/completion-rules`, `/certificates` (issue, revoke, PDF), `/cohorts/:id/monthly-report?month=`.
Guardian: `/me/children/:id/attendance`, `/me/children/:id/feedback`, `/me/children/:id/projects`, `/me/certificates`.

## Screens
Instructor (mobile-first): today's classes, roster with one-tap status, delivery form, quick progress, feedback drafts, follow-ups.
Staff: lesson plan library per program, objectives, attendance corrections log, certificates register, monthly report generator.
Guardian: child progress timeline, published feedback, attendance summary, certificates download.

## Audit actions
`attendance.recorded|corrected`, `delivery.recorded`, `progress.recorded`, `feedback.published|withdrawn`,
`followup.raised|resolved`, `project.uploaded`, `certificate.issued|revoked`, `report.generated`.

## Sub-steps
- **A.** Schema + migration; attendance + corrections + delivery + tests (scope: assigned instructor only).
- **B.** Objectives, lesson plans, progress, notes, feedback publish flow, follow-ups, projects + tests.
- **C.** Completion rules, certificates (PDF, verify, revoke), monthly cohort report PDF.
- **D.** Instructor mobile screens, guardian views, staff screens; Playwright: instructor records, guardian sees only published feedback.

## Acceptance tests
- Guardian never receives staff notes or other children's data in any endpoint.
- Attendance correction keeps original value and reason.
- Attendance rate matches documented definition for a learner who joined mid-course.
- Revoked certificate shows as revoked on public verification.
