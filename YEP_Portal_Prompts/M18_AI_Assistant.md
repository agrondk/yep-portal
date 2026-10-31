# M18 — AI assistant (drafting, comment analysis, "ask your data", translation)

**Depends on:** M04, M05, M10, M12, M16. **Attach with:** `01_MASTER_CONTEXT.md`, `PROGRESS.md`.
**When:** Release 4 (drafting and translation can start earlier, right after M05/M10).

## Goal
Save staff time with a large language model (LLM) while keeping people in control:
1. **Drafting** — school proposals, monthly cohort reports, franchise report narrative, parent messages and announcements, in Albanian or English.
2. **Comment analysis** — tag and summarise survey comments (M16) by theme and sentiment.
3. **Ask your data** — staff type a question ("how many children attended Bricks Challenge in October?") and get an answer from the official metrics.
4. **Translation helper** — Albanian ↔ English for templates, program descriptions and messages.

Every AI output is a **draft or suggestion**. Nothing is sent, published or decided without a person approving it.

## Architecture (inside the Python back end)
```
apps/api/app/ai/
  providers/     LLMProvider Protocol; AnthropicProvider (default, model name from settings); TestProvider (deterministic, for tests/dev)
  privacy.py     pseudonymisation: replace child/guardian names and identifiers with placeholders before sending; restore after
  prompts/       versioned prompt templates per feature (Jinja2), with YEP facts from master §1
  tools.py       function-calling tools for "ask your data" that call existing scoped report services
  service.py     feature orchestration, budget checks, logging
```
API key and model name in environment/secret config; no key → AI features hidden and labelled "not configured".

## Data model (`apps/api/app/modules/ai/models.py`)
- `ai_setting` (feature, enabled, model_name, max_tokens, monthly_budget_eur, allowed_roles)
- `ai_request_log` (feature, user_id, model_name, input_tokens, output_tokens, cost_estimate, latency_ms, outcome: ok | refused | error | budget_exceeded, prompt_version, created_at) — **no prompt or response content**
- `ai_draft` (feature, entity_type, entity_id, locale, content, status: draft | accepted | edited_and_accepted | discarded, created_by, reviewed_by, reviewed_at)
- `ai_usage_month` (month, feature, tokens, cost_estimate) — for budget cap and dashboard

## Features

**1. Drafting**
- Proposal sections (M05): intro letter, program description, terms — using the proposal's structured data (groups, prices, schedule) and the maintained "about us / references" list. The AI must not invent prices, partners, results or accreditations; numbers come from the data, not the model.
- Monthly cohort report narrative (M04): from session deliveries (models built, principles taught) and attendance figures.
- Parent messages and announcements (M10): from staff bullet points; tone options (formal / friendly).
- Franchise report narrative (M11) from the frozen snapshot.
- Output saved as `ai_draft`, shown with an "AI draft — review before sending" label; staff edit and accept into the real record.

**2. Comment analysis (M16)**
- For each comment: topic tags and sentiment (writes `comment_tag` with `tagged_by = ai`, editable by staff); monthly theme summary per program/school.
- Comments are treated strictly as data: instructions inside comments are ignored (prompt-injection protection).
- Respect M16 anonymity and minimum group size for summaries.

**3. Ask your data**
- The LLM may only choose from the official metric catalogue (M12 `metric_definition`) and allowed filters via tool calls; the back end executes them through the **same scoped report services**, as the asking user.
- **No free-form SQL**, no access beyond the user's role and scope.
- Answer shows the number(s), period, definition, and a link to the dashboard view. If the question can't be answered from the catalogue, say so.
- Available to owner_admin, operations_coordinator, finance_officer (finance metrics only for finance roles).

**Marketing campaigns (M19)** — campaign drafts (audience, message, channels, sq/en posts, email, flyer, KPI estimates) from aggregated,
non-personal context only; same no-invention and approval rules. Implemented in M19 step E using this module's provider, privacy and logging.

**4. Translation helper**
- Button on bilingual fields (templates, program texts, FAQ): fills the other language as a draft for review.

## Rules
- Privacy: send the minimum data. Never send dates of birth, support-needs notes, addresses, phone numbers, emails, payment details or private staff notes. Names are pseudonymised (e.g. "Child A") and restored locally. Choose an LLM provider with a data-processing agreement and no training on submitted data; record the choice in `PROGRESS.md`.
- Per-feature on/off switches and role access in `ai_setting`; monthly budget cap stops calls with a clear message.
- Log usage metadata only (tokens, cost, outcome) — never prompt or response text in logs or audit.
- AI never sends messages, issues documents, changes records or makes decisions about children, admissions, prices or payments.
- Albanian output must use correct characters (ë, ç); staff can regenerate or edit.
- When AI is disabled or unavailable, every workflow still works manually.

## API
`POST /ai/drafts` (feature, entity, locale, options) → draft · `POST /ai/drafts/:id/accept|discard` ·
`POST /ai/comments/analyze?campaign=` · `GET /ai/comments/summary?program&month` ·
`POST /ai/ask` (question) → answer + metrics used + links · `POST /ai/translate` · admin: `/ai/settings`, `/ai/usage`.

## Screens
"Draft with AI" buttons inside the proposal builder, monthly report generator, announcement composer and franchise report;
review panel showing draft vs final; "Ask your data" box on the owner summary page; comment themes panel on survey results;
AI settings and monthly usage/cost page for admins.

## Audit actions
`ai.draft_created|accepted|discarded`, `ai.comments_analyzed`, `ai.question_asked` (metric keys only, not the text), `ai.translation_created`,
`ai.setting_changed`, `ai.budget_exceeded`.

## Sub-steps
- **A.** Provider adapter (Anthropic + Test), settings, budget cap, usage logging, pseudonymisation + tests.
- **B.** Drafting for proposals and parent messages/announcements, draft review flow.
- **C.** Monthly report and franchise narrative drafting; translation helper.
- **D.** Survey comment tagging and theme summaries (with injection-safe prompts).
- **E.** Ask-your-data with tool calls over the metric catalogue and scope enforcement + tests.

## Acceptance tests
- With no API key, AI buttons are hidden and all workflows work manually.
- The payload captured by `TestProvider` contains no child names, dates of birth, support notes, phone numbers or emails.
- A proposal draft's prices and totals equal the proposal data exactly (the model cannot change numbers).
- "Ask your data" for a metric outside the user's scope (e.g. operations user asking for finance totals) is refused.
- A comment containing "ignore previous instructions…" is tagged as data, not obeyed.
- Reaching the monthly budget stops further calls and shows a clear message.
- Nothing is sent to parents or schools until a person accepts the draft.
