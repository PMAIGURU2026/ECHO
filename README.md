# ECHO — Early Care Handoff Observer

> *"Your well-baby visit rate is 94%. Your postpartum maternal visit rate is 61%. The system works. For babies."*

**ECHO** is a GTM intelligence agent for maternal health software companies. It scans public hospital data, finds hospitals where postpartum care commitments don't match actual outcomes, and hands a GTM engineer 10 prioritized accounts with a personalized outbound email — already written.

Turns 90 minutes of manual research into a 10-minute review.

---

## The Problem

GTM engineers at maternal health software companies have no systematic way to find which hospitals' public commitments to maternal care are contradicted by their actual postpartum outcome data.

The result: territory lists built on gut instinct. Generic outbound that doesn't convert. And the highest-priority accounts — the ones with the biggest gap between what they promised and what their data shows — stay invisible.

## The Thesis

Hospitals measure maternal success at delivery.

We built an agent that measures what happens after — and finds the organizations whose commitments don't survive discharge.

---

## How It Works

ECHO runs a 6-step pipeline. One hospital dict travels through the entire chain. Each tool adds fields. Nothing is ever removed.

```
get_hospital_commitments  →  Tool 1  (Jonel)   Load CMS birthing-friendly + commitment data
score_outcomes            →  Tool 2  (Jonel)   Add postpartum outcomes from CMS datasets
calculate_gap_score       →  Tool 3  (Luba)    Score the gap between commitment and outcomes (0–75)
add_urgency               →  Tool 4  (Luba)    Layer in state mortality + disparity context (0–100)
generate_outbound_email   →  Tool 5  (Paula)   Draft a personalized email per account
display_checkpoint        →  Tool 6  (Paula)   Human reviews everything. Nothing is sent automatically.
```

### The Gap Score

Three layers. One number per hospital.

| Layer | What it measures | Max pts |
|-------|-----------------|---------|
| Commitment Strength | Birthing-friendly designation, MMSM participation | 25 |
| Outcome Gap | SMM rate vs national, postpartum visit gap vs state avg, HCAHPS care transition, readmission penalty | 50 |
| Urgency Context | State maternal mortality rank, racial disparity flag, Medicaid coverage | 25 |

**70+ = 🔴 Act this week. 40–69 = 🟡 Monitor. Below 40 = 🟢 Not ready.**

### The Lead Angle

Every email leads with the sharpest contrast. ECHO picks one of five angles per account:

- `baby_vs_mother_contrast` — well-baby vs postpartum visit rate gap > 30 points
- `severe_morbidity_rate` — worse than national SMM benchmark
- `postpartum_visit_gap` — >15 points below state average
- `care_transition_gap` — HCAHPS care transition score below 3
- `readmission_penalty` — actively penalized by CMS for readmissions

---

## Quickstart

```bash
git clone https://github.com/PMAIGURU2026/ECHO.git
cd ECHO
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your OPENROUTER_API_KEY
python src/agent.py
```

Run for a specific state:
```bash
python src/agent.py GA
```

---

## Data Sources

All free. No login required.

| Source | What ECHO uses it for |
|--------|----------------------|
| [CMS Hospital General Information](https://data.cms.gov/provider-data/dataset/xubh-q36u) | Birthing-friendly designation, hospital identity |
| [CMS Maternal Health — Hospital](https://data.cms.gov/provider-data) | Maternal quality scores, SMM rate, postpartum visit %, well-baby visit % |
| [CMS Hospital Readmissions Reduction Program FY2025](https://data.cms.gov/provider-data) | Readmission penalty flag, excess readmission ratio |
| [CMS HCAHPS](https://data.cms.gov/provider-data) | Care transition score |
| [CDC WONDER](https://wonder.cdc.gov) | State maternal mortality rate by race |
| [KFF State Health Facts](https://kff.org) | 12-month Medicaid postpartum coverage by state |

---

## Who Buys This

Companies selling maternal health software to hospitals:

**Babyscripts · Maven Clinic · Wildflower Health · Mahmee · Bloomlife · Cocoon**

Pricing hypothesis: **$500–$2,000/month per seat.**

---

## Repo Structure

```
ECHO/
├── src/
│   ├── agent.py                  # Pipeline orchestrator (Strands + OpenRouter)
│   ├── commitment_ingester.py    # Tool 1 — Jonel
│   ├── outcome_scorer.py         # Tool 2 — Jonel
│   ├── gap_calculator.py         # Tool 3 — Luba
│   ├── urgency_ranker.py         # Tool 4 — Luba
│   ├── outbound_generator.py     # Tool 5 — Paula
│   └── human_checkpoint.py       # Tool 6 — Paula
├── tests/
│   └── test_gap.py               # TDD tests for gap + urgency logic
├── data/                         # CMS CSVs + state data (gitignored)
├── SCHEMA.md                     # Shared data contract — source of truth for the team
├── PRODUCT_VISION.md             # Vision, market, pricing, moat
├── requirements.txt
└── .env.example
```

---

## Team

**Team Female — Pursuit AI-Native Cycle 3**

| Person | Owns |
|--------|------|
| Jonel | commitment_ingester.py · outcome_scorer.py (Data Layer) |
| Luba | gap_calculator.py · urgency_ranker.py (Brain + Scoring) |
| Paula | outbound_generator.py · human_checkpoint.py (Voice + Output) |

Pipeline runs in that order. Jonel first. Then Luba. Then Paula. Then human.

---

## The Moat

The agent is replicable. The dataset — curated, tagged, verified hospital commitments matched to real outcome data — takes real work. That work has real value.

---

*Built at [Pursuit](https://pursuit.org) · April 2026*
