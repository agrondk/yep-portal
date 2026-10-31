# M17 — Machine learning predictions (dropout risk, demand forecast, late-payment risk)

**Depends on:** M02, M03, M04, M06, M12 (and M16 for satisfaction features). **Attach with:** `01_MASTER_CONTEXT.md`, `PROGRESS.md`.
**When:** Release 4 — only after the portal holds real history (target: at least 2 full terms of attendance and billing).

## Goal
Give staff early warnings and planning numbers from YEP's own data:
1. **Dropout risk** — which enrolled children are likely not to continue or renew, and why.
2. **Demand forecast** — how many children per program, location and term to expect, to plan groups, rooms, kits and instructors.
3. **Late-payment risk** — which open invoices are likely to become overdue.

Predictions are **advisory**: they create suggestions for staff, never automatic actions or decisions about a child or family.

## Architecture (inside the Python back end)
```
apps/api/app/ml/
  features/        SQL → pandas feature builders per use case (point-in-time correct, no future data leakage)
  models/          training + prediction code per use case (scikit-learn / statsmodels)
  registry.py      save/load models (joblib) to object storage, version and promote
  readiness.py     data-sufficiency checks per use case
  tasks.py         Celery tasks: monthly training, weekly/daily scoring (registered in app/jobs/registry.py)
  explain.py       top factors in plain language
```
No separate ML server is needed; training and scoring run as Celery tasks on the worker.

**Consumers:** M12 dashboards and **M19 marketing triggers** (`below_forecast`, `renewal_risk`) read active predictions; M17 itself never starts campaigns.

## Data model (`apps/api/app/modules/ml/models.py`)
- `ml_model` (use_case: dropout | demand | late_payment, version, algorithm, trained_at, training_window_from/to, feature_list jsonb, metrics jsonb, baseline_metrics jsonb, artifact_file_id, status: candidate | active | retired, promoted_by)
- `ml_prediction` (model_id, entity_type: enrollment | offering_program_term | financial_document, entity_id, score (0–1) or value + interval_low/high, band: low | medium | high, top_factors jsonb, predicted_at, valid_until)
- `ml_outcome` (prediction_id, actual_outcome, observed_at) — to measure real accuracy later
- `ml_action` (prediction_id, action: contacted | dismissed | follow_up_created, by, at, note) — what staff did
- `ml_setting` (use_case, enabled, thresholds, min_data_requirements)

## Use cases

**1. Dropout / non-renewal risk (per active enrollment)**
- Features (behavioural only): attendance rate and trend (last 4 sessions vs before), consecutive absences, late arrivals, months enrolled,
  number of previous enrollments, program, location/partner type, schedule changes experienced, invoice overdue days, survey score if identified, sibling enrolled.
- **Excluded features:** names, address, support-needs notes, consents, any protected characteristic. Document exclusions in the model card.
- Model: logistic regression baseline + `HistGradientBoostingClassifier`, probability calibration; evaluate on a time-based holdout.
- Output: risk band + top 3 reasons in plain Albanian/English (e.g. "attendance dropped from 90% to 50% in the last month").
- Before enough data: rule-based fallback flags (e.g. 2+ consecutive absences, attendance down > 30 points) clearly labelled "rule, not model".

**2. Demand forecast (per program × location × term)**
- Inputs: historical enrollments by term, inquiries and trial requests in the pre-term window, waiting lists, school agreements in pipeline (M05), seasonality.
- Model: statsmodels exponential smoothing / simple regression with prediction intervals; compare with naive "same as last year" baseline.
- Output: expected children with low–high range, suggested number of groups (using configured group size), rooms, kits and instructor sessions needed.

**3. Late-payment risk (per open customer invoice)**
- Features: party's payment history (average days late, share paid on time), invoice amount vs usual, installment number, fee model, days to due date.
- Model: logistic regression (interpretable).
- Output: watch list for finance with reasons; suggested reminder timing (reminders still sent only via M10 rules or by staff).

## Rules
- Readiness gate per use case (configurable minimums, e.g. ≥ 300 completed enrollments with known outcome for dropout). If not met: show "not enough data yet" and use the labelled rule-based fallback.
- A new model version is promoted only if it beats the baseline on the holdout; metrics and baseline stored and shown in a model card page.
- Monthly retraining job, daily/weekly scoring job; each run writes `job_run` and is idempotent.
- Visibility: dropout risk → owner_admin, operations_coordinator, and instructors for their own cohorts (band + reasons only); late-payment risk → finance_officer, owner_admin; forecasts → owner_admin, operations_coordinator. **Never shown to guardians, schools or sponsors.**
- Predictions are personal data: retention policy applies; mention in the privacy notice (M15).
- Track outcomes and staff actions so real-world accuracy is reported, not assumed.

## API
`GET /ml/dropout-risk?cohort&band` · `GET /ml/demand-forecast?program&location&term` · `GET /ml/late-payment-risk` ·
`POST /ml/predictions/:id/actions` · admin: `/ml/models` (list, metrics, promote, retire), `POST /ml/train/:use_case`, `/ml/settings`.

## Screens
- **At-risk learners** list (filters by cohort/program, band, reasons, "mark contacted / create follow-up").
- **Forecast** page: chart per program with range band, suggested groups/instructors/kits for next term.
- **Payment watch list** for finance.
- **Model cards** (admin): use case, data window, features used and excluded, accuracy vs baseline, last training, status.
- Dashboard cards in M12: "Children at high risk", "Next-term forecast", "Invoices at risk".

## Audit actions
`ml.model_trained|promoted|retired`, `ml.scoring_run`, `ml.prediction_actioned`, `ml.setting_changed`, `ml.export`.

## Sub-steps
- **A.** ML framework: feature builders (point-in-time), registry, readiness gate, Celery tasks, settings, synthetic training data generator for tests.
- **B.** Dropout risk: rule fallback, model, explanations, at-risk screen + tests.
- **C.** Demand forecast with intervals and planning suggestions + screen.
- **D.** Late-payment risk + finance watch list.
- **E.** Model cards, outcome tracking, M12 dashboard cards, scope tests.

## Acceptance tests
- With insufficient data, the UI shows "not enough data yet" and only labelled rule-based flags.
- Feature builders never use data dated after the prediction date (leakage test).
- Excluded fields (names, support needs, consents) are absent from training data (test inspects feature columns).
- A guardian, school coordinator or sponsor cannot call any `/ml` endpoint; instructors see only their cohorts.
- A candidate model worse than baseline cannot be promoted.
