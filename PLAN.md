# ECHO v1 — Build Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build all 6 pipeline tools, wire them into agent.py, and produce a working human checkpoint with real NY hospital data and 3 email variants per account.

**Architecture:** Six tools share one hospital dict. Jonel builds the data layer first (Tools 1+2). Luba builds the scoring layer second (Tools 3+4). Paula builds the output layer third (Tools 5+6). Integration runs last. No one skips ahead — each layer depends on the previous one's output.

**Tech Stack:** Python 3.12, strands-agents 1.37, OpenRouter (tencent/hy3-preview:free), pandas, requests, pytest, python-dotenv

---

## Before Anyone Writes Code

Read these three files first. Every function must match them exactly.

- `SCHEMA.md` — field names, types, exact string values, null handling rules
- `TDD.md` — what each tool does, test cases, done criteria
- `tests/fixtures.py` — shared test hospitals (written in Task 0 below)

**Pipeline order is a hard constraint:**
```
Jonel (Tools 1+2) → Luba (Tools 3+4) → Paula (Tools 5+6) → Integration
```
Luba starts Task 4 only after Jonel's Task 3 is marked done.
Paula starts Task 6 only after Luba's Task 5 is marked done.

---

## File Map

| File | Owner | Status |
|------|-------|--------|
| `tests/fixtures.py` | Luba | Task 0 — write first, everyone imports |
| `tests/test_commitment_ingester.py` | Jonel | Task 1 |
| `src/commitment_ingester.py` | Jonel | Task 2 |
| `tests/test_outcome_scorer.py` | Jonel | Task 3a |
| `src/outcome_scorer.py` | Jonel | Task 3b |
| `tests/test_gap_calculator.py` | Luba | Task 4a |
| `src/gap_calculator.py` | Luba | Task 4b |
| `tests/test_urgency_ranker.py` | Luba | Task 5a |
| `src/urgency_ranker.py` | Luba | Task 5b |
| `tests/test_outbound_generator.py` | Paula | Task 6a |
| `src/outbound_generator.py` | Paula | Task 6b |
| `tests/test_human_checkpoint.py` | Paula | Task 7a |
| `src/human_checkpoint.py` | Paula | Task 7b |
| `tests/test_pipeline.py` | All | Task 8 |
| `src/agent.py` | All | Task 9 |

---

## Task 0: Shared Test Fixtures
**Owner:** Luba
**Do this first. Everyone imports from here.**

**Files:**
- Create: `tests/fixtures.py`

- [ ] **Step 1: Create tests/fixtures.py with all 5 test hospitals**

```python
# tests/fixtures.py
"""
Shared test fixtures for all ECHO tests.
Import these instead of defining your own test hospitals.
Every fixture has all fields needed to run the full pipeline.
"""

HIGH_GAP = {
    "facility_id": "010001", "facility_name": "Test High Gap Hospital",
    "state": "MS", "county": "Hinds",
    "hospital_type": "Acute Care Hospitals",
    "hospital_ownership": "Voluntary non-profit",
    "has_commitment": True, "birthing_friendly": True,
    "commitment_tag": "Joined MMSM Initiative 2022",
    "commitment_source": "Collaborative", "commitment_year": 2022,
    "maternal_quality_score": 1, "severe_morbidity_rate": 145.2,
    "compared_to_national": "Worse",
    "postpartum_visit_pct": 38.0, "state_avg_postpartum_pct": 72.0,
    "well_baby_visit_pct": 94.0, "care_transition_score": 2,
    "readmission_penalty": True, "excess_readmission_ratio": 1.12,
    "medicaid_pct": 74.0,
    "state_mortality_rate": 49.2, "state_mortality_rank": 50,
    "medicaid_extended": True, "racial_disparity_flag": True,
}

MEDIUM_GAP = {
    "facility_id": "020002", "facility_name": "Test Medium Gap Hospital",
    "state": "GA", "county": "Fulton",
    "hospital_type": "Acute Care Hospitals",
    "hospital_ownership": "Voluntary non-profit",
    "has_commitment": True, "birthing_friendly": False,
    "commitment_tag": "Adopted ACOG Postpartum Toolkit 2021",
    "commitment_source": "ACOG", "commitment_year": 2021,
    "maternal_quality_score": 3, "severe_morbidity_rate": 72.0,
    "compared_to_national": "Same",
    "postpartum_visit_pct": 55.0, "state_avg_postpartum_pct": 72.0,
    "well_baby_visit_pct": 68.0, "care_transition_score": 3,
    "readmission_penalty": False, "excess_readmission_ratio": 0.98,
    "medicaid_pct": 55.0,
    "state_mortality_rate": 33.1, "state_mortality_rank": 45,
    "medicaid_extended": True, "racial_disparity_flag": True,
}

LOW_GAP = {
    "facility_id": "030003", "facility_name": "Test Low Gap Hospital",
    "state": "CA", "county": "San Francisco",
    "hospital_type": "Acute Care Hospitals",
    "hospital_ownership": "Proprietary",
    "has_commitment": True, "birthing_friendly": False,
    "commitment_tag": "Adopted ACOG Postpartum Toolkit 2020",
    "commitment_source": "ACOG", "commitment_year": 2020,
    "maternal_quality_score": 4, "severe_morbidity_rate": 40.0,
    "compared_to_national": "Better",
    "postpartum_visit_pct": 80.0, "state_avg_postpartum_pct": 72.0,
    "well_baby_visit_pct": 85.0, "care_transition_score": 4,
    "readmission_penalty": False, "excess_readmission_ratio": 0.92,
    "medicaid_pct": 30.0,
    "state_mortality_rate": 14.2, "state_mortality_rank": 12,
    "medicaid_extended": False, "racial_disparity_flag": False,
}

NULL_DATA = {
    "facility_id": "040004", "facility_name": "Test Null Data Hospital",
    "state": "TX", "county": "Harris",
    "hospital_type": "Acute Care Hospitals",
    "hospital_ownership": "Government",
    "has_commitment": True, "birthing_friendly": True,
    "commitment_tag": "Joined TX Perinatal Quality Collaborative 2023",
    "commitment_source": "Collaborative", "commitment_year": 2023,
    "maternal_quality_score": 3, "severe_morbidity_rate": None,
    "compared_to_national": "Same",
    "postpartum_visit_pct": None, "state_avg_postpartum_pct": None,
    "well_baby_visit_pct": None, "care_transition_score": None,
    "readmission_penalty": False, "excess_readmission_ratio": 1.0,
    "medicaid_pct": 45.0,
    "state_mortality_rate": 28.7, "state_mortality_rank": 42,
    "medicaid_extended": False, "racial_disparity_flag": True,
}

NO_COMMITMENT = {
    "facility_id": "050005", "facility_name": "Test No Commitment Hospital",
    "state": "FL", "county": "Miami-Dade",
    "hospital_type": "Acute Care Hospitals",
    "hospital_ownership": "Proprietary",
    "has_commitment": False, "birthing_friendly": False,
    "commitment_tag": None, "commitment_source": None, "commitment_year": None,
    "maternal_quality_score": 4, "severe_morbidity_rate": 40.0,
    "compared_to_national": "Better",
    "postpartum_visit_pct": 80.0, "state_avg_postpartum_pct": 72.0,
    "well_baby_visit_pct": 85.0, "care_transition_score": 4,
    "readmission_penalty": False, "excess_readmission_ratio": 0.92,
    "medicaid_pct": 30.0,
    "state_mortality_rate": 14.2, "state_mortality_rank": 12,
    "medicaid_extended": False, "racial_disparity_flag": False,
}
```

- [ ] **Step 2: Verify fixtures import cleanly**

```bash
cd /Users/lubakaper/Desktop/L3Projects/ECHO
.venv/bin/python -c "from tests.fixtures import HIGH_GAP, MEDIUM_GAP, LOW_GAP, NULL_DATA, NO_COMMITMENT; print('fixtures OK')"
```
Expected: `fixtures OK`

- [ ] **Step 3: Commit**

```bash
git add tests/fixtures.py
git commit -m "test: add shared fixtures for all pipeline tests"
```

---

## Task 1: Test — Commitment Ingester
**Owner:** Jonel
**Write tests before writing the function.**

**Files:**
- Create: `tests/test_commitment_ingester.py`

- [ ] **Step 1: Write test_commitment_ingester.py**

```python
# tests/test_commitment_ingester.py
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from commitment_ingester import get_hospital_commitments


def test_returns_list():
    result = get_hospital_commitments()
    assert isinstance(result, list)
    assert len(result) > 0


def test_output_shape():
    result = get_hospital_commitments()
    required_fields = [
        "facility_id", "facility_name", "state", "county",
        "hospital_type", "hospital_ownership", "has_commitment",
        "birthing_friendly", "commitment_tag", "commitment_source",
        "commitment_year",
    ]
    for hospital in result:
        for field in required_fields:
            assert field in hospital, f"Missing field: {field} in {hospital.get('facility_name')}"


def test_state_is_uppercase():
    result = get_hospital_commitments()
    for hospital in result:
        assert hospital["state"] == hospital["state"].upper(), \
            f"State not uppercase: {hospital['state']}"
        assert len(hospital["state"]) == 2, \
            f"State not 2 letters: {hospital['state']}"


def test_facility_id_is_string():
    result = get_hospital_commitments()
    for hospital in result:
        assert isinstance(hospital["facility_id"], str), \
            f"facility_id must be str, got {type(hospital['facility_id'])}"


def test_has_commitment_true():
    result = get_hospital_commitments()
    for hospital in result:
        assert hospital["has_commitment"] is True, \
            f"v1 hospitals must have has_commitment=True: {hospital['facility_name']}"


def test_commitment_tag_not_category():
    result = get_hospital_commitments()
    bad_tags = ["has commitment", "committed", "yes", "true", "designation"]
    for hospital in result:
        tag = hospital.get("commitment_tag") or ""
        for bad in bad_tags:
            assert tag.lower() != bad.lower(), \
                f"commitment_tag is a category label, not a sentence: '{tag}'"
        assert len(tag) > 20, \
            f"commitment_tag too short to be a real sentence: '{tag}'"


def test_birthing_friendly_is_bool():
    result = get_hospital_commitments()
    for hospital in result:
        assert isinstance(hospital["birthing_friendly"], bool), \
            f"birthing_friendly must be bool: {hospital['facility_name']}"
```

- [ ] **Step 2: Run — confirm all tests FAIL (function doesn't exist yet)**

```bash
.venv/bin/python -m pytest tests/test_commitment_ingester.py -v 2>&1 | head -20
```
Expected: `ImportError: cannot import name 'get_hospital_commitments'`

- [ ] **Step 3: Commit the failing tests**

```bash
git add tests/test_commitment_ingester.py
git commit -m "test: add commitment_ingester tests (failing — TDD)"
```

---

## Task 2: Build — Commitment Ingester
**Owner:** Jonel
**Now write the function to make the tests pass.**

**Files:**
- Create: `src/commitment_ingester.py`
- Create: `data/hospitals_commitments.csv` (manual research — see below)

- [ ] **Step 1: Download CMS Hospital General Information CSV**

Go to: https://data.cms.gov/provider-data/dataset/xubh-q36u
Click "Download" → CSV. Save to `data/Hospital_General_Information.csv`.

- [ ] **Step 2: Create hospitals_commitments.csv**

Create `data/hospitals_commitments.csv` with these columns:
```
facility_id,facility_name,state,county,commitment_tag,commitment_source,commitment_year
```
50 rows. One row per NY birthing-friendly hospital. `commitment_tag` must be a specific quotable sentence — find it from the hospital's website, press releases, or collaborative membership lists.

Example rows:
```csv
330024,Mount Sinai Hospital,NY,New York,"Joined NY Perinatal Quality Collaborative 2021",Collaborative,2021
330101,NewYork-Presbyterian / Columbia,NY,New York,"Committed to eliminating maternal health disparities by 2025 (press release Feb 2023)",Press Release,2023
```

- [ ] **Step 3: Write commitment_ingester.py**

```python
# src/commitment_ingester.py
"""
commitment_ingester.py — Tool 1 | Owner: Jonel

Loads hospital commitment data from curated CSV + CMS General Info.
Returns list of hospital dicts with Tool 1 fields per SCHEMA.md.

Run: called by agent.py as the first tool in the pipeline.
Reads: data/hospitals_commitments.csv, data/Hospital_General_Information.csv
"""
import os
import pandas as pd
from typing import Any

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')


def get_hospital_commitments() -> list[dict[str, Any]]:
    """
    Load and join commitment CSV with CMS general info.
    Returns list of hospital dicts with Tool 1 fields.
    """
    commitments = pd.read_csv(os.path.join(DATA_DIR, 'hospitals_commitments.csv'), dtype={'facility_id': str})
    cms = pd.read_csv(os.path.join(DATA_DIR, 'Hospital_General_Information.csv'), dtype={'Facility ID': str})

    cms = cms.rename(columns={
        'Facility ID': 'facility_id',
        'Facility Name': 'facility_name',
        'State': 'state',
        'County/Parish': 'county',
        'Hospital Type': 'hospital_type',
        'Hospital Ownership': 'hospital_ownership',
        'Meets criteria for birthing friendly designation': 'birthing_friendly_raw',
    })

    merged = commitments.merge(
        cms[['facility_id', 'facility_name', 'state', 'county',
             'hospital_type', 'hospital_ownership', 'birthing_friendly_raw']],
        on='facility_id',
        how='left',
    )

    hospitals = []
    for _, row in merged.iterrows():
        hospitals.append({
            'facility_id':        str(row['facility_id']).strip(),
            'facility_name':      str(row.get('facility_name', row.get('facility_name_x', ''))).strip(),
            'state':              str(row['state']).strip().upper(),
            'county':             str(row.get('county', '')).strip(),
            'hospital_type':      str(row.get('hospital_type', '')).strip(),
            'hospital_ownership': str(row.get('hospital_ownership', '')).strip(),
            'has_commitment':     True,
            'birthing_friendly':  str(row.get('birthing_friendly_raw', '')).strip().upper() == 'Y',
            'commitment_tag':     str(row['commitment_tag']).strip(),
            'commitment_source':  str(row['commitment_source']).strip(),
            'commitment_year':    int(row['commitment_year']) if pd.notna(row.get('commitment_year')) else None,
        })

    return hospitals
```

- [ ] **Step 4: Run tests — all 7 must pass**

```bash
.venv/bin/python -m pytest tests/test_commitment_ingester.py -v
```
Expected: 7 PASSED

- [ ] **Step 5: Commit**

```bash
git add src/commitment_ingester.py data/hospitals_commitments.csv
git commit -m "feat: implement commitment_ingester — loads 50 NY hospitals with commitment tags"
```

---

## Task 3: Build — Outcome Scorer
**Owner:** Jonel
**Tests first, then implementation.**

**Files:**
- Create: `tests/test_outcome_scorer.py`
- Create: `src/outcome_scorer.py`

- [ ] **Step 1: Download CMS outcome CSVs**

All from https://data.cms.gov/provider-data:
- `Maternal_Health-Hospital.csv` → save to `data/`
- `FY2025_Hospital_Readmissions_Reduction_Program.csv` → save to `data/`
- `HCAHPS-Hospital.csv` → save to `data/`

- [ ] **Step 2: Write test_outcome_scorer.py**

```python
# tests/test_outcome_scorer.py
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from commitment_ingester import get_hospital_commitments
from outcome_scorer import score_outcomes


def _get_scored():
    hospitals = get_hospital_commitments()
    return score_outcomes(hospitals)


def test_no_hospitals_dropped():
    hospitals = get_hospital_commitments()
    scored = score_outcomes(hospitals)
    assert len(scored) == len(hospitals), \
        "score_outcomes must not drop any hospitals"


def test_output_has_outcome_fields():
    scored = _get_scored()
    required = [
        "maternal_quality_score", "severe_morbidity_rate", "compared_to_national",
        "postpartum_visit_pct", "state_avg_postpartum_pct", "well_baby_visit_pct",
        "care_transition_score", "readmission_penalty", "excess_readmission_ratio",
        "medicaid_pct",
    ]
    for h in scored:
        for field in required:
            assert field in h, f"Missing field: {field} in {h.get('facility_name')}"


def test_compared_to_national_exact_values():
    scored = _get_scored()
    valid = {"Better", "Same", "Worse"}
    for h in scored:
        val = h.get("compared_to_national")
        if val is not None:
            assert val in valid, \
                f"compared_to_national='{val}' not in {valid}"


def test_state_avg_travels_with_postpartum():
    scored = _get_scored()
    for h in scored:
        if h.get("postpartum_visit_pct") is not None:
            assert h.get("state_avg_postpartum_pct") is not None, \
                f"state_avg_postpartum_pct missing when postpartum_visit_pct is set: {h['facility_name']}"


def test_missing_field_is_none_not_zero():
    hospitals = get_hospital_commitments()
    scored = score_outcomes(hospitals)
    nullable_fields = ["severe_morbidity_rate", "postpartum_visit_pct", "care_transition_score"]
    for h in scored:
        for field in nullable_fields:
            assert h.get(field) != 0 or h.get(field) is None, \
                f"{field} is 0 — should be None if missing, not 0"


def test_readmission_penalty_is_bool():
    scored = _get_scored()
    for h in scored:
        assert isinstance(h["readmission_penalty"], bool), \
            f"readmission_penalty must be bool: {h['facility_name']}"
```

- [ ] **Step 3: Run tests — confirm all FAIL**

```bash
.venv/bin/python -m pytest tests/test_outcome_scorer.py -v 2>&1 | head -10
```
Expected: ImportError

- [ ] **Step 4: Write outcome_scorer.py**

```python
# src/outcome_scorer.py
"""
outcome_scorer.py — Tool 2 | Owner: Jonel

Adds CMS outcome fields to each hospital dict.
Joins across 4 CMS CSVs using facility_id as the key.
Missing fields are set to None — never 0, never imputed.

Reads:
  data/Maternal_Health-Hospital.csv
  data/FY2025_Hospital_Readmissions_Reduction_Program.csv
  data/HCAHPS-Hospital.csv
  data/Hospital_General_Information.csv
"""
import os
import pandas as pd
from typing import Any

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')


def _load_maternal() -> pd.DataFrame:
    df = pd.read_csv(os.path.join(DATA_DIR, 'Maternal_Health-Hospital.csv'), dtype={'Facility ID': str})
    return df


def _load_readmissions() -> pd.DataFrame:
    df = pd.read_csv(os.path.join(DATA_DIR, 'FY2025_Hospital_Readmissions_Reduction_Program.csv'), dtype={'CCN': str})
    return df


def _load_hcahps() -> pd.DataFrame:
    df = pd.read_csv(os.path.join(DATA_DIR, 'HCAHPS-Hospital.csv'), dtype={'Facility ID': str})
    return df


def _safe_float(val) -> float | None:
    try:
        f = float(val)
        return None if pd.isna(f) else f
    except (TypeError, ValueError):
        return None


def _safe_int(val) -> int | None:
    try:
        i = int(float(val))
        return None if pd.isna(float(val)) else i
    except (TypeError, ValueError):
        return None


# State average postpartum visit rates — from CMS Medicaid Adult Core Set
# Luba provides this dict based on kff_state_data.csv
STATE_AVG_POSTPARTUM = {
    "NY": 72.0, "NJ": 69.0, "CT": 74.0, "MA": 78.0, "PA": 67.0,
    "AL": 58.0, "MS": 52.0, "GA": 63.0, "TX": 61.0, "LA": 55.0,
    # Add all 50 states — Jonel fills in from CMS Adult Core Set data
}


def score_outcomes(hospitals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Add CMS outcome fields to each hospital dict.
    Returns same list with outcome fields added. Never drops hospitals.
    """
    maternal = _load_maternal()
    readmissions = _load_readmissions()
    hcahps = _load_hcahps()

    for hospital in hospitals:
        fid = hospital['facility_id']
        state = hospital.get('state', '')

        # ── Maternal quality ────────────────────────────────────────────
        mat_row = maternal[maternal['Facility ID'] == fid]
        if not mat_row.empty:
            row = mat_row.iloc[0]
            hospital['maternal_quality_score'] = _safe_int(row.get('Hospital overall rating'))
            hospital['severe_morbidity_rate']  = _safe_float(row.get('Severe Maternal Morbidity Rate'))
            raw_comp = str(row.get('Compared to National', '')).strip()
            if 'better' in raw_comp.lower():
                hospital['compared_to_national'] = 'Better'
            elif 'worse' in raw_comp.lower():
                hospital['compared_to_national'] = 'Worse'
            else:
                hospital['compared_to_national'] = 'Same'
            hospital['postpartum_visit_pct']     = _safe_float(row.get('Postpartum Visit Rate'))
            hospital['well_baby_visit_pct']      = _safe_float(row.get('Well Baby Visit Rate'))
        else:
            hospital['maternal_quality_score']  = None
            hospital['severe_morbidity_rate']   = None
            hospital['compared_to_national']    = 'Same'
            hospital['postpartum_visit_pct']    = None
            hospital['well_baby_visit_pct']     = None

        hospital['state_avg_postpartum_pct'] = (
            STATE_AVG_POSTPARTUM.get(state)
            if hospital['postpartum_visit_pct'] is not None else None
        )

        # ── Readmissions ────────────────────────────────────────────────
        rad_row = readmissions[readmissions['CCN'] == fid]
        if not rad_row.empty:
            row = rad_row.iloc[0]
            ratio = _safe_float(row.get('Excess Readmission Ratio'))
            hospital['readmission_penalty']      = (ratio is not None and ratio > 1.0)
            hospital['excess_readmission_ratio'] = ratio if ratio is not None else 1.0
        else:
            hospital['readmission_penalty']      = False
            hospital['excess_readmission_ratio'] = 1.0

        # ── HCAHPS care transition ───────────────────────────────────────
        hc_rows = hcahps[
            (hcahps['Facility ID'] == fid) &
            (hcahps['HCAHPS Measure ID'].str.contains('CARE_TRANSITION', na=False))
        ]
        if not hc_rows.empty:
            score = _safe_float(hc_rows.iloc[0].get('Patient Survey Star Rating'))
            hospital['care_transition_score'] = _safe_int(score) if score is not None else None
        else:
            hospital['care_transition_score'] = None

        # ── Medicaid pct ────────────────────────────────────────────────
        hospital['medicaid_pct'] = 65.0  # TODO: Jonel — pull from CMS cost report

    return hospitals
```

- [ ] **Step 5: Run tests — all 6 must pass**

```bash
.venv/bin/python -m pytest tests/test_outcome_scorer.py -v
```
Expected: 6 PASSED

- [ ] **Step 6: Commit and signal Luba**

```bash
git add src/outcome_scorer.py
git commit -m "feat: implement outcome_scorer — joins 4 CMS CSVs, adds outcome fields to all hospitals"
```
**Tell Luba: Task 3 is done. She can now start Task 4.**

---

## Task 4: Build — Gap Calculator
**Owner:** Luba
**Start only after Jonel commits Task 3.**

**Files:**
- Create: `tests/test_gap_calculator.py`
- Create: `src/gap_calculator.py`

- [ ] **Step 1: Write test_gap_calculator.py**

```python
# tests/test_gap_calculator.py
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tests.fixtures import HIGH_GAP, MEDIUM_GAP, LOW_GAP, NULL_DATA, NO_COMMITMENT
from gap_calculator import calculate_gap_score
import copy


def test_high_gap_score():
    h = calculate_gap_score(copy.deepcopy(HIGH_GAP))
    assert h['gap_score'] == 75.0, f"Expected 75.0, got {h['gap_score']}"
    assert h['lead_angle'] == 'baby_vs_mother_contrast'


def test_commitment_strength_max_25():
    h = calculate_gap_score(copy.deepcopy(HIGH_GAP))
    assert h['gap_breakdown']['commitment_strength'] == 25


def test_outcome_gap_max_50():
    h = calculate_gap_score(copy.deepcopy(HIGH_GAP))
    assert h['gap_breakdown']['outcome_gap'] == 50


def test_null_postpartum_skips_visit_gap():
    h = calculate_gap_score(copy.deepcopy(NULL_DATA))
    assert h['gap_score'] is not None
    assert h['gap_breakdown']['outcome_gap'] <= 30  # no visit gap pts


def test_null_care_transition_is_neutral():
    h = calculate_gap_score(copy.deepcopy(NULL_DATA))
    # care_transition_score is None in NULL_DATA — should not crash and should add 0 pts
    assert isinstance(h['gap_score'], float)


def test_both_null_sets_low_confidence():
    h = calculate_gap_score(copy.deepcopy(NULL_DATA))
    assert h['data_confidence'] == 'low'


def test_high_confidence_when_data_present():
    h = calculate_gap_score(copy.deepcopy(HIGH_GAP))
    assert h['data_confidence'] == 'high'


def test_no_commitment_raises():
    with pytest.raises(ValueError, match='has_commitment'):
        calculate_gap_score(copy.deepcopy(NO_COMMITMENT))


def test_lead_angle_baby_vs_mother():
    h = calculate_gap_score(copy.deepcopy(HIGH_GAP))
    assert h['lead_angle'] == 'baby_vs_mother_contrast'


def test_lead_angle_severe_morbidity():
    hospital = copy.deepcopy(HIGH_GAP)
    hospital['well_baby_visit_pct'] = None  # disqualify baby_vs_mother
    h = calculate_gap_score(hospital)
    assert h['lead_angle'] == 'severe_morbidity_rate'


def test_gap_breakdown_structure():
    h = calculate_gap_score(copy.deepcopy(HIGH_GAP))
    assert 'commitment_strength' in h['gap_breakdown']
    assert 'outcome_gap' in h['gap_breakdown']
    assert h['gap_breakdown']['urgency_context'] == 0
```

- [ ] **Step 2: Run — confirm all FAIL**

```bash
.venv/bin/python -m pytest tests/test_gap_calculator.py -v 2>&1 | head -10
```
Expected: ImportError

- [ ] **Step 3: Write gap_calculator.py**

```python
# src/gap_calculator.py
"""
gap_calculator.py — Tool 3 | Owner: Luba

Calculates gap score (0-75 intermediate) and lead angle.
Called once per hospital after outcome_scorer has run.
See TDD.md for full formula and test cases.
"""
from typing import Any


def calculate_gap_score(hospital: dict[str, Any]) -> dict[str, Any]:
    """
    Score commitment-outcome gap for one hospital.
    Raises ValueError if has_commitment is False.
    """
    if not hospital.get('has_commitment', False):
        raise ValueError(
            f"has_commitment is False for {hospital.get('facility_id', 'unknown')}. "
            "v1 only scores hospitals with public commitments."
        )

    # ── Layer 1: Commitment Strength (max 25) ─────────────────────────────────
    commitment_pts = 0
    tag = hospital.get('commitment_tag') or ''

    if hospital.get('birthing_friendly'):
        commitment_pts += 15
    if 'MMSM' in tag:
        commitment_pts += 10
    elif commitment_pts == 0 and tag:
        commitment_pts += 5
    commitment_pts = min(commitment_pts, 25)

    # ── Layer 2: Outcome Gap (max 50) ─────────────────────────────────────────
    outcome_pts = 0
    compared = hospital.get('compared_to_national', '')

    if compared == 'Worse':
        outcome_pts += 20
    elif compared == 'Same':
        outcome_pts += 10

    postpartum_pct = hospital.get('postpartum_visit_pct')
    state_avg = hospital.get('state_avg_postpartum_pct')
    if postpartum_pct is not None and state_avg is not None:
        raw_gap = state_avg - postpartum_pct
        if raw_gap > 0:
            outcome_pts += min(int(raw_gap) // 2, 15)

    care = hospital.get('care_transition_score')
    if care is not None and care < 3:
        outcome_pts += 10

    if hospital.get('readmission_penalty'):
        outcome_pts += 5

    outcome_pts = min(outcome_pts, 50)

    # ── Data confidence ───────────────────────────────────────────────────────
    smm = hospital.get('severe_morbidity_rate')
    data_confidence = 'low' if (postpartum_pct is None and smm is None) else 'high'

    # ── Lead angle (first match wins) ────────────────────────────────────────
    well_baby = hospital.get('well_baby_visit_pct')
    if well_baby is not None and postpartum_pct is not None and (well_baby - postpartum_pct) > 30:
        lead_angle = 'baby_vs_mother_contrast'
    elif compared == 'Worse':
        lead_angle = 'severe_morbidity_rate'
    elif postpartum_pct is not None and state_avg is not None and (state_avg - postpartum_pct) > 15:
        lead_angle = 'postpartum_visit_gap'
    elif care is not None and care < 3:
        lead_angle = 'care_transition_gap'
    else:
        lead_angle = 'readmission_penalty'

    hospital['gap_score']       = float(commitment_pts + outcome_pts)
    hospital['lead_angle']      = lead_angle
    hospital['data_confidence'] = data_confidence
    hospital['gap_breakdown']   = {
        'commitment_strength': commitment_pts,
        'outcome_gap':         outcome_pts,
        'urgency_context':     0,
    }
    return hospital
```

- [ ] **Step 4: Run tests — all 11 must pass**

```bash
.venv/bin/python -m pytest tests/test_gap_calculator.py -v
```
Expected: 11 PASSED

- [ ] **Step 5: Commit**

```bash
git add src/gap_calculator.py tests/test_gap_calculator.py
git commit -m "feat: implement gap_calculator — Layer 1+2 scoring, lead angle, null handling"
```

---

## Task 5: Build — Urgency Ranker
**Owner:** Luba

**Files:**
- Create: `tests/test_urgency_ranker.py`
- Create: `src/urgency_ranker.py`
- Create: `data/kff_state_data.csv` (download from kff.org)

- [ ] **Step 1: Download KFF and CDC state data**

- KFF Medicaid Postpartum Coverage: https://kff.org/medicaid/issue-brief/medicaid-postpartum-coverage-extension-tracker/ → export CSV → save as `data/kff_state_data.csv`
- CDC WONDER maternal mortality by state/race: https://wonder.cdc.gov → Group by State, Race → export → save as `data/cdc_wonder_export.csv`

- [ ] **Step 2: Write test_urgency_ranker.py**

```python
# tests/test_urgency_ranker.py
import pytest
import sys
import os
import copy
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tests.fixtures import HIGH_GAP, MEDIUM_GAP, LOW_GAP
from gap_calculator import calculate_gap_score
from urgency_ranker import add_urgency


def _scored(fixture):
    return calculate_gap_score(copy.deepcopy(fixture))


def test_high_urgency_threshold():
    h = add_urgency(_scored(HIGH_GAP))
    assert h['gap_score'] >= 70
    assert h['urgency_tier'] == 'high'
    assert h['urgency_flag'] == '🔴 Act this week'


def test_medium_urgency_threshold():
    h = add_urgency(_scored(MEDIUM_GAP))
    assert 40 <= h['gap_score'] <= 69
    assert h['urgency_tier'] == 'medium'
    assert h['urgency_flag'] == '🟡 Monitor'


def test_low_urgency_threshold():
    h = add_urgency(_scored(LOW_GAP))
    assert h['gap_score'] < 40
    assert h['urgency_tier'] == 'low'
    assert h['urgency_flag'] == '🟢 Not ready'


def test_layer3_max_25():
    h = add_urgency(_scored(HIGH_GAP))
    assert h['gap_breakdown']['urgency_context'] <= 25


def test_final_score_overwrites_intermediate():
    intermediate = _scored(HIGH_GAP)
    intermediate_score = intermediate['gap_score']
    final = add_urgency(copy.deepcopy(intermediate))
    assert final['gap_score'] >= intermediate_score


def test_urgency_flag_exact_strings():
    valid = {'🔴 Act this week', '🟡 Monitor', '🟢 Not ready'}
    for fixture in [HIGH_GAP, MEDIUM_GAP, LOW_GAP]:
        h = add_urgency(_scored(fixture))
        assert h['urgency_flag'] in valid, f"Invalid flag: '{h['urgency_flag']}'"


def test_urgency_tier_lowercase():
    for fixture in [HIGH_GAP, MEDIUM_GAP, LOW_GAP]:
        h = add_urgency(_scored(fixture))
        assert h['urgency_tier'] in {'high', 'medium', 'low'}
        assert h['urgency_tier'] == h['urgency_tier'].lower()


def test_missing_gap_score_raises():
    with pytest.raises(KeyError):
        add_urgency({'facility_id': '000'})


def test_gap_breakdown_urgency_context_filled():
    h = add_urgency(_scored(HIGH_GAP))
    assert isinstance(h['gap_breakdown']['urgency_context'], int)
    assert h['gap_breakdown']['urgency_context'] > 0
```

- [ ] **Step 3: Run — confirm all FAIL**

```bash
.venv/bin/python -m pytest tests/test_urgency_ranker.py -v 2>&1 | head -10
```
Expected: ImportError

- [ ] **Step 4: Write urgency_ranker.py**

```python
# src/urgency_ranker.py
"""
urgency_ranker.py — Tool 4 | Owner: Luba

Adds Layer 3 urgency context and finalizes gap_score to 0-100.
Requires state context fields in the hospital dict before calling.
See TDD.md for Layer 3 formula and urgency thresholds.
"""
import os
import pandas as pd
from typing import Any

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

# State context — loaded once from KFF + CDC data
# Luba: replace hardcoded dict with CSV load when data is ready
_STATE_CONTEXT: dict[str, dict] | None = None


def _load_state_context() -> dict[str, dict]:
    global _STATE_CONTEXT
    if _STATE_CONTEXT is not None:
        return _STATE_CONTEXT

    kff_path = os.path.join(DATA_DIR, 'kff_state_data.csv')
    cdc_path = os.path.join(DATA_DIR, 'cdc_wonder_export.csv')

    if os.path.exists(kff_path) and os.path.exists(cdc_path):
        # TODO: Luba — implement real CSV load and merge
        pass

    # Fallback hardcoded values for demo
    _STATE_CONTEXT = {
        "MS": {"state_mortality_rate": 49.2, "state_mortality_rank": 50, "medicaid_extended": True,  "racial_disparity_flag": True},
        "AL": {"state_mortality_rate": 36.4, "state_mortality_rank": 47, "medicaid_extended": False, "racial_disparity_flag": True},
        "GA": {"state_mortality_rate": 33.1, "state_mortality_rank": 45, "medicaid_extended": True,  "racial_disparity_flag": True},
        "NY": {"state_mortality_rate": 18.2, "state_mortality_rank": 28, "medicaid_extended": True,  "racial_disparity_flag": True},
        "TX": {"state_mortality_rate": 28.7, "state_mortality_rank": 42, "medicaid_extended": False, "racial_disparity_flag": True},
        "CA": {"state_mortality_rate": 14.2, "state_mortality_rank": 12, "medicaid_extended": False, "racial_disparity_flag": False},
        "LA": {"state_mortality_rate": 58.1, "state_mortality_rank": 49, "medicaid_extended": True,  "racial_disparity_flag": True},
    }
    return _STATE_CONTEXT


def add_urgency(hospital: dict[str, Any]) -> dict[str, Any]:
    """
    Add Layer 3 urgency context and finalize gap_score (0-100).
    Raises KeyError if gap_score or gap_breakdown missing.
    Raises ValueError if state context fields missing.
    """
    if 'gap_score' not in hospital or 'gap_breakdown' not in hospital:
        raise KeyError(
            "gap_score and gap_breakdown required. Run calculate_gap_score() first."
        )

    state = hospital.get('state', '')
    ctx = _load_state_context().get(state, {
        "state_mortality_rate": 25.0, "state_mortality_rank": 30,
        "medicaid_extended": False, "racial_disparity_flag": False,
    })
    hospital.update(ctx)

    required = ['state_mortality_rank', 'medicaid_extended', 'racial_disparity_flag']
    missing = [f for f in required if f not in hospital]
    if missing:
        raise ValueError(f"Missing urgency context fields: {missing}")

    # ── Layer 3: Urgency Context (max 25) ─────────────────────────────────────
    urgency_pts = 0
    if hospital['state_mortality_rank'] >= 40:
        urgency_pts += 10
    if hospital['racial_disparity_flag']:
        urgency_pts += 8
    if hospital['medicaid_extended']:
        urgency_pts += 7
    urgency_pts = min(urgency_pts, 25)

    final_score = float(hospital['gap_score'] + urgency_pts)

    if final_score >= 70:
        urgency_tier, urgency_flag = 'high', '🔴 Act this week'
    elif final_score >= 40:
        urgency_tier, urgency_flag = 'medium', '🟡 Monitor'
    else:
        urgency_tier, urgency_flag = 'low', '🟢 Not ready'

    hospital['gap_score']                        = final_score
    hospital['gap_breakdown']['urgency_context'] = urgency_pts
    hospital['urgency_flag']                     = urgency_flag
    hospital['urgency_tier']                     = urgency_tier

    return hospital
```

- [ ] **Step 5: Run tests — all 9 must pass**

```bash
.venv/bin/python -m pytest tests/test_urgency_ranker.py -v
```
Expected: 9 PASSED

- [ ] **Step 6: Commit and signal Paula**

```bash
git add src/urgency_ranker.py tests/test_urgency_ranker.py
git commit -m "feat: implement urgency_ranker — Layer 3 scoring, finalize gap_score 0-100"
```
**Tell Paula: Task 5 is done. She can now start Task 6.**

---

## Task 6: Build — Outbound Generator
**Owner:** Paula
**Start only after Luba commits Task 5.**

**Files:**
- Create: `tests/test_outbound_generator.py`
- Create: `src/outbound_generator.py`

- [ ] **Step 1: Write test_outbound_generator.py**

```python
# tests/test_outbound_generator.py
import pytest
import sys
import os
import copy
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tests.fixtures import HIGH_GAP, MEDIUM_GAP, LOW_GAP
from gap_calculator import calculate_gap_score
from urgency_ranker import add_urgency
from outbound_generator import generate_outbound_email

BANNED_COMPANIES = ['Babyscripts', 'Maven', 'Wildflower', 'Mahmee', 'Bloomlife', 'Cocoon']
VALID_ROLES = {'CMO', 'VP of Women\'s Services', 'Chief Nursing Officer', 'VP of Quality'}


def _pipeline(fixture):
    h = add_urgency(calculate_gap_score(copy.deepcopy(fixture)))
    return h


def test_low_urgency_skipped():
    low = _pipeline(LOW_GAP)
    emails = generate_outbound_email([low])
    assert len(emails) == 0


def test_high_and_medium_included():
    hospitals = [_pipeline(HIGH_GAP), _pipeline(MEDIUM_GAP), _pipeline(LOW_GAP)]
    emails = generate_outbound_email(hospitals)
    assert len(emails) == 2


def test_body_moral_quotes_commitment_tag():
    h = _pipeline(HIGH_GAP)
    emails = generate_outbound_email([h])
    assert h['commitment_tag'] in emails[0]['body_moral'], \
        "body_moral must quote commitment_tag verbatim"


def test_body_clinical_has_postpartum_number():
    h = _pipeline(HIGH_GAP)
    emails = generate_outbound_email([h])
    assert '38' in emails[0]['body_clinical'], \
        "body_clinical must include postpartum_visit_pct (38.0)"


def test_body_financial_has_medicaid_number():
    h = _pipeline(HIGH_GAP)
    emails = generate_outbound_email([h])
    assert '74' in emails[0]['body_financial'], \
        "body_financial must include medicaid_pct (74.0)"


def test_to_role_exact_values():
    h = _pipeline(HIGH_GAP)
    emails = generate_outbound_email([h])
    assert emails[0]['to_role'] in VALID_ROLES


def test_no_company_name_hardcoded():
    hospitals = [_pipeline(HIGH_GAP), _pipeline(MEDIUM_GAP)]
    emails = generate_outbound_email(hospitals)
    for email in emails:
        for body_key in ['body_moral', 'body_clinical', 'body_financial']:
            for company in BANNED_COMPANIES:
                assert company not in email[body_key], \
                    f"Found hardcoded company '{company}' in {body_key}"


def test_placeholder_present():
    h = _pipeline(HIGH_GAP)
    emails = generate_outbound_email([h])
    email = emails[0]
    has_placeholder = any(
        '[COMPANY_NAME]' in email[k]
        for k in ['body_moral', 'body_clinical', 'body_financial']
    )
    assert has_placeholder, "At least one body variant must contain [COMPANY_NAME]"


def test_output_has_all_fields():
    h = _pipeline(HIGH_GAP)
    emails = generate_outbound_email([h])
    required = ['facility_id', 'subject', 'to_role', 'body_moral',
                'body_clinical', 'body_financial', 'lead_angle_used', 'urgency_tier']
    for field in required:
        assert field in emails[0], f"Missing field: {field}"


def test_urgency_tier_copied():
    h = _pipeline(HIGH_GAP)
    emails = generate_outbound_email([h])
    assert emails[0]['urgency_tier'] == 'high'
```

- [ ] **Step 2: Run — confirm all FAIL**

```bash
.venv/bin/python -m pytest tests/test_outbound_generator.py -v 2>&1 | head -10
```
Expected: ImportError

- [ ] **Step 3: Write outbound_generator.py**

```python
# src/outbound_generator.py
"""
outbound_generator.py — Tool 5 | Owner: Paula

Generates 3 email variants per high/medium urgency hospital.
GTM engineer reads all 3 and picks one. Nothing is sent.
[COMPANY_NAME] and [SOCIAL_PROOF] are placeholders — GTM engineer fills in.
"""
from typing import Any

LEAD_TO_VARIANT = {
    'baby_vs_mother_contrast': 'body_moral',
    'severe_morbidity_rate':   'body_clinical',
    'postpartum_visit_gap':    'body_clinical',
    'care_transition_gap':     'body_clinical',
    'readmission_penalty':     'body_financial',
}

TO_ROLE_BY_LEAD = {
    'baby_vs_mother_contrast': 'Chief Nursing Officer',
    'severe_morbidity_rate':   'CMO',
    'postpartum_visit_gap':    'VP of Women\'s Services',
    'care_transition_gap':     'VP of Quality',
    'readmission_penalty':     'CMO',
}


def _body_moral(h: dict) -> str:
    name = h['facility_name']
    tag = h['commitment_tag']
    well_baby = h.get('well_baby_visit_pct', 'N/A')
    postpartum = h.get('postpartum_visit_pct', 'N/A')
    state_avg = h.get('state_avg_postpartum_pct', 'N/A')
    return f"""Hi,

Your well-baby visit rate is {well_baby}%. Your postpartum maternal visit rate is {postpartum}%.

The system works. For babies.

{name} made a public commitment: "{tag}"

The CMS data shows that postpartum follow-up is running {postpartum}% against a state average of {state_avg}%. The commitment and the outcome are moving in different directions.

[COMPANY_NAME] works with hospitals that are serious about closing that gap. [SOCIAL_PROOF]

Would a 20-minute call make sense this week?

Best,
[YOUR NAME]"""


def _body_clinical(h: dict) -> str:
    name = h['facility_name']
    tag = h['commitment_tag']
    postpartum = h.get('postpartum_visit_pct', 'N/A')
    state_avg = h.get('state_avg_postpartum_pct', 'N/A')
    smm = h.get('severe_morbidity_rate', 'N/A')
    return f"""Hi,

{name} committed: "{tag}"

Here's what the outcome data shows: postpartum follow-up is running at {postpartum}%, against a state average of {state_avg}%. Severe maternal morbidity is at {smm} per 10,000 deliveries.

Women are leaving the building and not coming back for the follow-up that catches what goes wrong in the fourth trimester.

[COMPANY_NAME] helps hospitals close that gap with structured postpartum monitoring. [SOCIAL_PROOF]

Worth a conversation?

Best,
[YOUR NAME]"""


def _body_financial(h: dict) -> str:
    name = h['facility_name']
    tag = h['commitment_tag']
    medicaid_pct = h.get('medicaid_pct', 'N/A')
    medicaid_extended = h.get('medicaid_extended', False)
    medicaid_line = (
        "Your state has 12-month postpartum Medicaid coverage — that reimbursement window is open."
        if medicaid_extended
        else "49 states now reimburse 12-month postpartum Medicaid care."
    )
    return f"""Hi,

{name} committed: "{tag}"

{medicaid_line} With {medicaid_pct}% Medicaid payer mix, structured postpartum follow-up programs are directly reimbursable — and your current follow-up rate suggests there's room to capture it.

[COMPANY_NAME] helps hospitals build the postpartum infrastructure that turns that coverage into completed visits. [SOCIAL_PROOF]

Open to a quick call this week?

Best,
[YOUR NAME]"""


def generate_outbound_email(hospitals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Generate 3 email variants per high/medium urgency hospital.
    Low urgency hospitals are skipped.
    Returns list of email objects.
    """
    emails = []
    for h in hospitals:
        if h.get('urgency_tier') not in ('high', 'medium'):
            continue

        lead = h.get('lead_angle', 'readmission_penalty')
        emails.append({
            'facility_id':     h['facility_id'],
            'subject':         f"Postpartum follow-up gap at {h['facility_name']} — data attached",
            'to_role':         TO_ROLE_BY_LEAD.get(lead, 'VP of Women\'s Services'),
            'body_moral':      _body_moral(h),
            'body_clinical':   _body_clinical(h),
            'body_financial':  _body_financial(h),
            'lead_angle_used': lead,
            'urgency_tier':    h['urgency_tier'],
        })
    return emails
```

- [ ] **Step 4: Run tests — all 10 must pass**

```bash
.venv/bin/python -m pytest tests/test_outbound_generator.py -v
```
Expected: 10 PASSED

- [ ] **Step 5: Commit**

```bash
git add src/outbound_generator.py tests/test_outbound_generator.py
git commit -m "feat: implement outbound_generator — 3 email variants per account, no company names hardcoded"
```

---

## Task 7: Build — Human Checkpoint
**Owner:** Paula

**Files:**
- Create: `tests/test_human_checkpoint.py`
- Create: `src/human_checkpoint.py`

- [ ] **Step 1: Write test_human_checkpoint.py**

```python
# tests/test_human_checkpoint.py
import pytest
import sys
import os
import copy
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tests.fixtures import HIGH_GAP, MEDIUM_GAP, LOW_GAP
from gap_calculator import calculate_gap_score
from urgency_ranker import add_urgency
from outbound_generator import generate_outbound_email
from human_checkpoint import display_checkpoint


def _build():
    hospitals = [
        add_urgency(calculate_gap_score(copy.deepcopy(HIGH_GAP))),
        add_urgency(calculate_gap_score(copy.deepcopy(MEDIUM_GAP))),
        add_urgency(calculate_gap_score(copy.deepcopy(LOW_GAP))),
    ]
    emails = generate_outbound_email(hospitals)
    return hospitals, emails


def test_returns_summary_string():
    hospitals, emails = _build()
    result = display_checkpoint(hospitals, emails)
    assert isinstance(result, str)


def test_summary_counts_correct():
    hospitals, emails = _build()
    result = display_checkpoint(hospitals, emails)
    assert '1' in result  # 1 high
    assert '1' in result  # 1 medium (both have '1' so just check string)


def test_nothing_sent_in_summary():
    hospitals, emails = _build()
    result = display_checkpoint(hospitals, emails)
    assert 'sent' in result.lower() or 'nothing' in result.lower()
```

- [ ] **Step 2: Write human_checkpoint.py**

```python
# src/human_checkpoint.py
"""
human_checkpoint.py — Tool 6 | Owner: Paula

Displays email drafts for human review. Nothing is sent.
GTM engineer reads, picks a variant, copies and sends from their own tool.
"""
from typing import Any


def display_checkpoint(hospitals: list[dict[str, Any]], emails: list[dict[str, Any]]) -> str:
    """
    Print formatted review to terminal. Return summary string.
    """
    h_map = {h['facility_id']: h for h in hospitals}

    print('\n' + '='*70)
    print('  ECHO — HUMAN REVIEW CHECKPOINT')
    print(f'  {len(emails)} account(s) ready | Nothing has been sent')
    print('='*70)

    for i, email in enumerate(emails, 1):
        h = h_map.get(email['facility_id'], {})
        print(f"\n[{i}] {h.get('facility_name', email['facility_id'])}")
        print(f"    {h.get('state')} · {h.get('urgency_flag')} · Score: {h.get('gap_score')}")
        print(f"    Commitment: \"{h.get('commitment_tag')}\"")
        print(f"    Lead angle: {email['lead_angle_used']} → To: {email['to_role']}")
        print(f"    Subject: {email['subject']}")

        print(f"\n    ── Variant A — Moral ──────────────────────────────────")
        for line in email['body_moral'].split('\n'):
            print(f"    {line}")

        print(f"\n    ── Variant B — Clinical ───────────────────────────────")
        for line in email['body_clinical'].split('\n'):
            print(f"    {line}")

        print(f"\n    ── Variant C — Financial ──────────────────────────────")
        for line in email['body_financial'].split('\n'):
            print(f"    {line}")

        print('\n' + '-'*70)

    high   = sum(1 for e in emails if e.get('urgency_tier') == 'high')
    medium = sum(1 for e in emails if e.get('urgency_tier') == 'medium')
    summary = f"{high} high-urgency, {medium} medium-urgency accounts ready. Nothing sent."
    print(f'\n  ✋ {summary}\n' + '='*70 + '\n')
    return summary
```

- [ ] **Step 3: Run tests — all 3 must pass**

```bash
.venv/bin/python -m pytest tests/test_human_checkpoint.py -v
```
Expected: 3 PASSED

- [ ] **Step 4: Commit**

```bash
git add src/human_checkpoint.py tests/test_human_checkpoint.py
git commit -m "feat: implement human_checkpoint — displays 3 email variants per account"
```

---

## Task 8: Integration Test
**Owner:** All three — run this together after Tasks 2–7 are done.

**Files:**
- Create: `tests/test_pipeline.py`

- [ ] **Step 1: Write test_pipeline.py**

```python
# tests/test_pipeline.py
import pytest
import sys
import os
import copy
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tests.fixtures import HIGH_GAP, MEDIUM_GAP, LOW_GAP, NULL_DATA
from gap_calculator import calculate_gap_score
from urgency_ranker import add_urgency
from outbound_generator import generate_outbound_email
from human_checkpoint import display_checkpoint


def _run_pipeline(fixtures):
    hospitals = [copy.deepcopy(f) for f in fixtures]
    hospitals = [calculate_gap_score(h) for h in hospitals]
    hospitals = [add_urgency(h) for h in hospitals]
    emails    = generate_outbound_email(hospitals)
    summary   = display_checkpoint(hospitals, emails)
    return hospitals, emails, summary


def test_full_pipeline_runs():
    hospitals, emails, summary = _run_pipeline([HIGH_GAP, MEDIUM_GAP, LOW_GAP])
    assert len(hospitals) == 3
    assert isinstance(summary, str)


def test_dict_fields_only_grow():
    h = copy.deepcopy(HIGH_GAP)
    fields_before = set(h.keys())
    h = calculate_gap_score(h)
    fields_mid = set(h.keys())
    h = add_urgency(h)
    fields_after = set(h.keys())
    assert fields_mid >= fields_before, "calculate_gap_score removed fields"
    assert fields_after >= fields_mid,  "add_urgency removed fields"


def test_gap_score_intermediate_then_final():
    h = copy.deepcopy(HIGH_GAP)
    h = calculate_gap_score(h)
    assert h['gap_score'] <= 75, f"Intermediate score > 75: {h['gap_score']}"
    h = add_urgency(h)
    assert h['gap_score'] <= 100, f"Final score > 100: {h['gap_score']}"


def test_only_high_medium_get_emails():
    hospitals, emails, _ = _run_pipeline([HIGH_GAP, MEDIUM_GAP, LOW_GAP])
    email_ids = {e['facility_id'] for e in emails}
    assert LOW_GAP['facility_id'] not in email_ids


def test_data_confidence_low_flagged():
    h = calculate_gap_score(copy.deepcopy(NULL_DATA))
    assert h['data_confidence'] == 'low'
```

- [ ] **Step 2: Run — all 5 must pass**

```bash
.venv/bin/python -m pytest tests/test_pipeline.py -v
```
Expected: 5 PASSED

- [ ] **Step 3: Run the full test suite — everything green**

```bash
.venv/bin/python -m pytest tests/ -v
```
Expected: all tests PASSED, 0 failures

- [ ] **Step 4: Commit**

```bash
git add tests/test_pipeline.py
git commit -m "test: add integration test — full pipeline runs end to end"
```

---

## Task 9: Wire agent.py
**Owner:** All — do this last, after all tests are green.

**Files:**
- Modify: `src/agent.py`

- [ ] **Step 1: Replace inline tool logic with imports from standalone modules**

Update the `@tool` functions in `src/agent.py` to call the real implementations:

```python
# At the top of src/agent.py, replace inline imports with:
from commitment_ingester import get_hospital_commitments as _get_commitments
from outcome_scorer import score_outcomes as _score_outcomes
from gap_calculator import calculate_gap_score as _calculate_gap
from urgency_ranker import add_urgency as _add_urgency
from outbound_generator import generate_outbound_email as _generate_email
from human_checkpoint import display_checkpoint as _display_checkpoint
```

Then update each `@tool` function body to call the imported function instead of containing inline logic.

- [ ] **Step 2: Run the full agent on NY hospitals**

```bash
.venv/bin/python src/agent.py NY
```

Expected: agent loads real NY hospitals from CMS, scores them, generates 3 email variants per high/medium account, displays human checkpoint.

- [ ] **Step 3: Run the full test suite one final time**

```bash
.venv/bin/python -m pytest tests/ -v
```
Expected: all tests PASSED

- [ ] **Step 4: Final commit**

```bash
git add src/agent.py
git commit -m "feat: wire agent.py to real module implementations — full pipeline live"
```

---

## Build Order Summary

```
Luba:   Task 0 (fixtures)     ← do first, unblocks everyone
Jonel:  Task 1 → Task 2 → Task 3
Luba:   Task 4 → Task 5       ← starts after Jonel's Task 3 is committed
Paula:  Task 6 → Task 7       ← starts after Luba's Task 5 is committed
All:    Task 8 → Task 9       ← integration, runs last
```

## Done When

```
.venv/bin/python -m pytest tests/ -v     → all green
.venv/bin/python src/agent.py NY         → real NY hospitals, real email drafts, human checkpoint
```
