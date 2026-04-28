# tests/test_outbound_generator.py
import copy
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tests.fixtures import HIGH_GAP, MEDIUM_GAP, LOW_GAP, NULL_DATA
from src.gap_calculator import calculate_gap_score
from src.urgency_ranker import add_urgency
from src.outbound_generator import generate_outbound_email

BANNED_COMPANIES = ["Babyscripts", "Maven", "Wildflower", "Mahmee", "Bloomlife", "Cocoon"]
VALID_ROLES = {"CMO", "VP of Women's Services", "Chief Nursing Officer", "VP of Quality"}
BODY_KEYS = ["body_moral", "body_clinical", "body_financial"]
REQUIRED_FIELDS = [
    "facility_id", "subject", "to_role",
    "body_moral", "body_clinical", "body_financial",
    "lead_angle_used", "urgency_tier",
]


def _run(fixture):
    return add_urgency(calculate_gap_score(copy.deepcopy(fixture)))


# ── filtering ──────────────────────────────────────────────────────────────────

def test_low_urgency_skipped():
    emails = generate_outbound_email([_run(LOW_GAP)])
    assert len(emails) == 0


def test_high_and_medium_included():
    emails = generate_outbound_email([_run(HIGH_GAP), _run(MEDIUM_GAP), _run(LOW_GAP)])
    assert len(emails) == 2


def test_empty_list_returns_empty():
    assert generate_outbound_email([]) == []


# ── output shape ───────────────────────────────────────────────────────────────

def test_output_has_all_fields():
    email = generate_outbound_email([_run(HIGH_GAP)])[0]
    for field in REQUIRED_FIELDS:
        assert field in email, f"Missing field: {field}"


def test_facility_id_copied():
    email = generate_outbound_email([_run(HIGH_GAP)])[0]
    assert email["facility_id"] == HIGH_GAP["facility_id"]


def test_urgency_tier_copied():
    email = generate_outbound_email([_run(HIGH_GAP)])[0]
    assert email["urgency_tier"] == "high"


def test_lead_angle_used_matches_pipeline():
    h = _run(HIGH_GAP)
    email = generate_outbound_email([h])[0]
    assert email["lead_angle_used"] == h["lead_angle"]


# ── body_moral ─────────────────────────────────────────────────────────────────

def test_body_moral_quotes_commitment_tag():
    h = _run(HIGH_GAP)
    email = generate_outbound_email([h])[0]
    assert HIGH_GAP["commitment_tag"] in email["body_moral"], \
        "body_moral must quote commitment_tag verbatim"


def test_body_moral_medium_quotes_commitment_tag():
    h = _run(MEDIUM_GAP)
    email = generate_outbound_email([h])[0]
    assert MEDIUM_GAP["commitment_tag"] in email["body_moral"]


# ── body_clinical ──────────────────────────────────────────────────────────────

def test_body_clinical_has_discharge_help_pct():
    # HIGH_GAP discharge_help_pct = 62.0
    email = generate_outbound_email([_run(HIGH_GAP)])[0]
    assert "62" in email["body_clinical"], \
        "body_clinical must include discharge_help_pct (62.0)"


def test_body_clinical_has_state_postpartum_rate():
    # state_postpartum_visit_rate = 82.4 for all fixtures
    email = generate_outbound_email([_run(HIGH_GAP)])[0]
    assert "82" in email["body_clinical"], \
        "body_clinical must reference state_postpartum_visit_rate (82.4)"


# ── body_financial ─────────────────────────────────────────────────────────────

def test_body_financial_references_medicaid():
    email = generate_outbound_email([_run(HIGH_GAP)])[0]
    body = email["body_financial"].lower()
    assert "medicaid" in body, "body_financial must reference Medicaid coverage"


def test_body_financial_extended_coverage_line():
    # HIGH_GAP has medicaid_extended = True
    email = generate_outbound_email([_run(HIGH_GAP)])[0]
    assert "12-month" in email["body_financial"] or "12 month" in email["body_financial"], \
        "body_financial should mention 12-month Medicaid coverage when medicaid_extended is True"


# ── to_role ────────────────────────────────────────────────────────────────────

def test_to_role_is_valid():
    email = generate_outbound_email([_run(HIGH_GAP)])[0]
    assert email["to_role"] in VALID_ROLES


def test_to_role_valid_for_medium():
    email = generate_outbound_email([_run(MEDIUM_GAP)])[0]
    assert email["to_role"] in VALID_ROLES


# ── placeholder hygiene ────────────────────────────────────────────────────────

def test_no_company_name_hardcoded():
    emails = generate_outbound_email([_run(HIGH_GAP), _run(MEDIUM_GAP)])
    for email in emails:
        for key in BODY_KEYS:
            for company in BANNED_COMPANIES:
                assert company not in email[key], \
                    f"Hardcoded company '{company}' found in {key}"


def test_company_name_placeholder_present():
    email = generate_outbound_email([_run(HIGH_GAP)])[0]
    has_placeholder = any("[COMPANY_NAME]" in email[k] for k in BODY_KEYS)
    assert has_placeholder, "At least one body variant must contain [COMPANY_NAME]"


# ── null data ──────────────────────────────────────────────────────────────────

def test_null_data_does_not_crash():
    # NULL_DATA has no HCAHPS stars — should still produce an email if tier qualifies
    h = _run(NULL_DATA)
    emails = generate_outbound_email([h])
    # just confirm it runs without error — tier determines inclusion
    assert isinstance(emails, list)
