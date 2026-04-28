# ECHO v1 Build Plan

This plan follows `prd.md` and `SCHEMA.md`. If there is a conflict, `SCHEMA.md`
wins for field names, allowed values, null handling, and pipeline contracts.

## Goal

Build the v1 ECHO pipeline:

```text
commitment_ingester -> outcome_scorer -> gap_calculator -> urgency_ranker -> outbound_generator -> human_checkpoint
```

One hospital dict moves through the full pipeline. Each tool only adds fields.
No tool removes or renames fields.

v1 detects a within-state mismatch:

```text
CMS Birthing-Friendly commitment
+ hospital HCAHPS patient experience lag
+ state postpartum care strength
```

v1 uses OpenRouter for email generation. Anthropic is v2 only.
v1 uses CMS Birthing-Friendly as the only commitment source.
v1 should use local CSV files in `data/` for demo reliability. Do not build
live web scraping or rely on live API calls in the core pipeline.

## Source Of Truth

Read in this order before implementation:

1. `prd.md` - product direction and scope.
2. `SCHEMA.md` - exact field names, allowed values, and null rules.
3. `tests/fixtures.py` - shared test hospitals.
4. This file - build order and ownership.

Do not implement any field or feature that is not in `SCHEMA.md`.

## v1 Scope

In v1, hospital-level outcome data is HCAHPS only.

In v1, commitment data is CMS Birthing-Friendly only. Do not add ACOG,
collaborative, press-release, or manually researched commitment sources.

Use these v1 outcome fields:

- `hcahps_discharge_score`
- `hcahps_discharge_national_avg`
- `hcahps_care_transition_score`
- `state_postpartum_care_pct`
- `compared_to_national`

Do not use these old/v2 fields in v1:

- `severe_morbidity_rate`
- `postpartum_visit_pct`
- `well_baby_visit_pct`
- `maternal_quality_score`
- `readmission_penalty`
- `excess_readmission_ratio`
- `medicaid_pct`

Valid v1 `lead_angle` values:

- `hcahps_discharge_gap`
- `hcahps_care_transition_gap`
- `state_strength_vs_hospital_lag`

Valid v1 `generation_method` values:

- `openrouter_api`
- `cached_fallback`

## Ownership

| Owner | Files | Responsibility |
|---|---|---|
| Jonel | `src/commitment_ingester.py`, `src/outcome_scorer.py`, `tests/test_commitment_ingester.py`, `tests/test_outcome_scorer.py` | Data layer |
| Luba | `src/gap_calculator.py`, `src/urgency_ranker.py`, `tests/test_gap_calculator.py`, `tests/test_urgency_ranker.py` | Scoring and ranking |
| Paula | `src/outbound_generator.py`, `src/human_checkpoint.py`, `tests/test_outbound_generator.py`, `tests/test_human_checkpoint.py`, `data/email_cache.json` | Email generation and human review |
| Team | `src/agent.py`, `tests/test_pipeline.py` | End-to-end integration |

Do not edit another owner's files without flagging the reason.

## Build Order

### Task 0 - Shared Fixtures

Owner: Luba

Status: shipped, but verify before implementation.

Acceptance criteria:

- `tests/fixtures.py` uses only fields from `SCHEMA.md`.
- Fixtures cover high, medium, low, null-data, and no-commitment cases.
- No test file defines its own hospital fixtures.

### Task 1 - Commitment Ingester Tests

Owner: Jonel

Create `tests/test_commitment_ingester.py`.

Test requirements:

- `get_hospital_commitments()` returns a non-empty list.
- Every hospital has all Tool 1 schema fields.
- `facility_id` is a string.
- `state` is two-letter uppercase.
- `birthing_friendly` is boolean.
- v1 returned hospitals have `has_commitment is True`.
- `commitment_tag` is a specific sentence or `None`, never an empty string or category label.

Run:

```bash
.venv/bin/python -m pytest tests/test_commitment_ingester.py -v
```

Expected before implementation: import failure or failing tests.

### Task 2 - Commitment Ingester Implementation

Owner: Jonel

Create `src/commitment_ingester.py`.

Data inputs:

- `data/Hospital_General_Information.csv`

Acceptance criteria:

- Returns Tool 1 fields exactly as defined in `SCHEMA.md`.
- Uses `facility_id` as the join key.
- Keeps `state` uppercase.
- Filters to CMS Birthing-Friendly hospitals for the v1 territory.
- Sets `commitment_source` to `CMS`.
- Does not skip hospitals because of partial CMS data.
- Missing values are `None`, not `0`.

Run:

```bash
.venv/bin/python -m pytest tests/test_commitment_ingester.py -v
```

### Task 3 - Outcome Scorer Tests

Owner: Jonel

Create `tests/test_outcome_scorer.py`.

Test requirements:

- `score_outcomes(hospitals)` does not drop hospitals.
- Adds only the v1 outcome fields from `SCHEMA.md`.
- `compared_to_national` is exactly `Better`, `Same`, or `Worse`.
- If `hcahps_discharge_score` is present, `hcahps_discharge_national_avg` is present.
- Missing HCAHPS fields are `None`, not `0`.
- HCAHPS scores have the expected numeric types when present.

Run:

```bash
.venv/bin/python -m pytest tests/test_outcome_scorer.py -v
```

Expected before implementation: import failure or failing tests.

### Task 4 - Outcome Scorer Implementation

Owner: Jonel

Create `src/outcome_scorer.py`.

Data inputs:

- `data/HCAHPS-Hospital.csv`
- `data/Adult_Core_Set_PPC-AD.csv`

Acceptance criteria:

- Adds `hcahps_discharge_score`.
- Adds `hcahps_discharge_national_avg`.
- Adds `hcahps_care_transition_score`.
- Adds `state_postpartum_care_pct`.
- Adds `compared_to_national`.
- Does not add old/v2 hospital-level fields.
- Documents the exact HCAHPS measure IDs used after the real CSV is inspected.

Run:

```bash
.venv/bin/python -m pytest tests/test_outcome_scorer.py -v
```

Signal Luba when Tasks 1-4 pass.

### Task 5 - Gap Calculator Tests

Owner: Luba

Create `tests/test_gap_calculator.py`.

Test requirements:

- `calculate_gap_score(hospital)` returns the same dict with added Tool 3 fields.
- Intermediate `gap_score` is a float from 0 to 75.
- `lead_angle` is one of the three v1 values.
- `gap_breakdown` contains `commitment_strength`, `outcome_gap`, and `urgency_context`.
- `urgency_context` is `0` after Tool 3.
- High-gap fixture scores above low-gap fixture.
- `data_confidence` is `low` only when both HCAHPS fields are `None`.
- `has_commitment=False` raises `ValueError`.
- Null HCAHPS data does not crash.

Run:

```bash
.venv/bin/python -m pytest tests/test_gap_calculator.py -v
```

Expected before implementation: import failure or failing tests.

### Task 6 - Gap Calculator Implementation

Owner: Luba

Create `src/gap_calculator.py`.

Acceptance criteria:

- Uses only HCAHPS/state postpartum v1 fields.
- Does not reference dropped fields like `postpartum_visit_pct` or `severe_morbidity_rate`.
- Uses `hospital.get("field") is not None` before calculations that may receive nulls.
- Sets `data_confidence` exactly as defined in `SCHEMA.md`.
- Produces one of the three valid v1 `lead_angle` values.

Run:

```bash
.venv/bin/python -m pytest tests/test_gap_calculator.py -v
```

### Task 7 - Urgency Ranker Tests

Owner: Luba

Create `tests/test_urgency_ranker.py`.

Test requirements:

- `add_urgency(hospital)` requires Tool 3 fields.
- Final `gap_score` is a float from 0 to 100.
- `urgency_tier` is exactly `high`, `medium`, or `low`.
- `urgency_flag` is exactly one of the three schema strings.
- `gap_breakdown["urgency_context"]` is filled in and is between 0 and 25.
- Missing `gap_score` or `gap_breakdown` raises `KeyError`.

Run:

```bash
.venv/bin/python -m pytest tests/test_urgency_ranker.py -v
```

Expected before implementation: import failure or failing tests.

### Task 8 - Urgency Ranker Implementation

Owner: Luba

Create `src/urgency_ranker.py`.

Data inputs:

- `data/kff_state_data.csv`
- `data/nchs_mortality_export.csv`

Acceptance criteria:

- Adds state mortality, Medicaid extension, and racial disparity context.
- Updates intermediate Tool 3 `gap_score` to final Tool 4 `gap_score`.
- Sets `urgency_tier` and `urgency_flag` exactly per schema.
- Does not rank hospitals against each other inside this function.

Run:

```bash
.venv/bin/python -m pytest tests/test_urgency_ranker.py -v
```

Signal Paula when Tasks 5-8 pass.

### Task 9 - Outbound Generator Tests

Owner: Paula

Create `tests/test_outbound_generator.py`.

Test requirements:

- Low urgency hospitals do not get emails.
- High and medium urgency hospitals get emails.
- Email object has all Tool 5 schema fields.
- Each email has `body_moral`, `body_clinical`, and `body_financial`.
- `generation_method` is exactly `openrouter_api` or `cached_fallback`.
- Fallback triggers when required grounding fields are null.
- Fallback triggers when the OpenRouter call fails.
- No body contains hardcoded vendor names.
- Bodies include `[COMPANY_NAME]` and `[SOCIAL_PROOF]` placeholders.
- `urgency_tier` is copied from the hospital dict.

Run:

```bash
.venv/bin/python -m pytest tests/test_outbound_generator.py -v
```

Expected before implementation: import failure or failing tests.

### Task 10 - Outbound Generator Implementation

Owner: Paula

Create:

- `src/outbound_generator.py`
- `data/email_cache.json`

Acceptance criteria:

- Requires input hospitals to have `urgency_tier`.
- Uses OpenRouter in v1.
- Sets `generation_method` truthfully.
- Falls back to cached templates on API failure or missing required grounding fields.
- Generates three grounded variants per included hospital.
- Does not send email.

Run:

```bash
.venv/bin/python -m pytest tests/test_outbound_generator.py -v
```

### Task 11 - Human Checkpoint Tests

Owner: Paula

Create `tests/test_human_checkpoint.py`.

Test requirements:

- `display_checkpoint(hospitals, emails)` returns a summary string.
- Summary includes high and medium counts.
- Summary clearly says nothing was sent.
- Display includes all three email variants.
- Display includes hospital name, state, urgency flag, final gap score, commitment tag, and lead angle.

Run:

```bash
.venv/bin/python -m pytest tests/test_human_checkpoint.py -v
```

Expected before implementation: import failure or failing tests.

### Task 12 - Human Checkpoint Implementation

Owner: Paula

Create `src/human_checkpoint.py`.

Acceptance criteria:

- Presents a readable terminal checkpoint.
- Shows all high/medium email drafts.
- Clearly communicates that ECHO drafts only; a human sends.

Run:

```bash
.venv/bin/python -m pytest tests/test_human_checkpoint.py -v
```

### Task 13 - Pipeline Integration Tests

Owner: Team

Create `tests/test_pipeline.py`.

Test requirements:

- Full pipeline runs on `tests/fixtures.py`.
- Dict fields only grow after each tool.
- Tool 3 `gap_score` is <= 75.
- Tool 4 `gap_score` is <= 100.
- Emails are created only for high/medium hospitals.
- Null-data hospital is retained and flagged with low confidence.

Run:

```bash
.venv/bin/python -m pytest tests/test_pipeline.py -v
```

### Task 14 - Agent Integration

Owner: Team

Refactor `src/agent.py` so it orchestrates the separate modules instead of
embedding tool implementations.

Acceptance criteria:

- Runs the tools in the required order.
- Accepts a state argument, with NY as the demo target.
- Produces a ranked top list.
- Displays the human checkpoint.
- Does not send email.

Run:

```bash
.venv/bin/python src/agent.py NY
```

## Final Done Criteria

```bash
.venv/bin/python -m pytest tests/ -v
.venv/bin/python src/agent.py NY
```

Expected final behavior:

- All tests pass.
- The NY run uses real NY hospitals.
- High/medium accounts get three email variants.
- Email generation uses OpenRouter or cached fallback.
- Human checkpoint is displayed.
- Nothing is sent automatically.
