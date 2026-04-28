# ECHO - Early Care Handoff Observer

ECHO is a GTM intelligence agent for maternal health software companies. It
finds Birthing-Friendly hospitals whose HCAHPS patient experience lags behind
their state's postpartum care strength, then drafts grounded outreach for a
human to review and send.

```text
NY achieves 72% postpartum care completion.
This Birthing-Friendly hospital's HCAHPS discharge score is 14 points below the national average.
```

## What It Does

ECHO gives a GTM Engineer a daily prioritized account list and three outreach
variants per high/medium account.

The human stays in control:

- ECHO ranks accounts.
- ECHO explains the mismatch.
- ECHO drafts outreach.
- The GTM Engineer reviews, edits, copies, and sends.
- ECHO never sends email automatically.

## v1 Scope

v1 is intentionally narrow:

- NY demo territory.
- CMS Birthing-Friendly hospitals.
- Hospital-level HCAHPS patient experience.
- State-level postpartum care baseline.
- OpenRouter email generation with cached fallback.
- Terminal human checkpoint.

Hospital-level severe maternal morbidity, hospital postpartum visit rates,
readmissions, Medicaid payer mix, silent-gap mode, CRM integration, and
Anthropic are v2.

## Pipeline

```text
commitment_ingester
  -> outcome_scorer
  -> gap_calculator
  -> urgency_ranker
  -> outbound_generator
  -> human_checkpoint
```

One hospital dict travels through the full pipeline. Each tool only adds fields.

## Data Sources

| Source | v1 Use |
|---|---|
| CMS Hospital General Information | Hospital identity and Birthing-Friendly designation |
| CMS HCAHPS | Hospital discharge communication and care transition scores |
| CMS Medicaid Adult Core Set PPC-AD | State postpartum care completion baseline |
| NCHS maternal mortality data | State urgency context |
| KFF postpartum Medicaid tracker | State Medicaid extension context |
| OpenRouter API | Three grounded outreach variants |

## Team Ownership

| Owner | Files |
|---|---|
| Jonel | `src/commitment_ingester.py`, `src/outcome_scorer.py` |
| Luba | `src/gap_calculator.py`, `src/urgency_ranker.py` |
| Paula | `src/outbound_generator.py`, `src/human_checkpoint.py` |
| Team | `src/agent.py`, `tests/test_pipeline.py` |

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Add `OPENROUTER_API_KEY` to `.env` for live generation. Without it, the outbound
generator should use cached fallback templates.

## Run

```bash
.venv/bin/python -m pytest tests/ -v
.venv/bin/python src/agent.py NY
```

## Docs

- `prd.md` - product source of truth.
- `SCHEMA.md` - engineering contract.
- `PLAN.md` - owner split, implementation order, and test contract.
