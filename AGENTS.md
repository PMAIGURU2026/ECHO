# AGENTS.md — ECHO

Instructions for AI coding assistants working in this repo.

## Read These First

Before touching any file:
1. `SCHEMA.md` — field names, types, exact string values, null rules. Every function must match it exactly.
2. `TDD.md` — what each tool does, test cases, done criteria.
3. `PLAN.md` — build order, file ownership, complete implementation per task.
4. `tests/fixtures.py` — shared test hospitals. Import from here; do not define your own.

## Pipeline Order — Hard Constraint

```
commitment_ingester → outcome_scorer → gap_calculator → urgency_ranker → outbound_generator → human_checkpoint
```

One hospital dict travels the full pipeline. Fields are only **added** — never removed, never renamed. If a function removes or renames a field, it is wrong.

## Field Rules — Non-Negotiable

- Field names are exact. `facility_name` not `hospital_name`. `postpartum_visit_pct` not `postpartum_pct`. Copy from SCHEMA.md, do not type from memory.
- `state` is always 2-letter uppercase. `"NY"` not `"New York"` not `"ny"`.
- `compared_to_national` is exactly one of: `"Better"` / `"Same"` / `"Worse"`. Capital first letter. No other values.
- `urgency_tier` is exactly one of: `"high"` / `"medium"` / `"low"`. Lowercase. Paula's email template branches on this.
- `urgency_flag` is exactly one of: `"🔴 Act this week"` / `"🟡 Monitor"` / `"🟢 Not ready"`.
- `lead_angle` is exactly one of: `"baby_vs_mother_contrast"` / `"severe_morbidity_rate"` / `"postpartum_visit_gap"` / `"care_transition_gap"` / `"readmission_penalty"`.
- `commitment_tag` is a specific quotable sentence or `None`. Never `""`. Never a category label like `"has commitment"`.
- `gap_score` after `gap_calculator.py` is **intermediate** (0–75). Only read `gap_score` after `urgency_tier` is present in the dict.

## Null Handling

- Missing fields are `None` — never `0`, never imputed.
- Never skip a hospital for missing data — score what is available, set `data_confidence` accordingly.
- Use `hospital.get("field_name") is not None` before every calculation that could receive `None`.
- `data_confidence = "low"` only when both `postpartum_visit_pct` **and** `severe_morbidity_rate` are `None`.

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
- No hospital-level outcome data — v1 uses state-level aggregates

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
.venv/bin/python src/agent.py NY           → real NY hospitals, real email drafts, human checkpoint displayed
```
