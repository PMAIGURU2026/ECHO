# ECHO — Shared Data Schema
Team Female | Pursuit AI-Native Cycle 3 | April 2026

This is the team's source of truth for the week. If a field name, type, or value is not in this document, it does not exist. Every function in every file must match this schema exactly — no exceptions, no variations.


## Pipeline Order
Jonel (Tools 1+2) → Luba (Tools 3+4) → Paula (Tools 5+6) → Human

Jonel must finish first. Luba cannot score without Jonel's output. Paula cannot generate emails without Luba's scores.


## The Hospital Dict — Full Schema
One dict per hospital travels through the entire pipeline. Each tool adds fields — nothing is ever removed or renamed.

### After Tool 1 — Commitment Ingester (Jonel)
```python
{
  # ── IDENTITY ──────────────────────────────────────────────────────
  "facility_id":        str,   # CMS hospital ID e.g. "010001"
                               # PRIMARY KEY — used to join all CMS files
  "facility_name":      str,   # Full name e.g. "Valley General Hospital"
  "state":              str,   # 2-letter code e.g. "MS" — ALWAYS uppercase
  "county":             str,   # County name e.g. "Hinds"
  "hospital_type":      str,   # "Acute Care" / "Critical Access" / other CMS values
  "hospital_ownership": str,   # "Voluntary non-profit" / "Government" / "Proprietary"

  # ── COMMITMENT SIGNALS ────────────────────────────────────────────
  "has_commitment":     bool,  # True if any public commitment found
                               # v1: always True (curated DB only has committed hospitals)
                               # v2: False for silent-gap hospitals
  "birthing_friendly":  bool,  # CMS birthing-friendly designation YES=True NO=False
  "commitment_tag":     str,   # Specific quotable sentence e.g.
                               # "Joined GA Perinatal Quality Collaborative 2023"
                               # MUST be specific — never a category label
                               # MUST be None if has_commitment=False
  "commitment_source":  str,   # "CMS" / "Collaborative" / "ACOG" / "AWHONN" / "Press Release"
  "commitment_year":    int,   # Year of commitment e.g. 2023
                               # Use None if year not found
}
```

### After Tool 2 — Outcome Scorer (Jonel)
Adds outcome fields to the dict above:

```python
{
  # ── OUTCOME DATA ──────────────────────────────────────────────────
  "maternal_quality_score":       int,   # CMS overall maternal score 1-5
                                         # LOWER = WORSE
  "severe_morbidity_rate":        float, # SMM rate per 10,000 deliveries
  "compared_to_national":         str,   # "Better" / "Same" / "Worse"
                                         # EXACTLY these three strings, no variations
  "postpartum_visit_pct":         float, # % patients with postpartum visit e.g. 45.0
  "state_avg_postpartum_pct":     float, # State benchmark e.g. 72.0
                                         # Must travel with postpartum_visit_pct always
  "well_baby_visit_pct":          float, # % well-baby visit completion e.g. 94.0
  "care_transition_score":        int,   # HCAHPS care transition stars 1-5
                                         # LOWER = WORSE
  "readmission_penalty":          bool,  # True if CMS penalizing this hospital FY2025
  "excess_readmission_ratio":     float, # 1.0 = average, above 1.0 = penalized
  "medicaid_pct":                 float, # % Medicaid payer mix e.g. 74.0
}
```

### After Tool 3 — Gap Calculator (Luba)
Adds gap score fields:

```python
{
  # ── GAP SCORE ─────────────────────────────────────────────────────
  "gap_score":          float, # 0-75 AFTER this tool (intermediate value)
                               # ⚠️ NOT FINAL — urgency_ranker adds up to 25 more pts
                               # Paula must NOT read gap_score until after add_urgency()
  "lead_angle":         str,   # Which mismatch to lead with in outbound email
                               # EXACTLY one of these five strings:
                               # "baby_vs_mother_contrast"
                               # "severe_morbidity_rate"
                               # "postpartum_visit_gap"
                               # "care_transition_gap"
                               # "readmission_penalty"
                               # v2 adds: "silent_gap" (for has_commitment=False)
  "gap_breakdown":      dict,  # Point breakdown for transparency
                               # {
                               #   "commitment_strength": int,  # 0-25
                               #   "outcome_gap": int,          # 0-50
                               #   "urgency_context": int       # 0-25 (added by Tool 4)
                               # }
  "data_confidence":    str,   # "high" or "low"
                               # "low" = both postpartum_visit_pct AND
                               #   severe_morbidity_rate are None
                               # "high" = at least one key outcome field present
                               # Paula: show "data unavailable" on briefing card
                               #   when data_confidence = "low"
}
```

### After Tool 4 — Urgency Ranker (Luba)
Updates gap_score to FINAL value and adds urgency fields:

```python
{
  # ── URGENCY ───────────────────────────────────────────────────────
  "gap_score":              float, # ✅ FINAL VALUE — Layer 1 + 2 + 3 complete
                                   # Paula reads this value, not the intermediate one
                                   # Max 100 for commitment-gap hospitals
                                   # Max 75 for silent-gap hospitals (v2)
  "urgency_flag":           str,   # EXACTLY one of:
                                   # "🔴 Act this week"
                                   # "🟡 Monitor"
                                   # "🟢 Not ready"
  "urgency_tier":           str,   # EXACTLY one of: "high" / "medium" / "low"
                                   # Paula's email template branches on this value
                                   # Must be consistent — no variations
  "state_mortality_rate":   float, # Per 100k live births e.g. 32.1
  "state_mortality_rank":   int,   # 1-50, higher = worse state e.g. 47
  "medicaid_extended":      bool,  # True if state has 12-month Medicaid postpartum coverage
  "racial_disparity_flag":  bool,  # True if Black MMR > 2x White MMR in this state
}
```

### After Tool 5 — Outbound Generator (Paula)
One email object per hospital, separate from the hospital dict:

```python
{
  "facility_id":        str,   # Matches hospital dict — used to link email to account
  "subject":            str,   # Email subject line
  "to_role":            str,   # Recommended contact role e.g. "VP of Women's Services"
                               # EXACTLY one of:
                               # "CMO" / "VP of Women's Services" /
                               # "Chief Nursing Officer" / "VP of Quality"
  "body":               str,   # Full email body — quotes commitment_tag and
                               # names specific lagging metric with number
  "lead_angle_used":    str,   # Which lead_angle from hospital dict drove the email
  "urgency_tier":       str,   # Copied from hospital dict — "high"/"medium"/"low"
}
```


## ⚠️ Critical Handoff Note — gap_score
gap_score appears in the hospital dict after Tool 3 AND after Tool 4.

- After Tool 3 (calculate_gap_score): value is 0-75. This is **intermediate**. Do not use.
- After Tool 4 (add_urgency): value is 0-100. This is **final**. Paula reads this.

Paula's Outbound Generator must only consume hospital dicts that have passed through `add_urgency()`. If `urgency_tier` is not present in the dict, `add_urgency()` has not run yet — do not proceed.


## Field Rules — Non-Negotiable
These rules apply to every file, every function, every person:

1. **Field names are exact.** `facility_name` not `hospital_name`. `postpartum_visit_pct` not `postpartum_pct`. Copy from this doc, do not type from memory.

2. **State is always 2-letter uppercase.** `"MS"` not `"Mississippi"` not `"ms"`.

3. **`compared_to_national` is always one of exactly three strings.** `"Better"` / `"Same"` / `"Worse"`. Capital first letter. No other values.

4. **`urgency_tier` is always one of exactly three strings.** `"high"` / `"medium"` / `"low"`. Lowercase. Paula's email template branches on this — any variation breaks her code.

5. **`commitment_tag` is a specific quotable sentence or None.** Never an empty string `""`. Never a category like `"has commitment"`. If Jonel can't find a specific statement, the value is `None` and `has_commitment` is `False`.

6. **`gap_score` after Tool 3 is intermediate.** Only read `gap_score` after `urgency_tier` is present in the dict.


## Missing Data Handling

CMS data has gaps. `gap_calculator.py` must never crash on `None`. Hospitals are **never skipped** for missing data in v1 — they are scored on what is available and flagged with `data_confidence`.

### Per-field rules

| Field | If missing | Effect on scoring |
|-------|-----------|-------------------|
| `postpartum_visit_pct` | `None` — do not impute | Skip visit gap calculation in Layer 2 entirely |
| `severe_morbidity_rate` | `None` — do not impute | Rely on `compared_to_national` only (already the default) |
| `care_transition_score` | `None` — do not impute | Treat as neutral — 0 pts, no penalty |
| `well_baby_visit_pct` | `None` — do not impute | Skip `baby_vs_mother_contrast` lead angle |
| `commitment_year` | `None` — tag still valid | No scoring impact |

### data_confidence field

Output of `gap_calculator.py`. Set based on how much outcome data is available:

- `"low"` — both `postpartum_visit_pct` **and** `severe_morbidity_rate` are `None`
- `"high"` — at least one of those fields is present

**Paula:** when `data_confidence = "low"`, display `"data unavailable"` on the briefing card instead of the gap score number.

### Implementation rules for Luba

- Use `hospital.get("field_name") is not None` before every calculation that could receive `None`
- Never substitute `0` for a missing value — that would falsely penalize the hospital
- Never skip a hospital — score what you have, set `data_confidence` accordingly


## v1 Scope Boundaries
These are **NOT** in v1. Do not build them this week:

- Live web scraping of press releases
- CRM integration
- Sending emails
- Clinical recommendations
- Patient-facing features
- Ranking the top 10 against each other
- Silent Gap mode (`has_commitment=False`) — this is v2


## v2 Changes (next week, do not touch now)
- Add `has_commitment: bool` as a required field
- Add `"silent_gap"` as a valid `lead_angle` value
- Update Gap Calculator to skip Layer 1 when `has_commitment=False`
- Cap score at 75 for silent-gap hospitals
- Paula adds second email template for silent-gap accounts
- Add `disparity_worsening_trend: bool` to urgency context (Layer 3)
  — `True` if the Black/White maternal mortality gap in that state is **widening post-2020**,
  not just high. Source: Kamijo et al., Cureus 2025 — post-pandemic racial disparity trend data.
  A widening trend is a stronger urgency signal than a static gap.
  Will replace or stack with `racial_disparity_flag` in `urgency_ranker.py`.


## File Ownership

| File | Owner | Depends on |
|------|-------|-----------|
| `commitment_ingester.py` | Jonel | Raw CMS CSVs + manual commitment CSV |
| `outcome_scorer.py` | Jonel | Output of `commitment_ingester.py` |
| `gap_calculator.py` | Luba | Output of `outcome_scorer.py` |
| `urgency_ranker.py` | Luba | Output of `gap_calculator.py` + KFF/CDC CSVs |
| `outbound_generator.py` | Paula | Output of `urgency_ranker.py` (final gap_score only) |
| `human_checkpoint.py` | Paula | Output of `outbound_generator.py` |
| `hospitals_commitments.csv` | Jonel | Manual research — 50 hospitals with commitment tags |
| `kff_state_data.csv` | Luba | Downloaded from kff.org |
| `cdc_wonder_export.csv` | Luba | Downloaded from wonder.cdc.gov |


## Wednesday Deliverables

| Person | Done when |
|--------|----------|
| Jonel | `outcome_scorer.py` runs on real CMS CSVs, outputs clean list of 50 hospital dicts matching this schema |
| Luba | `gap_calculator.py` + `urgency_ranker.py` run on Jonel's output, produce ranked top 10 with final gap scores |
| Paula | `outbound_generator.py` produces one draft email per top-10 account, `human_checkpoint.py` displays them clearly |


---
*Last updated: April 2026 — Team Female, Pursuit AI-Native Cycle 3*
*Any schema changes must be agreed by all three team members before implementation.*
