# ECHO — Technical Design Document

**Team Female | Pursuit AI-Native Cycle 3 | April 2026**
**Read this before writing any code. Every function must match this document exactly.**

---

## Overview

ECHO is a 6-tool pipeline. One hospital dict travels through all 6 tools in sequence. Each tool adds fields — nothing is ever removed or renamed. The pipeline is owned in three layers:

| Layer | Tools | Owner | Depends on |
|-------|-------|-------|-----------|
| Data | Tool 1 + Tool 2 | Jonel | CMS CSVs |
| Brain | Tool 3 + Tool 4 | Luba | Jonel's output |
| Voice | Tool 5 + Tool 6 | Paula | Luba's output |

**Pipeline order is non-negotiable.** Luba cannot start until Jonel's output is confirmed. Paula cannot start until Luba's output is confirmed.

---

## Tool 1 — Commitment Ingester

**File:** `src/commitment_ingester.py`
**Owner:** Jonel
**Function:** `get_hospital_commitments() -> list[dict]`

### What it does
Loads the curated hospital commitment CSV (50 hospitals, manually researched) and joins it with CMS Hospital General Information to get the birthing-friendly designation flag. Returns a list of hospital dicts — one per hospital.

### Inputs
No arguments. Reads from:
- `data/hospitals_commitments.csv` — manually curated, 50 rows, Jonel builds this
- `data/Hospital_General_Information.csv` — downloaded from CMS Provider Data Catalog

### Output shape
```python
{
  "facility_id":        str,   # e.g. "330024" — CMS CCN, primary join key
  "facility_name":      str,   # e.g. "Mount Sinai Hospital"
  "state":              str,   # 2-letter uppercase e.g. "NY"
  "county":             str,   # e.g. "New York"
  "hospital_type":      str,   # e.g. "Acute Care Hospitals"
  "hospital_ownership": str,   # e.g. "Voluntary non-profit - Other"
  "has_commitment":     bool,  # always True in v1
  "birthing_friendly":  bool,  # True if CMS designation = "Y"
  "commitment_tag":     str,   # specific quotable sentence — never a category label
  "commitment_source":  str,   # "CMS" / "Collaborative" / "ACOG" / "AWHONN" / "Press Release"
  "commitment_year":    int,   # e.g. 2023 — or None if year not found
}
```

### Logic
1. Load `hospitals_commitments.csv` with pandas
2. Load `Hospital_General_Information.csv` with pandas
3. Join on `facility_id` (CMS CCN)
4. Map `meets_criteria_for_birthing_friendly_designation` → `"Y"` = `True`, else `False`
5. Return list of dicts — one per row

### Field rules
- `state` must always be 2-letter uppercase. Use `.str.upper().str.strip()`
- `commitment_tag` must be a specific quotable sentence. Example: `"Joined NY Perinatal Quality Collaborative 2022"`. Never: `"has commitment"` or `"CMS designation"`
- `commitment_tag` must be `None` if `has_commitment` is `False` — not applicable in v1 but enforce the rule
- `commitment_year` is `None` if the year cannot be found — tag is still valid

### Test cases
| Test | Input | Expected output |
|------|-------|----------------|
| `test_output_shape` | Run function on real or mock CSV | Every dict has all 11 fields, no extras, no missing |
| `test_state_uppercase` | Hospital with state "ny" in CSV | Output state is "NY" |
| `test_commitment_tag_not_category` | Any hospital | `commitment_tag` is a sentence, not a label like "has commitment" |
| `test_facility_id_is_string` | Any hospital | `facility_id` is str, not int |
| `test_has_commitment_true` | v1 curated CSV | All hospitals have `has_commitment = True` |

### Done when
`get_hospital_commitments()` runs on real CSVs and returns a clean list of 50 hospital dicts with no missing fields and no schema violations.

---

## Tool 2 — Outcome Scorer

**File:** `src/outcome_scorer.py`
**Owner:** Jonel
**Function:** `score_outcomes(hospitals: list[dict]) -> list[dict]`

### What it does
Takes the list of hospital dicts from Tool 1 and adds CMS outcome fields to each dict. Joins across four CMS datasets using `facility_id` as the key.

### Inputs
- `hospitals` — list of dicts from `get_hospital_commitments()`

Reads from:
- `data/Maternal_Health-Hospital.csv` — maternal quality score, SMM rate, compared_to_national, postpartum visit %, well-baby visit %
- `data/FY2025_Hospital_Readmissions_Reduction_Program.csv` — readmission penalty flag, excess readmission ratio
- `data/HCAHPS-Hospital.csv` — care transition score
- `data/Hospital_General_Information.csv` — Medicaid payer mix proxy

### Output shape
Adds these fields to each dict:
```python
{
  "maternal_quality_score":       int,   # 1-5, LOWER = WORSE. e.g. 2
  "severe_morbidity_rate":        float, # per 10,000 deliveries. e.g. 145.2. None if missing.
  "compared_to_national":         str,   # EXACTLY "Better" / "Same" / "Worse"
  "postpartum_visit_pct":         float, # e.g. 45.0. None if missing.
  "state_avg_postpartum_pct":     float, # e.g. 72.0. Must travel with postpartum_visit_pct.
  "well_baby_visit_pct":          float, # e.g. 94.0. None if missing.
  "care_transition_score":        int,   # 1-5, LOWER = WORSE. None if missing.
  "readmission_penalty":          bool,  # True if CMS penalizing this hospital FY2025
  "excess_readmission_ratio":     float, # >1.0 = penalized. e.g. 1.08
  "medicaid_pct":                 float, # % Medicaid payer mix. e.g. 65.0
}
```

### Logic
1. Load each CMS CSV with pandas
2. For each hospital in the input list, look up its `facility_id` in each CSV
3. Add the fields to the dict
4. If a field is not found, set to `None` — never impute, never set to 0
5. If both `postpartum_visit_pct` and `severe_morbidity_rate` are `None`, log a warning — hospital stays in the list but will receive `data_confidence = "low"` in Tool 3

### Field rules
- `compared_to_national` must be exactly one of: `"Better"` / `"Same"` / `"Worse"` — capital first letter, nothing else. Map raw CMS values to these three strings explicitly.
- `state_avg_postpartum_pct` must always be set when `postpartum_visit_pct` is set — they travel together
- `care_transition_score` comes from HCAHPS — find the "Care Transition" composite measure, map to 1-5

### Test cases
| Test | Input | Expected output |
|------|-------|----------------|
| `test_compared_to_national_values` | Any hospital | Value is exactly "Better", "Same", or "Worse" — no other strings |
| `test_state_avg_travels_with_postpartum` | Hospital with postpartum_visit_pct set | `state_avg_postpartum_pct` is also set and not None |
| `test_missing_field_is_none_not_zero` | Hospital not found in CMS CSV | Missing field is `None`, not `0` |
| `test_no_hospitals_dropped` | 50 hospitals in | 50 hospitals out — missing data never drops a hospital |
| `test_readmission_penalty_is_bool` | Any hospital | `readmission_penalty` is `True` or `False`, not a string |

### Done when
`score_outcomes()` runs on real CMS CSVs, all 50 hospitals come out with outcome fields populated, no hospitals dropped, no schema violations.

---

## Tool 3 — Gap Calculator

**File:** `src/gap_calculator.py`
**Owner:** Luba
**Function:** `calculate_gap_score(hospital: dict) -> dict`

### What it does
Takes one hospital dict (after Tools 1 and 2) and calculates the commitment-outcome gap score and lead angle. This is the core intelligence of ECHO.

### Inputs
Single hospital dict with all Tool 1 + Tool 2 fields present.

### Scoring formula

**Layer 1 — Commitment Strength (max 25 pts)**
| Condition | Points |
|-----------|--------|
| `birthing_friendly = True` | +15 |
| `"MMSM"` in `commitment_tag` | +10 (stackable with birthing_friendly) |
| Any other non-empty commitment_tag | +5 (only if neither above scored) |

**Layer 2 — Outcome Gap (max 50 pts)**
| Condition | Points |
|-----------|--------|
| `compared_to_national = "Worse"` | +20 |
| `compared_to_national = "Same"` | +10 |
| `compared_to_national = "Better"` | 0 |
| `state_avg - postpartum_visit_pct` per 2 ppt below avg | +1 per 2 ppt, max 15 |
| `care_transition_score < 3` | +10 |
| `readmission_penalty = True` | +5 |

**Total after Tool 3: 0–75 (intermediate)**

### Lead angle logic (first match wins)
1. `well_baby_visit_pct - postpartum_visit_pct > 30` → `"baby_vs_mother_contrast"`
2. `compared_to_national == "Worse"` → `"severe_morbidity_rate"`
3. `state_avg - postpartum_visit_pct > 15` → `"postpartum_visit_gap"`
4. `care_transition_score < 3` → `"care_transition_gap"`
5. else → `"readmission_penalty"`

### Null handling rules
- `postpartum_visit_pct is None` → skip visit gap calculation entirely
- `severe_morbidity_rate is None` → rely on `compared_to_national` only (already default)
- `care_transition_score is None` → treat as neutral, 0 pts, no penalty
- `well_baby_visit_pct is None` → skip `baby_vs_mother_contrast` lead angle
- Both `postpartum_visit_pct` AND `severe_morbidity_rate` are `None` → `data_confidence = "low"`
- **Never substitute 0 for None** — that falsely penalizes the hospital
- Use `hospital.get("field") is not None` before every calculation

### Output shape
Adds these fields:
```python
{
  "gap_score":        float, # 0-75 INTERMEDIATE — not final
  "lead_angle":       str,   # one of five exact values above
  "data_confidence":  str,   # "high" or "low"
  "gap_breakdown":    dict,  # {"commitment_strength": int, "outcome_gap": int, "urgency_context": 0}
}
```

### Error handling
- Raise `ValueError` if `has_commitment = False` — v1 only scores committed hospitals

### Test cases
| Test | Input | Expected output |
|------|-------|----------------|
| `test_high_gap_score` | birthing_friendly=True, MMSM tag, Worse, postpartum=38, state_avg=72, well_baby=94, care_transition=2, readmission=True | gap_score=75, lead_angle="baby_vs_mother_contrast" |
| `test_commitment_strength_max_25` | birthing_friendly=True + MMSM tag | commitment_strength=25, not 26 |
| `test_outcome_gap_max_50` | All Layer 2 conditions true with large visit gap | outcome_gap=50, not 51 |
| `test_null_postpartum_skips_visit_gap` | postpartum_visit_pct=None | visit gap pts = 0, no crash |
| `test_null_care_transition_is_neutral` | care_transition_score=None | 0 pts added, no crash |
| `test_both_null_sets_low_confidence` | postpartum_visit_pct=None, severe_morbidity_rate=None | data_confidence="high" is NOT in output; data_confidence="low" |
| `test_no_commitment_raises` | has_commitment=False | raises ValueError mentioning "has_commitment" |
| `test_lead_angle_baby_vs_mother` | well_baby=94, postpartum=38 (gap=56 > 30) | lead_angle="baby_vs_mother_contrast" |
| `test_lead_angle_severe_morbidity` | well_baby=None, compared_to_national="Worse" | lead_angle="severe_morbidity_rate" |
| `test_gap_breakdown_structure` | Any valid hospital | gap_breakdown has keys: commitment_strength, outcome_gap, urgency_context=0 |

### Done when
`calculate_gap_score()` passes all 10 test cases. `gap_score` is always 0–75. `lead_angle` is always one of the five exact strings.

---

## Tool 4 — Urgency Ranker

**File:** `src/urgency_ranker.py`
**Owner:** Luba
**Function:** `add_urgency(hospital: dict) -> dict`

### What it does
Adds Layer 3 urgency context (state mortality data, racial disparity, Medicaid coverage) to the hospital dict, finalizes the gap_score to 0–100, and sets urgency tier and flag.

### Inputs
Single hospital dict after `calculate_gap_score()`. Also requires state context fields — Luba loads these from `data/kff_state_data.csv` and `data/cdc_wonder_export.csv` and merges them before calling this function.

Required fields in dict before calling:
- `gap_score` (0–75 intermediate)
- `gap_breakdown`
- `state` (2-letter code)
- `state_mortality_rank` (int 1–50)
- `medicaid_extended` (bool)
- `racial_disparity_flag` (bool)

### Layer 3 scoring (max 25 pts)
| Condition | Points |
|-----------|--------|
| `state_mortality_rank >= 40` | +10 |
| `racial_disparity_flag = True` | +8 |
| `medicaid_extended = True` | +7 |

### Urgency thresholds
| Final gap_score | urgency_tier | urgency_flag |
|----------------|-------------|-------------|
| ≥ 70 | `"high"` | `"🔴 Act this week"` |
| 40–69 | `"medium"` | `"🟡 Monitor"` |
| < 40 | `"low"` | `"🟢 Not ready"` |

### Output shape
Updates and adds these fields:
```python
{
  "gap_score":              float, # FINAL 0-100 — overwrites intermediate value
  "gap_breakdown":          dict,  # urgency_context key now filled in
  "urgency_flag":           str,   # exactly "🔴 Act this week" / "🟡 Monitor" / "🟢 Not ready"
  "urgency_tier":           str,   # exactly "high" / "medium" / "low"
  "state_mortality_rate":   float, # per 100k live births
  "state_mortality_rank":   int,   # 1-50
  "medicaid_extended":      bool,
  "racial_disparity_flag":  bool,
}
```

### Error handling
- Raise `KeyError` if `gap_score` or `gap_breakdown` missing — Tool 3 hasn't run
- Raise `ValueError` if `state_mortality_rank`, `medicaid_extended`, or `racial_disparity_flag` missing

### Test cases
| Test | Input | Expected output |
|------|-------|----------------|
| `test_high_urgency_threshold` | gap_score=75 + rank=48 + disparity=True + medicaid=True (L3=25) | final gap_score=100, urgency_tier="high", urgency_flag="🔴 Act this week" |
| `test_medium_urgency_threshold` | gap_score=35 + rank=42 + disparity=False + medicaid=True (L3=17) | final=52, urgency_tier="medium", urgency_flag="🟡 Monitor" |
| `test_low_urgency_threshold` | gap_score=20 + rank=15 + disparity=False + medicaid=False (L3=0) | final=20, urgency_tier="low", urgency_flag="🟢 Not ready" |
| `test_layer3_max_25` | rank=48 + disparity=True + medicaid=True | urgency_context=25, not 26 |
| `test_final_score_overwrites_intermediate` | gap_score=50 intermediate | gap_score after = 50 + L3 pts, not 50 |
| `test_urgency_flag_exact_strings` | Any hospital | urgency_flag is exactly one of three strings with emoji |
| `test_urgency_tier_lowercase` | Any hospital | urgency_tier is "high" / "medium" / "low" — never capitalized |
| `test_missing_gap_score_raises` | Dict without gap_score | raises KeyError |
| `test_gap_breakdown_urgency_context_filled` | Any valid hospital | gap_breakdown["urgency_context"] is an int, not 0 |

### Done when
`add_urgency()` passes all 9 test cases. `gap_score` is always 0–100. `urgency_tier` is always lowercase. Emoji strings are exact.

---

## Tool 5 — Outbound Generator

**File:** `src/outbound_generator.py`
**Owner:** Paula
**Function:** `generate_outbound_email(hospitals: list[dict]) -> list[dict]`

### What it does
Takes the full list of scored hospitals and generates one email object per high or medium urgency account. Each email object has three body variants — moral, clinical, financial. The GTM engineer reads all three and picks one. Nothing is sent.

### Inputs
List of hospital dicts that have passed through all four prior tools. Every dict must have `urgency_tier` present — if it's missing, Tool 4 has not run.

### Email structure
Every email body must:
- Quote `commitment_tag` verbatim
- Name a specific lagging metric with its number (e.g. "your postpartum visit rate is 45%")
- Leave `[COMPANY_NAME]` and `[SOCIAL_PROOF]` as placeholders — GTM engineer fills these in
- Never name a specific software company — ECHO is company-agnostic

**Variant A — Moral (`body_moral`)**
- Opens: commitment vs. outcome gap
- Lead hook for `baby_vs_mother_contrast`: *"Your well-baby visit rate is {well_baby}%. Your postpartum maternal visit rate is {postpartum_visit_pct}%. The system works. For babies."*
- Quotes commitment_tag, names the outcome gap

**Variant B — Clinical (`body_clinical`)**
- Opens: patient care failure, not just numbers
- Names postpartum visit rate vs. state average with both numbers
- References severe morbidity rate if available

**Variant C — Financial (`body_financial`)**
- Opens: unused reimbursement opportunity
- References `medicaid_pct` and whether state has `medicaid_extended = True`
- Hook: "49 states reimburse 12-month postpartum Medicaid"

### Output shape
```python
{
  "facility_id":      str,   # matches hospital dict
  "subject":          str,   # same subject for all 3 variants
  "to_role":          str,   # EXACTLY one of: "CMO" / "VP of Women's Services" /
                             #   "Chief Nursing Officer" / "VP of Quality"
  "body_moral":       str,   # Variant A — quotes commitment_tag
  "body_clinical":    str,   # Variant B — names postpartum metric with number
  "body_financial":   str,   # Variant C — references medicaid_pct
  "lead_angle_used":  str,   # from hospital dict — determines default variant on load
  "urgency_tier":     str,   # copied from hospital dict
}
```

### Lead angle → default variant
| lead_angle | Pre-selected variant |
|------------|---------------------|
| `baby_vs_mother_contrast` | `body_moral` |
| `severe_morbidity_rate` | `body_clinical` |
| `postpartum_visit_gap` | `body_clinical` |
| `care_transition_gap` | `body_clinical` |
| `readmission_penalty` | `body_financial` |

### Test cases
| Test | Input | Expected output |
|------|-------|----------------|
| `test_low_urgency_skipped` | Hospital with urgency_tier="low" | Not in output list |
| `test_high_and_medium_included` | Mix of high/medium/low hospitals | Only high and medium in output |
| `test_body_moral_quotes_commitment_tag` | Any hospital | `body_moral` contains the exact `commitment_tag` string |
| `test_body_clinical_has_postpartum_number` | postpartum_visit_pct=45.0 | `body_clinical` contains "45" |
| `test_body_financial_has_medicaid_number` | medicaid_pct=65.0 | `body_financial` contains "65" |
| `test_to_role_exact_values` | Any hospital | `to_role` is one of the four exact strings |
| `test_no_company_name_hardcoded` | Any hospital | None of the three bodies contain "Babyscripts", "Maven", "Wildflower", "Mahmee", "Bloomlife", "Cocoon" |
| `test_placeholder_present` | Any hospital | At least one body contains "[COMPANY_NAME]" |
| `test_output_has_all_fields` | Any valid hospital | Email object has all 8 fields |
| `test_urgency_tier_copied_correctly` | urgency_tier="high" | email["urgency_tier"] == "high" |

### Done when
`generate_outbound_email()` passes all 10 test cases. Every email has three distinct body variants. No company names hardcoded. All `to_role` values are from the exact allowed list.

---

## Tool 6 — Human Checkpoint

**File:** `src/human_checkpoint.py`
**Owner:** Paula
**Function:** `display_checkpoint(hospitals: list[dict], emails: list[dict]) -> str`

### What it does
Displays all email drafts for human review in the terminal (v1) or dashboard (v2). Returns a summary string. Nothing is sent. This is the final gate before any GTM action.

### Inputs
- `hospitals` — full list of hospital dicts from the pipeline
- `emails` — list of email objects from `generate_outbound_email()`

### Output
- Side effect: prints formatted review to terminal
- Returns: summary string — e.g. `"3 high-urgency, 2 medium-urgency accounts ready. Nothing sent."`

### Display requirements (v1 terminal)
For each email, display:
- Hospital name, state, urgency flag, final gap score
- Commitment tag (what the hospital publicly committed to)
- Lead angle (what ECHO is leading with)
- All three email body variants labeled A / B / C
- Clear separator between accounts

### Test cases
| Test | Input | Expected output |
|------|-------|----------------|
| `test_returns_summary_string` | Any valid inputs | Returns a string, not None |
| `test_summary_counts_correct` | 3 high + 2 medium emails | String contains "3" and "2" |
| `test_nothing_sent_in_summary` | Any inputs | Return string contains "Nothing sent" or equivalent |

### Done when
`display_checkpoint()` passes all 3 test cases and prints a readable review to the terminal that a GTM engineer could use without further explanation.

---

## Integration Test

**File:** `tests/test_pipeline.py`

### What it tests
The full pipeline runs end to end with all 6 tools using the mock hospital data in `tests/fixtures.py`. No real CMS CSVs required.

### Test cases
| Test | What it proves |
|------|---------------|
| `test_full_pipeline_runs` | All 6 tools run in sequence without error on mock data |
| `test_dict_fields_only_grow` | Hospital dict after each tool has more fields than before — nothing removed |
| `test_gap_score_intermediate_then_final` | gap_score after Tool 3 is ≤75; gap_score after Tool 4 is ≤100 |
| `test_only_high_medium_get_emails` | Low urgency hospitals have no email in output |
| `test_data_confidence_low_flagged` | Hospital with both postpartum and SMM = None gets data_confidence="low" |

---

## Shared Fixtures

**File:** `tests/fixtures.py`

All test files import from here. One source of truth for test data.

```python
# High gap hospital — scores ≥70 after urgency
HIGH_GAP = {
    "facility_id": "010001", "facility_name": "Test High Gap Hospital",
    "state": "MS", "county": "Hinds",
    "hospital_type": "Acute Care Hospitals", "hospital_ownership": "Voluntary non-profit",
    "has_commitment": True, "birthing_friendly": True,
    "commitment_tag": "Joined MMSM Initiative 2022",
    "commitment_source": "Collaborative", "commitment_year": 2022,
    "maternal_quality_score": 1, "severe_morbidity_rate": 145.2,
    "compared_to_national": "Worse",
    "postpartum_visit_pct": 38.0, "state_avg_postpartum_pct": 72.0,
    "well_baby_visit_pct": 94.0, "care_transition_score": 2,
    "readmission_penalty": True, "excess_readmission_ratio": 1.12, "medicaid_pct": 74.0,
    "state_mortality_rate": 49.2, "state_mortality_rank": 50,
    "medicaid_extended": True, "racial_disparity_flag": True,
}

# Medium gap hospital — scores 40-69 after urgency
MEDIUM_GAP = {
    "facility_id": "020002", "facility_name": "Test Medium Gap Hospital",
    "state": "GA", "county": "Fulton",
    "hospital_type": "Acute Care Hospitals", "hospital_ownership": "Voluntary non-profit",
    "has_commitment": True, "birthing_friendly": False,
    "commitment_tag": "Adopted ACOG Postpartum Toolkit 2021",
    "commitment_source": "ACOG", "commitment_year": 2021,
    "maternal_quality_score": 3, "severe_morbidity_rate": 72.0,
    "compared_to_national": "Same",
    "postpartum_visit_pct": 55.0, "state_avg_postpartum_pct": 72.0,
    "well_baby_visit_pct": 68.0, "care_transition_score": 3,
    "readmission_penalty": False, "excess_readmission_ratio": 0.98, "medicaid_pct": 55.0,
    "state_mortality_rate": 33.1, "state_mortality_rank": 45,
    "medicaid_extended": True, "racial_disparity_flag": True,
}

# Low gap hospital — scores <40 after urgency
LOW_GAP = {
    "facility_id": "030003", "facility_name": "Test Low Gap Hospital",
    "state": "CA", "county": "San Francisco",
    "hospital_type": "Acute Care Hospitals", "hospital_ownership": "Proprietary",
    "has_commitment": True, "birthing_friendly": False,
    "commitment_tag": "Adopted ACOG Postpartum Toolkit 2020",
    "commitment_source": "ACOG", "commitment_year": 2020,
    "maternal_quality_score": 4, "severe_morbidity_rate": 40.0,
    "compared_to_national": "Better",
    "postpartum_visit_pct": 80.0, "state_avg_postpartum_pct": 72.0,
    "well_baby_visit_pct": 85.0, "care_transition_score": 4,
    "readmission_penalty": False, "excess_readmission_ratio": 0.92, "medicaid_pct": 30.0,
    "state_mortality_rate": 14.2, "state_mortality_rank": 12,
    "medicaid_extended": False, "racial_disparity_flag": False,
}

# Null data hospital — missing key outcome fields
NULL_DATA = {
    "facility_id": "040004", "facility_name": "Test Null Data Hospital",
    "state": "TX", "county": "Harris",
    "hospital_type": "Acute Care Hospitals", "hospital_ownership": "Government",
    "has_commitment": True, "birthing_friendly": True,
    "commitment_tag": "Joined TX Perinatal Quality Collaborative 2023",
    "commitment_source": "Collaborative", "commitment_year": 2023,
    "maternal_quality_score": 3, "severe_morbidity_rate": None,
    "compared_to_national": "Same",
    "postpartum_visit_pct": None, "state_avg_postpartum_pct": None,
    "well_baby_visit_pct": None, "care_transition_score": None,
    "readmission_penalty": False, "excess_readmission_ratio": 1.0, "medicaid_pct": 45.0,
    "state_mortality_rate": 28.7, "state_mortality_rank": 42,
    "medicaid_extended": False, "racial_disparity_flag": True,
}

# No commitment hospital — should raise ValueError in Tool 3
NO_COMMITMENT = {
    "facility_id": "050005", "facility_name": "Test No Commitment Hospital",
    "state": "FL", "county": "Miami-Dade",
    "hospital_type": "Acute Care Hospitals", "hospital_ownership": "Proprietary",
    "has_commitment": False, "birthing_friendly": False,
    "commitment_tag": None, "commitment_source": None, "commitment_year": None,
    "maternal_quality_score": 4, "severe_morbidity_rate": 40.0,
    "compared_to_national": "Better",
    "postpartum_visit_pct": 80.0, "state_avg_postpartum_pct": 72.0,
    "well_baby_visit_pct": 85.0, "care_transition_score": 4,
    "readmission_penalty": False, "excess_readmission_ratio": 0.92, "medicaid_pct": 30.0,
    "state_mortality_rate": 14.2, "state_mortality_rank": 12,
    "medicaid_extended": False, "racial_disparity_flag": False,
}
```

---

## What "Done" Means for Each Person

| Person | Done when |
|--------|----------|
| **Jonel** | `get_hospital_commitments()` + `score_outcomes()` run on real CMS CSVs, return 50 hospital dicts, all 5 Tool 1 tests pass, all 5 Tool 2 tests pass |
| **Luba** | `calculate_gap_score()` + `add_urgency()` run on Jonel's output, all 10 Tool 3 tests pass, all 9 Tool 4 tests pass, output is ranked list with final gap scores |
| **Paula** | `generate_outbound_email()` + `display_checkpoint()` run on Luba's output, all 10 Tool 5 tests pass, all 3 Tool 6 tests pass, 3 email variants display cleanly in terminal |
| **Team** | `test_pipeline.py` integration test passes end to end, `python src/agent.py NY` produces a human checkpoint with real NY hospitals and real email drafts |

---

*Last updated: April 2026 — Team Female, Pursuit AI-Native Cycle 3*
*Schema changes require team agreement. Test cases are the contract. Code that passes the tests ships.*
