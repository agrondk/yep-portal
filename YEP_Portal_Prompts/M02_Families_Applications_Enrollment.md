# M02 — Households, children, applications, offers, waiting list, enrollment, consent

**Depends on:** M00, M01. **Attach with:** `01_MASTER_CONTEXT.md`, `PROGRESS.md`.

## Goal
The complete family journey, backed by the database:
Discover → Apply → Review → Offer → Accept → Satisfy requirements → Enrolled.
Staff manage admissions with safe seat allocation and waiting lists.

## Scope
**In:** households, guardians, children, household linking, applications (draft → decision), offers, seat reservation
and expiry, waiting lists, enrollments and their requirements, consent versions and acceptances, staff-assisted
applications, renewal/progression invitations.
**Out:** bulk institutional enrollment (M05), invoices (M06 — but expose a hook), sessions/attendance (M03/M04).

## Data model (`apps/api/app/modules/admissions/models.py`)
- `household` (name, primary_contact_user_id, address, phone)
- `guardian` (user_id, household_id, relationship, is_billing_contact, is_emergency_contact)
- `household_invitation` (household_id, email, token_hash, expires_at, accepted_at, granted_by) — explicit link only
- `child` (household_id, first_name, last_name, date_of_birth, school_name nullable, grade nullable, support_needs_note (restricted), emergency_contact, photo_consent_status derived, is_demo)
- `application` (child_id, offering_id, preferred_schedule, source: guardian | staff_assisted | institutional, utm fields + promo_code nullable (for M19 attribution), submitted_by, status, eligibility_result jsonb, override_reason nullable)
  - partial unique: one active application per (child_id, offering_id)
- `application_info_request` (application_id, message, requested_by, responded_at, response)
- `offer` (application_id, offered_by, expires_at, reserves_seat bool, status: open | accepted | declined | expired | withdrawn, decided_at)
- `waitlist_entry` (offering_id, application_id, priority, priority_rule, position_snapshot, status)
- `enrollment` (child_id, offering_id, offer_id unique, status, pending_reasons text[], confirmed_at, completed_at, cancelled_reason, transferred_to_enrollment_id, funding: paid | free | sponsored, sponsor_initiative_id nullable)
- `consent_document` (key: participation_terms | photo_video | data_processing, version, text_sq/en, required bool, effective_from)
- `consent_acceptance` (consent_document_id, child_id, guardian_user_id, accepted bool, accepted_at, ip) — append-only; withdrawal is a new row
- `renewal_invitation` (enrollment_id, target_offering_id, status, expires_at)

## State machines
Application: draft → submitted → under_review → info_requested ↔ under_review → offered | waitlisted | declined; any non-final → withdrawn.
Offer: open → accepted | declined | expired | withdrawn.
Enrollment: pending_requirements → confirmed → active → completed | cancelled | transferred.

## Rules
- Children never need an email address. One guardian account manages many children.
- Another guardian gains access only by accepting a `household_invitation` sent by an existing guardian or staff; matching surname/school is never enough.
- Eligibility computed from child DOB vs offering `age_min/age_max` at `age_reference_date`; result explained in UI. Staff override needs a reason + audit.
- Offer acceptance in one transaction: lock offering row, check capacity (counting active enrollments + open seat-reserving offers), mark offer accepted, create exactly one enrollment (`offer_id` unique). Repeated acceptance returns the existing enrollment.
- Offer expiry runs as a scheduled job (system actor), releases the seat, and notifies the next waitlist entry per recorded priority rule.
- Enrollment `pending_reasons` computed from configurable requirements: required consents, payment (if fee_model not free/sponsored — check via M06 hook, stubbed until M06), documents.
- Optional photo/video consent is never a condition of enrollment.
- `support_needs_note` visible only to owner_admin, operations_coordinator and the child's assigned instructors (after M03).
- Free and sponsored enrollments must not create unpaid debts.

## API
Guardian: `/me/household`, `/me/children` CRUD, `/me/household/invitations`, `/me/applications` (draft, save, submit, respond to info request), `/me/offers/:id/accept|decline`, `/me/enrollments`, `/me/consents`.
Staff: `/admissions/applications` (search, filters, saved views, transitions, notes), `/admissions/offers`, `/admissions/waitlists/:offeringId`, `/admissions/enrollments` (transfer, cancel, complete), `/admissions/assisted-applications`, `/admissions/renewals`, consent documents admin.

## Screens
Guardian (mobile-first): my family, add child, browse & apply (with eligibility explanation), application status timeline, respond to info request, offer accept/decline with expiry countdown, enrollment checklist (what's pending and why), consents.
Staff: applications table (filters, saved views, export if permitted), application detail (history, internal notes, info request, make offer, waitlist), waiting list per offering, enrollment register, assisted application wizard, consent document versions.

## Audit actions
`household.created|linked|unlinked`, `child.created|edited`, `application.*` (each transition), `eligibility.overridden`,
`offer.created|accepted|declined|expired|withdrawn`, `waitlist.added|reordered|promoted`, `enrollment.*` (each transition),
`consent.accepted|withdrawn`, `renewal.invited|accepted`.

## Sub-steps
- **A.** Schema + migration; household/guardian/child + household invitation; scope rules for household; tests (cross-household isolation).
- **B.** Applications + info requests + eligibility + state machine + tests.
- **C.** Offers, seat reservation, acceptance transaction, waiting list, expiry job + concurrency tests.
- **D.** Enrollments + requirements + consents + renewals + tests.
- **E.** Guardian and staff screens; Playwright journey: guardian adds two children, applies, gets offer, accepts, completes consent, sees enrollment.

## Acceptance tests
- Two concurrent acceptances for the last seat: exactly one succeeds.
- Double-click acceptance creates one enrollment.
- Expired offer releases capacity and promotes waitlist per rule.
- Household B cannot read Household A's children through pages, API, files, search, exports or activity feed.
- Free/sponsored enrollment reaches `confirmed` with no payment requirement.
