# AGENTS.md — ECHO

Instructions for AI coding assistants working in this repo.

## Read These First

Before touching any file:
1. `prd.md` — what we're building and why.
2. `SCHEMA.md` — field names, types, exact string values, null rules. Every function must match it exactly.
3. `PLAN.md` — build order, file ownership, test requirements, done criteria.
4. `tests/fixtures.py` — shared test hospitals. Import from here; do not define your own.

## Pipeline Order — Hard Constraint

```
commitment_ingester → outcome_scorer → gap_calculator → urgency_ranker → outbound_generator → human_checkpoint
```

One hospital dict travels the full pipeline. Fields are only **added** — never removed, never renamed. If a function removes or renames a field, it is wrong.

## Within-State Mismatch — Core Logic

The v1 mismatch compares **hospital HCAHPS patient experience** against **state postpartum care strength**. State aggregate is the expectation; hospital lagging behind it is the signal.

> "NY achieves 72% postpartum care completion. This Birthing-Friendly hospital's HCAHPS discharge score is 14 points below national average."

## Field Rules — Non-Negotiable

- Field names are exact. `facility_name` not `hospital_name`. `hcahps_discharge_score` not `hcahps_score`. Copy from SCHEMA.md, do not type from memory.
- `state` is always 2-letter uppercase. `"NY"` not `"New York"` not `"ny"`.
- `compared_to_national` is exactly one of: `"Better"` / `"Same"` / `"Worse"`. Capital first letter.
- `urgency_tier` is exactly one of: `"high"` / `"medium"` / `"low"`. Lowercase.
- `urgency_flag` is exactly one of: `"🔴 Act this week"` / `"🟡 Monitor"` / `"🟢 Not ready"`.
- `lead_angle` is exactly one of (v1):
  - `"hcahps_discharge_gap"`
  - `"hcahps_care_transition_gap"`
  - `"state_strength_vs_hospital_lag"`
  - v2 adds `"silent_gap"`
- `generation_method` is exactly one of: `"openrouter_api"` / `"cached_fallback"`.
- `commitment_tag` is a specific quotable sentence or `None`. Never `""`. Never a category label.
- `gap_score` after `gap_calculator.py` is **intermediate** (0–75). Only read it after `urgency_tier` is present in the dict.

## Null Handling

- Missing fields are `None` — never `0`, never imputed.
- Never skip a hospital for missing data — score what is available, set `data_confidence` accordingly.
- Use `hospital.get("field_name") is not None` before every calculation that could receive `None`.
- `data_confidence = "low"` only when both `hcahps_discharge_score` **and** `hcahps_care_transition_score` are `None`.

## Cached Fallback Trigger (Paula's Tool 5)

Paula's `outbound_generator.py` falls back to pre-generated static templates and sets `generation_method = "cached_fallback"` when **either**:

1. OpenRouter API call fails (timeout, non-200, empty/malformed output).
2. Any required grounding field is null: `hcahps_discharge_score`, `state_postpartum_care_pct`, or `commitment_tag`.

Otherwise `generation_method = "openrouter_api"`.

## File Ownership

| File | Owner |
|------|-------|
| `src/commitment_ingester.py` | Jonel |
| `src/outcome_scorer.py` | Jonel |
| `src/gap_calculator.py` | Luba |
| `src/urgency_ranker.py` | Luba |
| `src/outbound_generator.py` | Paula |
| `src/human_checkpoint.py` | Paula |

Do not modify another person's file without flagging it. If a cross-file fix is needed, note it in the commit message and tell the owner.

## v1 Scope — Do Not Build

- No live web scraping
- No CRM integration
- No sending email — ECHO drafts, the human sends
- No patient-facing features
- No silent gap mode (`has_commitment=False`) — v2 only
- No ranking the top 10 against each other
- No hospital-level outcome data beyond HCAHPS (severe maternal morbidity per hospital, hospital postpartum visit %, hospital readmissions, hospital Medicaid payer mix are v2)
- No Anthropic API in v1 — use OpenRouter free tier (v2 swaps to Anthropic)

If a feature is not in `PLAN.md`, do not build it.

## TDD Workflow

Tests are written before implementation. For every task:
1. Write the failing test
2. Run it — confirm it fails
3. Write minimal implementation to make it pass
4. Run again — confirm it passes
5. Commit

Never commit an implementation without a passing test. Never skip the failing-test step.

## Running Tests

```bash
# Single file
.venv/bin/python -m pytest tests/test_gap_calculator.py -v

# Full suite
.venv/bin/python -m pytest tests/ -v

# Run agent
.venv/bin/python src/agent.py NY
```

## Done Criteria

```
.venv/bin/python -m pytest tests/ -v       → all green, 0 failures
.venv/bin/python src/agent.py NY           → real NY hospitals, 3 OpenRouter-generated email variants per high/medium account, human checkpoint displayed
```
