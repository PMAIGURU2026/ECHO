"""
outbound_generator.py — Tool 5 | Owner: Paula

Generates 3 email variants (moral, clinical, financial) per high/medium
urgency hospital. Low urgency hospitals are skipped.

[COMPANY_NAME] and [SOCIAL_PROOF] are placeholders — the GTM engineer
fills these in before sending. Nothing is sent by this tool.
"""
from typing import Any

TO_ROLE_BY_LEAD = {
    "hcahps_care_transition_gap": "CMO",
    "hcahps_discharge_gap": "VP of Women's Services",
    "state_strength_vs_hospital_lag": "VP of Quality",
}


def _subject(h: dict[str, Any]) -> str:
    return f"{h['facility_name']} — postpartum discharge gap vs. Birthing-Friendly commitment"


def _body_moral(h: dict[str, Any]) -> str:
    tag = h["commitment_tag"]
    name = h["facility_name"]
    pct = h.get("discharge_help_pct")
    pct_line = f"Only {pct}% of patients said they got the help they needed after discharge." if pct else ""
    return f"""Hi,

{name} made a public commitment: "{tag}"

{pct_line}

The commitment is on record. The patient experience data tells a different story.

[COMPANY_NAME] works with hospitals that are serious about closing that gap. [SOCIAL_PROOF]

Would a 20-minute call make sense this week?

Best,
[YOUR NAME]"""


def _body_clinical(h: dict[str, Any]) -> str:
    tag = h["commitment_tag"]
    name = h["facility_name"]
    discharge_pct = h.get("discharge_help_pct")
    state_rate = h.get("state_postpartum_visit_rate")
    discharge_star = h.get("discharge_info_star")
    overall_star = h.get("overall_star")

    discharge_line = (
        f"HCAHPS discharge help: {discharge_pct}% of patients received adequate discharge support."
        if discharge_pct else "Discharge help data unavailable."
    )
    star_line = ""
    if discharge_star is not None:
        star_line = f"Discharge information: {discharge_star}-star. Overall experience: {overall_star}-star."
    state_line = (
        f"NY postpartum visit completion: {state_rate}% — the state benchmark the system is measured against."
        if state_rate else ""
    )

    return f"""Hi,

{name} committed: "{tag}"

{star_line}
{discharge_line}
{state_line}

Women are leaving the building without the follow-up that catches what goes wrong in the fourth trimester.

[COMPANY_NAME] helps hospitals close that gap with structured postpartum monitoring. [SOCIAL_PROOF]

Worth a conversation?

Best,
[YOUR NAME]"""


def _body_financial(h: dict[str, Any]) -> str:
    tag = h["commitment_tag"]
    name = h["facility_name"]
    medicaid_extended = h.get("medicaid_extended", False)
    medicaid_line = (
        "New York has 12-month postpartum Medicaid coverage — that reimbursement window is open."
        if medicaid_extended
        else "Federal postpartum Medicaid policy is expanding reimbursement windows across states."
    )

    return f"""Hi,

{name} committed: "{tag}"

{medicaid_line}

Hospitals that close the fourth-trimester gap are better positioned to capture that reimbursement. The ones that don't are leaving both outcomes and revenue on the table.

[COMPANY_NAME] helps hospitals make that follow-up happen. [SOCIAL_PROOF]

Open to a quick call?

Best,
[YOUR NAME]"""


def generate_outbound_email(hospitals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return one email dict per high or medium urgency hospital. Low is skipped."""
    results = []
    for h in hospitals:
        tier = h.get("urgency_tier")
        if tier not in ("high", "medium"):
            continue
        lead = h.get("lead_angle", "state_strength_vs_hospital_lag")
        results.append({
            "facility_id": h["facility_id"],
            "subject": _subject(h),
            "to_role": TO_ROLE_BY_LEAD.get(lead, "VP of Women's Services"),
            "body_moral": _body_moral(h),
            "body_clinical": _body_clinical(h),
            "body_financial": _body_financial(h),
            "lead_angle_used": lead,
            "urgency_tier": tier,
        })
    return results
