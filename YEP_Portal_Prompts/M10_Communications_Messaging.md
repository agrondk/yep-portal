# M10 — Communications: templates, notifications, announcements, parent–staff messages, preferences

**Depends on:** M00 outbox, M02 (others add their templates). **Attach with:** `01_MASTER_CONTEXT.md`, `PROGRESS.md`.

## Goal
Reliable, bilingual communication: transactional notifications from every module, targeted announcements,
and private guardian ↔ staff conversations, all through the M00 outbox with delivery history.

## Scope
**In:** template library (sq/en) with variables, notification catalogue per module event, preferences, essential vs
marketing separation, marketing consent, announcements by cohort/school/offering/program, in-app inbox,
guardian ↔ staff conversations, delivery status and failures view, development outbox viewer.
**Out:** SMS/Viber (adapter interface only), student messaging (not allowed).

## Data model (`apps/api/app/modules/comms/models.py`)
- `message_template` (key, channel: email | in_app, subject_sq/en, body_sq/en (Markdown + variables), category: essential | marketing, version, active)
- `notification_preference` (user_id, category, channel, enabled) — essential cannot be disabled for email
- `marketing_consent` (user_id, granted bool, source, at) — append-only
- `announcement` (title_sq/en, body_sq/en, audience_type: cohort | partner | offering | program | all_guardians, audience_id, scheduled_for, sent_at, created_by, status)
- `conversation` (household_id or partner_id, subject, created_by, status: open | closed) + `conversation_participant` (conversation_id, user_id)
- `message` (conversation_id, sender_id, body, file_ids[], created_at, read_by jsonb)
- delivery uses `outbox_message` (M00) + `delivery_attempt` (outbox_id, attempt_no, at, result, provider_message_id)

## Rules
- Every module event that notifies uses a template key, e.g. `application.submitted`, `offer.created`, `offer.expiring`, `enrollment.confirmed`,
  `invoice.issued`, `invoice.overdue`, `session.changed`, `feedback.published`, `proposal.sent`, `session.confirmation_requested`.
- Recipient's saved locale chooses the language.
- Business change + outbox entry in the same transaction; worker sends with retry limits and dedupe; failures visible to admins.
- Scheduled announcements run via the job registry.
- Conversations: guardians only with staff (never with other guardians or students); school coordinators with staff about their partner only.
- Without SMTP credentials: messages land in a clearly labelled "Development outbox" and are never reported as sent.

## API
`/comms/templates` (CRUD, preview with sample data), `/comms/announcements` (create, schedule, send), `/comms/deliveries` (status, retry),
`/me/notifications`, `/me/preferences`, `/me/marketing-consent`, `/conversations` (list, create, messages, close).

## Screens
Template editor with live preview in both languages, announcement composer with audience picker and recipient count,
delivery log with failures, guardian inbox and conversation view (mobile), staff conversations queue.

## Audit actions
`template.changed`, `announcement.created|scheduled|sent`, `notification.queued|sent|failed`, `preference.changed`, `marketing_consent.changed`, `conversation.created|closed`.

## Sub-steps
- **A.** Templates, catalogue wiring for M01–M06 events, preferences, consent + tests.
- **B.** Announcements (scheduled), conversations, delivery log, dev outbox viewer, screens.

## Acceptance tests
- A retried business request produces one notification.
- Guardian cannot message another guardian or any student; school coordinator sees only own-partner conversations.
- Marketing announcement skips users without marketing consent; essential notifications still delivered.
