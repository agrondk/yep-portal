# M16 — Feedback & satisfaction surveys

**Depends on:** M02, M04, M05, M10 (M12 consumes the results). **Attach with:** `01_MASTER_CONTEXT.md`, `PROGRESS.md`.

## Goal
Measure parent, school and (optionally) student satisfaction in a structured, repeatable way, so management sees
real satisfaction scores and comments by program, instructor, school and period — never typed-in or invented figures.

## Scope
**In:** survey templates (sq/en), question types, versioning, distribution rules (end of term, after trial class,
mid-term check, after camps/birthdays/workshops, school end-of-agreement review), invitations via M10, anonymous or
identified responses, reminders, response collection on mobile, comment moderation/tagging, NPS and satisfaction
scores, follow-up actions on low scores, results views per program/instructor/school/period.
**Out:** public review publishing or testimonials (never publish responses as testimonials without explicit written consent).

## Data model (`apps/api/app/modules/surveys/models.py`)
- `survey_template` (key, title_sq/en, audience: guardian | school_coordinator | student | staff, version, status: draft | active | retired, anonymous bool, created_by)
- `survey_question` (template_id, order, type: rating_1_5 | nps_0_10 | single_choice | multi_choice | yes_no | text, text_sq/en, options jsonb, required, metric_tag: overall_satisfaction | nps | instructor | content | communication | value_for_money | facilities | schedule | other)
- `survey_campaign` (template_id, trigger: manual | end_of_offering | after_trial | mid_term | agreement_review, target_type: offering | cohort | partner | program | all_guardians,
  target_id, open_from, open_until, reminder_days, status: scheduled | open | closed, created_by)
- `survey_invitation` (campaign_id, recipient_user_id, subject refs: child_id, cohort_id, instructor_id, partner_id (stored even when anonymous, for aggregation only), token_hash, sent_at, reminded_at, responded_at)
  - unique (campaign_id, recipient_user_id, child_id)
- `survey_response` (campaign_id, invitation_id nullable when anonymous, submitted_at, locale, dims snapshot: program_id, offering_id, cohort_id, instructor_id, partner_id, location_id)
- `survey_answer` (response_id, question_id, value_numeric, value_text, value_options)
- `comment_tag` (response_id, question_id, tag: praise | complaint | suggestion | safety | pricing | scheduling | other, sentiment: positive | neutral | negative, tagged_by: staff | ai) — AI tagging added in M18
- `survey_follow_up` (response_id, reason: low_score | complaint | safety, assigned_to, status: open | contacted | resolved, note)

## Rules
- Campaigns are created by owner_admin or operations_coordinator; automatic triggers configurable (e.g. survey 3 days after an offering ends).
- One response per invitation (per child for guardians with several children); links expire at `open_until`.
- **Anonymous surveys:** responses are not linked to the user in any API or export; dimensions (program, cohort, instructor) are stored for aggregation only, and results are shown only when a group has at least **5 responses** (configurable) to avoid identifying anyone.
- Identified surveys may trigger follow-ups: score ≤ 2 of 5 or NPS ≤ 6 creates a follow-up task for operations (configurable thresholds).
- Instructors see aggregated results for their own cohorts only (with the same minimum group size), never individual identified answers unless admin enables it.
- School coordinators see their own school's aggregated results; sponsors only the aggregated satisfaction for initiatives they fund.
- Metric definitions (registered in M12 `metric_definition`):
  - **Satisfaction score** = average of `overall_satisfaction` (1–5) and **% satisfied** = share of answers 4–5.
  - **NPS** = % promoters (9–10) − % detractors (0–6), shown with response count.
  - **Response rate** = responses ÷ invitations sent in the campaign.
- Never present a score without its response count, period and population.
- Free-text answers are personal data: retention rules apply; exports exclude identities for anonymous surveys.

## API
`/surveys/templates` CRUD + versions, `/surveys/campaigns` (create, schedule, open, close, send reminders), `GET /surveys/campaigns/:id/results`,
`/surveys/responses/:id/tags`, `/surveys/follow-ups` (list, assign, resolve), public: `GET|POST /s/:token` (mobile form),
`GET /surveys/results?groupBy=program|instructor|partner|period&from&to`, school: `/school/me/survey-results`, instructor: `/my/survey-results`.

## Screens
Template builder (questions, preview in sq/en), campaign wizard (audience, timing, reminders, recipient count), mobile response form (no login needed via token),
results page (scores, NPS, response rate, trend, comments with tags, filters), follow-up board, instructor and school result views.

## Seed templates (draft, editable)
- Parent end-of-term survey: overall satisfaction, child enjoyed classes, learned new skills, instructor, communication, value for money, would recommend (NPS), comments.
- After-trial-class survey: short — experience, likelihood to enroll, comments.
- School partner review: delivery quality, punctuality, communication, student engagement, would continue next year, comments.

## Audit actions
`survey.template_changed`, `survey.campaign_created|opened|closed`, `survey.invitations_sent|reminded`, `survey.response_submitted` (no answer content in audit),
`survey.comment_tagged`, `survey.followup_created|resolved`, `survey.results_exported`.

## Sub-steps
- **A.** Schema + migration, templates and questions, campaign creation and invitations via M10 + tests.
- **B.** Token response form (mobile), anonymity rules, reminders job, auto-triggers + tests.
- **C.** Results aggregation with minimum group size, NPS/satisfaction metrics, comment tags, follow-ups, role views + scope tests.

## Acceptance tests
- An anonymous survey with 4 responses for a cohort shows "not enough responses"; at 5 it shows aggregates and no identities anywhere (API, export, audit).
- A guardian with two children receives one invitation per child and can answer each once.
- A score of 2/5 on an identified survey creates one follow-up task.
- NPS computed correctly for a known set (e.g. 6 promoters, 2 passives, 2 detractors → NPS 40, n = 10).
