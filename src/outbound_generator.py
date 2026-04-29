"""
outbound_generator.py — Tool 5 | Owner: Paula

Generates 3 email variants (moral, clinical, financial) per high/medium
urgency hospital. Low urgency and low data_confidence hospitals are skipped.

generation_method is "openrouter_api" when OpenRouter succeeds;
"cached_fallback" when commitment_tag is None or the API call fails.

[COMPANY_NAME] and [SOCIAL_PROOF] are placeholders — the GTM engineer
fills these in before sending. Nothing is sent by this tool.
"""
import json
import os
from typing import Any

try:
    import requests as _requests
    _REQUESTS_AVAILABLE = True
except ImportError:
    _REQUESTS_AVAILABLE = False

_OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY", "")

TO_ROLE_BY_LEAD = {
    "hcahps_care_transition_gap": "CMO",
    "hcahps_discharge_gap": "VP of Women's Services",
    "state_strength_vs_hospital_lag": "VP of Quality",
}


def _subject(h: dict[str, Any]) -> str:
    return f"{h['facility_name']} — postpartum discharge gap vs. Birthing-Friendly commitment"


def _body_moral(h: dict[str, Any]) -> str:
    tag = h.get("commitment_tag") or "a CMS Birthing-Friendly commitment"
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
    tag = h.get("commitment_tag") or "a CMS Birthing-Friendly commitment"
    name = h["facility_name"]
    state = h.get("state", "")
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
        f"{state} postpartum visit completion: {state_rate}% — the state benchmark the system is measured against."
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
    tag = h.get("commitment_tag") or "a CMS Birthing-Friendly commitment"
    name = h["facility_name"]
    state = h.get("state", "")
    medicaid_extended = h.get("medicaid_extended", False)
    medicaid_line = (
        f"{state} has 12-month postpartum Medicaid coverage — that reimbursement window is open."
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


def _call_openrouter(h: dict[str, Any]) -> tuple[str, str, str]:
    """Call OpenRouter to generate personalized email bodies. Raises on failure."""
    tag = h.get("commitment_tag")
    name = h["facility_name"]
    state = h.get("state", "")
    discharge_pct = h.get("discharge_help_pct")
    state_rate = h.get("state_postpartum_visit_rate")
    discharge_star = h.get("discharge_info_star")
    overall_star = h.get("overall_star")
    medicaid_extended = h.get("medicaid_extended", False)
    lead = h.get("lead_angle", "state_strength_vs_hospital_lag")

    prompt = f"""Generate three cold email variants for a maternal health platform selling to hospital leadership.

Hospital: {name} ({state})
Commitment: "{tag}"
Lead angle: {lead}
HCAHPS discharge help: {discharge_pct}%
HCAHPS discharge star: {discharge_star}/5
HCAHPS overall star: {overall_star}/5
State postpartum visit rate: {state_rate}%
Medicaid extended (12-month): {medicaid_extended}

Write three variants as JSON with keys body_moral, body_clinical, body_financial.

Rules:
- Each email must include [COMPANY_NAME] and [SOCIAL_PROOF] placeholders
- Do not name any competitor companies
- Include specific numbers from the data above
- Keep each under 150 words
- Start each with "Hi,"

Return only valid JSON."""

    resp = _requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {_OPENROUTER_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "anthropic/claude-haiku",
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=15,
    )
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"]
    data = json.loads(content)
    return data["body_moral"], data["body_clinical"], data["body_financial"]


def generate_outbound_email(hospitals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return one email dict per high/medium urgency, high data_confidence hospital."""
    results = []
    for h in hospitals:
        if h.get("data_confidence") == "low":
            continue
        tier = h.get("urgency_tier")
        if tier not in ("high", "medium"):
            continue

        tag = h.get("commitment_tag")
        generation_method = "cached_fallback"
        body_moral = body_clinical = body_financial = None

        if tag and _OPENROUTER_KEY and _REQUESTS_AVAILABLE:
            try:
                body_moral, body_clinical, body_financial = _call_openrouter(h)
                generation_method = "openrouter_api"
            except Exception:
                pass

        if body_moral is None:
            body_moral = _body_moral(h)
            body_clinical = _body_clinical(h)
            body_financial = _body_financial(h)

        lead = h.get("lead_angle", "state_strength_vs_hospital_lag")
        results.append({
            "facility_id": h["facility_id"],
            "subject": _subject(h),
            "to_role": TO_ROLE_BY_LEAD.get(lead, "VP of Women's Services"),
            "body_moral": body_moral,
            "body_clinical": body_clinical,
            "body_financial": body_financial,
            "lead_angle_used": lead,
            "urgency_tier": tier,
            "generation_method": generation_method,
        })
    return results
