# AGENTS.md — ECHO

Instructions for AI coding assistants working in this repo.

## Read These First

Before touching any file:

1. `prd.md` — what we are building and why.
2. `SCHEMA.md` — exact field names, types, allowed values, source files, and null rules.
3. `PLAN.md` — build order, file ownership, test requirements, done criteria.
4. `tests/fixtures.py` — shared test hospitals. Import from here; do not define your own.

## Pipeline Order — Hard Constraint

```text
commitment_ingester -> outcome_scorer -> gap_calculator -> urgency_ranker -> outbound_generator -> human_checkpoint
```

One hospital dict travels the full pipeline. Fields are only added. If a function removes or renames a field, it is wrong.

## v0.2 Core Logic

The v1 mismatch compares hospital HCAHPS patient experience against state postpartum visit strength.

Example:

```text
NY achieves 82.4% postpartum visit completion. This Birthing-Friendly hospital scores 1 star on HCAHPS discharge information.
```

## Field Rules — Non-Negotiable

- Field names are exact. `discharge_info_star` not `care_transition_score`. `state_postpartum_visit_rate` not `state_postpartum_care_pct`.
- `state` is always 2-letter uppercase.
- `urgency_tier` is exactly one of: `"high"` / `"medium"` / `"low"`.
- `urgency_flag` is exactly one of: `"🔴 Act this week"` / `"🟡 Monitor"` / `"🟢 Not ready"`.
- `lead_angle` is exactly one of: `"hcahps_discharge_gap"` / `"hcahps_care_transition_gap"` / `"state_strength_vs_hospital_lag"`.
- `generation_method` is exactly one of: `"openrouter_api"` / `"cached_fallback"`.
- `commitment_tag` v1 default is exactly `"Earned the CMS Birthing-Friendly designation"`.
- `gap_score` after `gap_calculator.py` is intermediate (0-75). Only read it after `urgency_tier` is present in the dict.

## Removed v0.1 Fields

Do not use these in v1:

- `hcahps_discharge_score`
- `hcahps_discharge_national_avg`
- `hcahps_care_transition_score`
- `state_postpartum_care_pct`
- `compared_to_national`
- `severe_morbidity_rate`
- `postpartum_visit_pct`
- `well_baby_visit_pct`
- `maternal_quality_score`
- `readmission_penalty`
- `excess_readmission_ratio`
- `medicaid_pct`

## Null Handling

- Missing fields are `None`, never `0`, never imputed.
- Never skip a hospital in Tools 1-4 for missing HCAHPS data. Score what is available and set `data_confidence`.
- `data_confidence = "low"` only when both `discharge_info_star` and `overall_star` are `None`.
- Tool 5 skips low-confidence hospitals for email generation.

## Cached Fallback Trigger

Paula's `outbound_generator.py` falls back to cached templates and sets `generation_method = "cached_fallback"` when either:

1. OpenRouter API call fails.
2. Any required grounding field is null: `discharge_info_star`, `state_postpartum_visit_rate`, or `commitment_tag`.

Otherwise `generation_method = "openrouter_api"`.

## File Ownership

| File | Owner |
|------|-------|
| `tests/fixtures.py` | Luba |
| `src/commitment_ingester.py` | Jonel |
| `src/outcome_scorer.py` | Jonel |
| `src/gap_calculator.py` | Luba |
| `src/urgency_ranker.py` | Luba |
| `src/outbound_generator.py` | Paula |
| `src/human_checkpoint.py` | Paula |

Do not modify another person's file without flagging it. If a cross-file fix is needed, note it in the commit message and tell the owner.

## v1 Scope — Do Not Build

- No live web scraping.
- No CRM integration.
- No sending email.
- No patient-facing features.
- No silent gap mode.
- No hospital-level severe morbidity, readmissions, maternal quality scores, or Medicaid payer mix.
- No per-hospital curated commitment tags.
- No Anthropic API in v1.

If a feature is not in `PLAN.md`, do not build it.

## TDD Workflow

Tests are written before implementation. For every task:

1. Write the failing test.
2. Run it and confirm it fails.
3. Write minimal implementation.
4. Run again and confirm it passes.
5. Commit.

Never commit an implementation without a passing test. Never skip the failing-test step.

## Running Tests

```bash
.venv/bin/python -m pytest tests/test_gap_calculator.py -v
.venv/bin/python -m pytest tests/ -v
.venv/bin/python src/agent.py NY
```

## Done Criteria

```text
.venv/bin/python -m pytest tests/ -v       -> all green, 0 failures
.venv/bin/python src/agent.py NY           -> real NY hospitals, 3 OpenRouter/cached email variants per high/medium high-confidence account, human checkpoint displayed
```
