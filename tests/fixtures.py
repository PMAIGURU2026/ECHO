# tests/fixtures.py
"""
Shared test fixtures for all ECHO tests.
Import these instead of defining your own test hospitals.
Every fixture has all fields needed to run the full pipeline per SCHEMA.md.
"""

HIGH_GAP = {
    # Identity
    "facility_id": "010001", "facility_name": "Test High Gap Hospital",
    "state": "MS", "county": "Hinds",
    "hospital_type": "Acute Care Hospitals",
    "hospital_ownership": "Voluntary non-profit",
    # Commitment
    "has_commitment": True, "birthing_friendly": True,
    "commitment_tag": "CMS recognizes this hospital as Birthing-Friendly.",
    "commitment_source": "CMS", "commitment_year": 2023,
    # Hospital HCAHPS
    "hcahps_discharge_score": 72.0,
    "hcahps_discharge_national_avg": 86.0,
    "hcahps_care_transition_score": 2,
    # State baseline
    "state_postpartum_care_pct": 52.0,
    "compared_to_national": "Worse",
    # State context (Layer 3)
    "state_mortality_rate": 49.2, "state_mortality_rank": 50,
    "medicaid_extended": True, "racial_disparity_flag": True,
}

MEDIUM_GAP = {
    "facility_id": "020002", "facility_name": "Test Medium Gap Hospital",
    "state": "GA", "county": "Fulton",
    "hospital_type": "Acute Care Hospitals",
    "hospital_ownership": "Voluntary non-profit",
    "has_commitment": True, "birthing_friendly": True,
    "commitment_tag": "CMS recognizes this hospital as Birthing-Friendly.",
    "commitment_source": "CMS", "commitment_year": 2023,
    "hcahps_discharge_score": 82.0,
    "hcahps_discharge_national_avg": 86.0,
    "hcahps_care_transition_score": 3,
    "state_postpartum_care_pct": 63.0,
    "compared_to_national": "Same",
    "state_mortality_rate": 33.1, "state_mortality_rank": 45,
    "medicaid_extended": True, "racial_disparity_flag": True,
}

LOW_GAP = {
    "facility_id": "030003", "facility_name": "Test Low Gap Hospital",
    "state": "CA", "county": "San Francisco",
    "hospital_type": "Acute Care Hospitals",
    "hospital_ownership": "Proprietary",
    "has_commitment": True, "birthing_friendly": True,
    "commitment_tag": "CMS recognizes this hospital as Birthing-Friendly.",
    "commitment_source": "CMS", "commitment_year": 2023,
    "hcahps_discharge_score": 90.0,
    "hcahps_discharge_national_avg": 86.0,
    "hcahps_care_transition_score": 4,
    "state_postpartum_care_pct": 78.0,
    "compared_to_national": "Better",
    "state_mortality_rate": 14.2, "state_mortality_rank": 12,
    "medicaid_extended": False, "racial_disparity_flag": False,
}

NULL_DATA = {
    "facility_id": "040004", "facility_name": "Test Null Data Hospital",
    "state": "TX", "county": "Harris",
    "hospital_type": "Acute Care Hospitals",
    "hospital_ownership": "Government",
    "has_commitment": True, "birthing_friendly": True,
    "commitment_tag": "CMS recognizes this hospital as Birthing-Friendly.",
    "commitment_source": "CMS", "commitment_year": 2023,
    "hcahps_discharge_score": None,
    "hcahps_discharge_national_avg": None,
    "hcahps_care_transition_score": None,
    "state_postpartum_care_pct": None,
    "compared_to_national": "Same",
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
    "hcahps_discharge_score": 90.0,
    "hcahps_discharge_national_avg": 86.0,
    "hcahps_care_transition_score": 4,
    "state_postpartum_care_pct": 78.0,
    "compared_to_national": "Better",
    "state_mortality_rate": 14.2, "state_mortality_rank": 12,
    "medicaid_extended": False, "racial_disparity_flag": False,
}
