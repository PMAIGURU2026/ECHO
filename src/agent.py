"""
agent.py — ECHO Pipeline Orchestrator
Early Care Handoff Observer | GTM Intelligence Agent for Maternal Health

v1 model: openrouter/openrouter/free via OpenRouter
Run:  python src/agent.py
"""

import os
import sys
import requests
from dotenv import load_dotenv
from strands import Agent, tool
from strands.models.openai import OpenAIModel

load_dotenv()

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

# CMS Provider Data API — no key required
CMS_API = "https://data.cms.gov/provider-data/api/1/datastore/query"
HOSPITAL_GENERAL_INFO_UUID = "xubh-q36u"


# ── Tool 1: Commitment Ingester ───────────────────────────────────────────────

@tool
def get_hospital_commitments(state: str = "MS", limit: int = 5) -> list[dict]:
    """
    Load hospitals that meet the CMS Birthing-Friendly designation from the
    CMS Hospital General Information dataset (live API call — no key required).

    In v1 the birthing-friendly flag IS the commitment signal. Returns hospitals
    with has_commitment=True, birthing_friendly=True, and a commitment_tag derived
    from the CMS designation year.

    Args:
        state: 2-letter uppercase state code to filter by. Default "MS".
        limit: Max hospitals to return. Default 5.

    Returns:
        List of hospital dicts with Tool 1 fields:
        facility_id, facility_name, state, county, hospital_type,
        hospital_ownership, has_commitment, birthing_friendly,
        commitment_tag, commitment_source, commitment_year.
    """
    # GET with a large limit, then filter in Python — avoids POST body format issues
    url = f"{CMS_API}/{HOSPITAL_GENERAL_INFO_UUID}/0"
    params = {"limit": 500}  # fetch enough to find birthing-friendly hospitals per state
    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    all_rows = response.json().get("results", [])

    # Filter to target state + birthing-friendly, then cap at limit
    raw = [
        r for r in all_rows
        if r.get("state", "").upper() == state.upper()
        and r.get("meets_criteria_for_birthing_friendly_designation") == "Y"
    ][:limit]

    hospitals = []
    for row in raw:
        hospitals.append({
            "facility_id":        row.get("facility_id", ""),
            "facility_name":      row.get("facility_name", ""),
            "state":              row.get("state", "").upper(),
            "county":             row.get("countyparish", ""),
            "hospital_type":      row.get("hospital_type", ""),
            "hospital_ownership": row.get("hospital_ownership", ""),
            "has_commitment":     True,
            "birthing_friendly":  row.get("meets_criteria_for_birthing_friendly_designation") == "Y",
            "commitment_tag":     "Meets CMS Birthing-Friendly Hospital Designation criteria",
            "commitment_source":  "CMS",
            "commitment_year":    2023,
        })

    return hospitals


# ── Tool 2: Outcome Scorer (stub — Jonel owns this) ──────────────────────────

@tool
def score_outcomes(hospitals: list[dict]) -> list[dict]:
    """
    Add CMS outcome fields to each hospital dict.
    Owner: Jonel. This is a stub — Jonel fills in real CSV logic.

    Args:
        hospitals: List of hospital dicts from get_hospital_commitments().

    Returns:
        Same list with outcome fields added to each dict.
    """
    for hospital in hospitals:
        hospital.update({
            "maternal_quality_score":   2,
            "severe_morbidity_rate":    125.0,
            "compared_to_national":     "Worse",
            "postpartum_visit_pct":     45.0,
            "state_avg_postpartum_pct": 72.0,
            "well_baby_visit_pct":      91.0,
            "care_transition_score":    2,
            "readmission_penalty":      True,
            "excess_readmission_ratio": 1.08,
            "medicaid_pct":             65.0,
        })
    return hospitals


# ── Tool 3: Gap Calculator (Luba owns this — real logic) ─────────────────────

@tool
def calculate_gap_score(hospital: dict) -> dict:
    """
    Calculate gap score (0-75 intermediate) and lead angle for one hospital.
    Owner: Luba. Contains real scoring logic.

    Args:
        hospital: Single hospital dict with Tool 1+2 fields.

    Returns:
        Same dict with gap_score (0-75), lead_angle, gap_breakdown added.
    """
    if not hospital.get("has_commitment", False):
        raise ValueError(f"has_commitment is False for {hospital.get('facility_id')}. v1 only.")

    # Layer 1: Commitment Strength (max 25)
    commitment_pts = 0
    tag = hospital.get("commitment_tag") or ""
    if hospital.get("birthing_friendly"):
        commitment_pts += 15
    if "MMSM" in tag:
        commitment_pts += 10
    elif commitment_pts == 0 and tag:
        commitment_pts += 5
    commitment_pts = min(commitment_pts, 25)

    # Layer 2: Outcome Gap (max 50)
    outcome_pts = 0
    compared = hospital.get("compared_to_national", "")
    if compared == "Worse":
        outcome_pts += 20
    elif compared == "Same":
        outcome_pts += 10

    postpartum_pct = hospital.get("postpartum_visit_pct")
    state_avg = hospital.get("state_avg_postpartum_pct")
    if postpartum_pct is not None and state_avg is not None:
        raw_gap = state_avg - postpartum_pct
        if raw_gap > 0:
            outcome_pts += min(int(raw_gap) // 2, 15)

    care = hospital.get("care_transition_score")
    if care is not None and care < 3:
        outcome_pts += 10
    if hospital.get("readmission_penalty"):
        outcome_pts += 5
    outcome_pts = min(outcome_pts, 50)

    # Lead angle (first match wins)
    well_baby = hospital.get("well_baby_visit_pct")
    if well_baby is not None and postpartum_pct is not None and (well_baby - postpartum_pct) > 30:
        lead_angle = "baby_vs_mother_contrast"
    elif compared == "Worse":
        lead_angle = "severe_morbidity_rate"
    elif postpartum_pct is not None and state_avg is not None and (state_avg - postpartum_pct) > 15:
        lead_angle = "postpartum_visit_gap"
    elif care is not None and care < 3:
        lead_angle = "care_transition_gap"
    else:
        lead_angle = "readmission_penalty"

    hospital["gap_score"] = float(commitment_pts + outcome_pts)
    hospital["lead_angle"] = lead_angle
    hospital["gap_breakdown"] = {
        "commitment_strength": commitment_pts,
        "outcome_gap": outcome_pts,
        "urgency_context": 0,
    }
    return hospital


# ── Tool 4: Urgency Ranker (Luba owns this — real logic) ─────────────────────

@tool
def add_urgency(hospital: dict) -> dict:
    """
    Add Layer 3 urgency context and finalize gap_score (0-100).
    Owner: Luba. Contains real scoring logic.

    Requires state context fields: state_mortality_rank, medicaid_extended,
    racial_disparity_flag. Uses hardcoded MS state values for v1 demo.

    Args:
        hospital: Single hospital dict after calculate_gap_score().

    Returns:
        Same dict with urgency_flag, urgency_tier, final gap_score (0-100) added.
    """
    # Hardcoded state data for v1 demo — Luba will wire real KFF/CDC CSVs
    STATE_DATA = {
        "MS": {"state_mortality_rate": 49.2, "state_mortality_rank": 50, "medicaid_extended": True,  "racial_disparity_flag": True},
        "AL": {"state_mortality_rate": 36.4, "state_mortality_rank": 47, "medicaid_extended": False, "racial_disparity_flag": True},
        "GA": {"state_mortality_rate": 33.1, "state_mortality_rank": 45, "medicaid_extended": True,  "racial_disparity_flag": True},
        "LA": {"state_mortality_rate": 58.1, "state_mortality_rank": 49, "medicaid_extended": True,  "racial_disparity_flag": True},
        "TX": {"state_mortality_rate": 28.7, "state_mortality_rank": 42, "medicaid_extended": False, "racial_disparity_flag": True},
    }
    state = hospital.get("state", "MS")
    ctx = STATE_DATA.get(state, {"state_mortality_rate": 25.0, "state_mortality_rank": 30, "medicaid_extended": False, "racial_disparity_flag": False})

    hospital.update(ctx)

    urgency_pts = 0
    if ctx["state_mortality_rank"] >= 40:
        urgency_pts += 10
    if ctx["racial_disparity_flag"]:
        urgency_pts += 8
    if ctx["medicaid_extended"]:
        urgency_pts += 7
    urgency_pts = min(urgency_pts, 25)

    final_score = float(hospital["gap_score"] + urgency_pts)

    if final_score >= 70:
        urgency_tier, urgency_flag = "high", "🔴 Act this week"
    elif final_score >= 40:
        urgency_tier, urgency_flag = "medium", "🟡 Monitor"
    else:
        urgency_tier, urgency_flag = "low", "🟢 Not ready"

    hospital["gap_score"] = final_score
    hospital["gap_breakdown"]["urgency_context"] = urgency_pts
    hospital["urgency_flag"] = urgency_flag
    hospital["urgency_tier"] = urgency_tier
    return hospital


# ── Tool 5: Outbound Generator (stub — Paula owns this) ──────────────────────

@tool
def generate_outbound_email(hospitals: list[dict]) -> list[dict]:
    """
    Generate one email object per high/medium urgency hospital.
    Owner: Paula. This is a stub — Paula fills in real template logic.

    Args:
        hospitals: List of hospital dicts after add_urgency().

    Returns:
        List of email dicts for high/medium urgency accounts only.
    """
    emails = []
    for h in hospitals:
        if h.get("urgency_tier") not in ("high", "medium"):
            continue
        emails.append({
            "facility_id":     h["facility_id"],
            "subject":         f"[STUB] Postpartum gap at {h['facility_name']}",
            "to_role":         "VP of Women's Services",
            "body":            (
                f"[Paula fills this in]\n"
                f"Commitment: {h.get('commitment_tag')}\n"
                f"Postpartum visit rate: {h.get('postpartum_visit_pct')}% "
                f"(state avg: {h.get('state_avg_postpartum_pct')}%)\n"
                f"Lead angle: {h.get('lead_angle')}\n"
                f"Gap score: {h.get('gap_score')}"
            ),
            "lead_angle_used": h.get("lead_angle"),
            "urgency_tier":    h.get("urgency_tier"),
        })
    return emails


# ── Tool 6: Human Checkpoint (stub — Paula owns this) ────────────────────────

@tool
def display_checkpoint(hospitals: list[dict], emails: list[dict]) -> str:
    """
    Display all emails for human review. Nothing is sent automatically.
    Owner: Paula. This stub prints a formatted review to the terminal.

    Args:
        hospitals: All hospital dicts from the pipeline.
        emails:    Email objects from generate_outbound_email().

    Returns:
        Summary string of accounts ready for review.
    """
    h_map = {h["facility_id"]: h for h in hospitals}
    print("\n" + "="*65)
    print("  ECHO — HUMAN REVIEW CHECKPOINT")
    print(f"  {len(emails)} account(s) ready | Nothing has been sent")
    print("="*65)
    for i, email in enumerate(emails, 1):
        h = h_map.get(email["facility_id"], {})
        print(f"\n[{i}] {h.get('facility_name', email['facility_id'])}")
        print(f"    State: {h.get('state')} | {h.get('urgency_flag')} | Score: {h.get('gap_score')}")
        print(f"    Lead:  {email['lead_angle_used']} → To: {email['to_role']}")
        print(f"    Subj:  {email['subject']}")
        print(f"\n{email['body']}")
        print("\n" + "-"*65)
    high = sum(1 for e in emails if e.get("urgency_tier") == "high")
    med  = sum(1 for e in emails if e.get("urgency_tier") == "medium")
    summary = f"✋ {high} high-urgency, {med} medium-urgency accounts ready. Nothing sent."
    print(f"\n  {summary}\n" + "="*65 + "\n")
    return summary


# ── Agent Setup ───────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are ECHO, an Early Care Handoff Observer — a GTM intelligence agent for
maternal health software companies.

Run the full 6-tool pipeline in this exact order:
1. get_hospital_commitments — load hospitals with CMS birthing-friendly commitment data
2. score_outcomes — add CMS outcome fields to each hospital
3. calculate_gap_score — compute gap score + lead angle for EACH hospital (call once per hospital)
4. add_urgency — finalize gap_score and set urgency tier for EACH hospital
5. generate_outbound_email — create email drafts for high and medium urgency accounts
6. display_checkpoint — display all emails for human review

Rules:
- gap_score after step 3 is intermediate (0-75). Only read it after step 4 (urgency_tier present).
- Only generate emails for urgency_tier "high" or "medium".
- Nothing is ever sent without human review at step 6.
- If has_commitment is False, skip that hospital (v2 feature).

After the checkpoint, report how many high vs medium urgency accounts were found.
"""


def run_echo(state: str = "MS", limit: int = 3):
    """Run the full ECHO pipeline for a given state."""
    print("🤰 ECHO — Early Care Handoff Observer")
    print("   GTM Intelligence Agent | Maternal Health | v1")
    print("-" * 65)

    if not OPENROUTER_API_KEY:
        # No LLM key — run pipeline directly to show real tool output
        print("⚠  OPENROUTER_API_KEY not set. Running pipeline directly (no LLM orchestration).\n")
        print(f"Fetching CMS birthing-friendly hospitals in {state}...\n")

        hospitals = get_hospital_commitments._tool_func(state=state, limit=limit)
        print(f"Tool 1 returned {len(hospitals)} hospital(s):")
        for h in hospitals:
            print(f"  • {h['facility_id']} — {h['facility_name']} ({h['state']}) | birthing_friendly={h['birthing_friendly']}")
        print()

        hospitals = score_outcomes._tool_func(hospitals)
        for h in hospitals:
            h = calculate_gap_score._tool_func(h)
            h = add_urgency._tool_func(h)
        emails = generate_outbound_email._tool_func(hospitals)
        display_checkpoint._tool_func(hospitals, emails)

        print("\n✅ Agent(model=model, tools=[...]) is instantiated below.")
        print("   Set OPENROUTER_API_KEY in .env to enable full LLM orchestration.\n")

    # Agent is always instantiated regardless of key
    model = OpenAIModel(
        client_args={
            "api_key": OPENROUTER_API_KEY or "no-key",
            "base_url": "https://openrouter.ai/api/v1",
        },
        model_id=os.environ.get("OPENROUTER_MODEL", "tencent/hy3-preview:free"),
    )

    agent = Agent(
        model=model,
        tools=[
            get_hospital_commitments,
            score_outcomes,
            calculate_gap_score,
            add_urgency,
            generate_outbound_email,
            display_checkpoint,
        ],
        system_prompt=SYSTEM_PROMPT,
    )
    print(f"Agent instantiated: {agent}")

    if OPENROUTER_API_KEY:
        print(f"\nRunning agent with OpenRouter (state={state}, limit={limit})...\n")
        response = agent(
            f"Run the full ECHO pipeline for {limit} birthing-friendly hospitals in {state}. "
            "Load commitments, score outcomes, calculate gaps, rank urgency, generate emails, then display the checkpoint."
        )
        print("\nAgent response:", response)


if __name__ == "__main__":
    state = sys.argv[1] if len(sys.argv) > 1 else "MS"
    run_echo(state=state)
