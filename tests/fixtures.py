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
