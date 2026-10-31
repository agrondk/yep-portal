# M20 — Staff training & onboarding (welcome package, internal trainings, program certification)

**Depends on:** M00, M07 (M04 for shadowing sessions, M08 for equipment handover). **Attach with:** `01_MASTER_CONTEXT.md`, `PROGRESS.md`.

## Goal
Every new instructor or staff member goes through a structured **welcome package**, and all internal trainings are planned,
attended, completed and tracked, so YEP knows who is qualified to teach which program and when refreshers are due.

## Scope
**In:** onboarding plans (welcome package) with checklists, documents to read and acknowledge, training catalogue, training sessions
(in person / online), materials, attendance, assessments/sign-off, program certification that updates instructor qualifications (M07),
shadowing and supervised teaching, refresher/expiry reminders, trainer hours to timesheets, onboarding and training reports, historical training import (M13).
**Out:** external HR/payroll systems; e2 Young Engineers' own training portals (only record completion and upload certificates).

## Data model (`apps/api/app/modules/training/models.py`)
- `onboarding_template` (name e.g. "Instructor welcome package", role, version, active)
- `onboarding_task_template` (template_id, order, title_sq/en, type: document_ack | training | shadowing | equipment_handover | portal_setup | meeting | other,
  document_file_id nullable, training_course_id nullable, due_offset_days, required bool, owner_role)
- `onboarding_plan` (staff_id, template_id, version, start_date, mentor_id, status: active | completed | cancelled, completed_at)
- `onboarding_task` (plan_id, task_template_id, due_date, status: todo | done | waived, done_at, confirmed_by, note, waive_reason)
- `policy_document` (key, title_sq/en, version, file_id, requires_ack, effective_from) + `policy_acknowledgement` (document_id, staff_id, acknowledged_at) — append-only
- `training_course` (code, title_sq/en, category: welcome | methodology | program | safeguarding | first_aid | customer_service | portal | other, program_id nullable,
  duration_minutes, delivery: in_person | online | self_study | external, validity_months nullable, grants_qualification_level nullable, materials file_ids[])
- `training_session` (course_id, starts_at, ends_at, location_id nullable, online_link nullable, trainer_id, capacity, status: planned | held | cancelled)
- `training_participant` (session_id, staff_id, status: invited | attended | absent | excused, score nullable, passed bool nullable, certificate_file_id nullable)
- `training_completion` (staff_id, course_id, completed_on, valid_until, source: session | external | historical_import, evidence_file_id)
- `shadowing_record` (staff_id, session_id (M03), mentor_id, type: observe | co_teach | supervised_lead, feedback, sign_off bool)

## Default welcome package (seeded as draft template — owner edits before use)
1. Welcome meeting and introduction to YEP and the e2 Young Engineers network.
2. Read and acknowledge: code of conduct, child safeguarding and protection, data protection and photo rules, health & safety, emergency procedures.
3. Portal training: instructor app (attendance, delivery notes, feedback, equipment).
4. Methodology training: Learn – Explore – Play, classroom management for ages 4–16.
5. Program training for assigned programs (e.g. Bricks Challenge models and principles) with sign-off.
6. Shadowing: observe 2 sessions, co-teach 2 sessions, lead 1 supervised session (numbers configurable).
7. Equipment handover (kits, laptop) recorded in M08 with acknowledgement.
8. First-month check-in with mentor.
The seed is a starting structure only; content, counts and documents are confirmed by the owner.

## Rules
- Hiring/invitation of an instructor (M00/M07) automatically creates an onboarding plan from the active template for that role.
- An instructor can be assigned as **lead** on a cohort (M03) only after required onboarding tasks and the program certification are complete;
  assignment before that is blocked or requires owner override with reason (audited). Assistant roles allowed during shadowing.
- Passing a program course creates/updates `staff_program_qualification` (M07) with the course's level and validity.
- Expiring completions (e.g. first aid, safeguarding refresher) trigger reminders 30 days before `valid_until` (job registry) and show on dashboards.
- Training hours: attended sessions create `timesheet_entry` type `training` for participants and trainers (M07), paid only if pay rules say so.
- Staff see their own plan, trainings and certificates; mentors see their mentees; owner/operations see all; training records are staff personal data (restricted).
- Historical trainings since June 2022 can be imported (M13 profile `trainings`) as completions with source `historical_import`.

## API
`/training/onboarding-templates` (+ tasks), `/training/onboarding-plans` (create, tasks complete/waive), `/training/policies` (+ acknowledge),
`/training/courses`, `/training/sessions` (schedule, invite, attendance, results), `/training/completions`, `/training/shadowing`,
`/my/onboarding`, `/my/trainings`, `GET /training/reports?period` (completion rates, expiring certifications, qualified instructors per program).

## Screens
Owner/operations: welcome package builder, onboarding board (each new staff member with progress %), training calendar, course catalogue,
session attendance & results, qualification matrix (staff × programs with expiry colours), expiring certifications list.
Staff (mobile): "My onboarding" checklist with documents to acknowledge, upcoming trainings, my certificates.

## Dashboard (adds to M12 Staff view)
Onboarding in progress, average days to complete, trainings held this period, attendance rate, qualified instructors per program, certifications expiring in 30/60 days.

## Audit actions
`onboarding.plan_created|task_completed|task_waived|completed`, `policy.acknowledged`, `training.course_changed|session_scheduled|attendance_recorded|result_recorded`,
`training.completion_recorded|expired`, `qualification.granted_from_training`, `shadowing.signed_off`, `assignment.override_untrained`.

## Sub-steps
- **A.** Schema + migration, policies & acknowledgements, onboarding templates and plans (auto-created on hire), seeded draft welcome package + tests.
- **B.** Courses, sessions, participants, results, completions, M07 qualification and timesheet links, expiry reminders + tests.
- **C.** Shadowing records, M03 lead-assignment guard, screens (builder, board, qualification matrix, my onboarding), dashboard cards.

## Acceptance tests
- Inviting a new instructor creates one onboarding plan with dated tasks; completing all required tasks marks it complete.
- Assigning an uncertified instructor as lead is blocked; owner override needs a reason and is audited.
- Passing "Bricks Challenge program training" grants the qualification with validity; expiry reminder is sent once 30 days before.
- An instructor cannot see another staff member's training records.
