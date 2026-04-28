# ECHO — Shared Data Schema
Team Female | Pursuit AI-Native Cycle 3 | April 2026

This is the team's source of truth for the week. If a field name, type, or value is not in this document, it does not exist. Every function in every file must match this schema exactly — no exceptions, no variations.


## Pipeline Order
Jonel (Tools 1+2) → Luba (Tools 3+4) → Paula (Tools 5+6) → Human

Jonel must finish first. Luba cannot score without Jonel's output. Paula cannot generate emails without Luba's scores.


## Within-State Mismatch — Core Logic

ECHO compares hospital-level HCAHPS patient experience scores against state-aggregate postpartum care strength.

> *"NY state achieves [state_postpartum_care_pct]% postpartum care completion. This Birthing-Friendly hospital's HCAHPS discharge communication score is [hcahps_discharge_score - hcahps_discharge_national_avg] points below the national average, suggesting their patients aren't benefiting from the state's overall strength."*

**v1 hospital-level metric is HCAHPS only** (PRD line 87). Hospital-level severe morbidity, hospital postpartum visit %, hospital readmissions, and hospital Medicaid payer mix are explicitly v2.


## The Hospital Dict — Full Schema
One dict per hospital travels through the entire pipeline. Each tool adds fields — nothing is ever removed or renamed.

### After Tool 1 — Commitment Ingester (Jonel)
```python
{
  # ── IDENTITY ──────────────────────────────────────────────────────
  "facility_id":        str,   # CMS hospital ID e.g. "330024"
                               # PRIMARY KEY — used to join all CMS files
  "facility_name":      str,   # Full name e.g. "Mount Sinai Hospital"
  "state":              str,   # 2-letter code e.g. "NY" — ALWAYS uppercase
  "county":             str,   # County name e.g. "New York"
  "hospital_type":      str,   # "Acute Care" / "Critical Access" / other CMS values
  "hospital_ownership": str,   # "Voluntary non-profit" / "Government" / "Proprietary"

  # ── COMMITMENT SIGNALS ────────────────────────────────────────────
  "has_commitment":     bool,  # True if a v1 CMS Birthing-Friendly commitment exists
                               # v1: True for hospitals returned by Tool 1
                               # v2: False for silent-gap hospitals
  "birthing_friendly":  bool,  # CMS birthing-friendly designation YES=True NO=False
  "commitment_tag":     str,   # Specific CMS Birthing-Friendly sentence e.g.
                               # "CMS recognizes this hospital as Birthing-Friendly."
                               # MUST be specific — never a category label
                               # MUST be None if has_commitment=False
  "commitment_source":  str,   # v1: "CMS"
                               # v2 may add "Collaborative" / "ACOG" /
                               # "AWHONN" / "Press Release"
  "commitment_year":    int,   # CMS designation year if available
                               # Use None if year not found
}
```

### After Tool 2 — Outcome Scorer (Jonel)
Adds HCAHPS hospital-level scores + state-level postpartum care baseline.

```python
{
  # ── HOSPITAL-LEVEL HCAHPS (v1's only hospital metric) ─────────────
  "hcahps_discharge_score":         float, # % of patients answering "Yes" to
                                           # "discussed help after discharge"
                                           # e.g. 78.0
                                           # Source: CMS Provider Data Catalog
                                           #   dataset dgck-syfz
  "hcahps_discharge_national_avg":  float, # National average for the same
                                           # HCAHPS measure e.g. 86.0
                                           # Travels with hcahps_discharge_score
                                           # always — needed to compute the gap
  "hcahps_care_transition_score":   int,   # HCAHPS care transition stars 1-5
                                           # LOWER = WORSE
                                           # None if hospital not in HCAHPS file

  # ── STATE-LEVEL BASELINE ──────────────────────────────────────────
  "state_postpartum_care_pct":      float, # State-aggregate postpartum care
                                           # completion % from CMS Adult Core Set
                                           # PPC-AD measure e.g. 72.0 (NY top quartile)
                                           # Source: medicaid.gov core-set-data-dashboard

  # ── COMPARISON SUMMARY ────────────────────────────────────────────
  "compared_to_national":           str,   # "Better" / "Same" / "Worse"
                                           # EXACTLY these three strings
                                           # Derived from hcahps_discharge_score
                                           # vs hcahps_discharge_national_avg:
                                           #   diff > +2 → "Better"
                                           #   diff between -2 and +2 → "Same"
                                           #   diff < -2 → "Worse"
}
```

### After Tool 3 — Gap Calculator (Luba)
Adds gap score fields.

```python
{
  # ── GAP SCORE ─────────────────────────────────────────────────────
  "gap_score":          float, # 0-75 AFTER this tool (intermediate value)
                               # ⚠️ NOT FINAL — urgency_ranker adds up to 25 more pts
                               # Paula must NOT read gap_score until after add_urgency()
  "lead_angle":         str,   # Which mismatch to lead with in outbound email
                               # EXACTLY one of these three strings (v1):
                               # "hcahps_discharge_gap"
                               # "hcahps_care_transition_gap"
                               # "state_strength_vs_hospital_lag"
                               # v2 adds: "silent_gap" (for has_commitment=False)
  "gap_breakdown":      dict,  # Point breakdown for transparency
                               # {
                               #   "commitment_strength": int,  # 0-25
                               #   "outcome_gap": int,          # 0-50
                               #   "urgency_context": int       # 0-25 (added by Tool 4)
                               # }
  "data_confidence":    str,   # "high" or "low"
                               # "low" = both hcahps_discharge_score AND
                               #   hcahps_care_transition_score are None
                               # "high" = at least one HCAHPS field present
                               # Paula: show "data unavailable" on briefing card
                               #   when data_confidence = "low"
}
```

### After Tool 4 — Urgency Ranker (Luba)
Updates gap_score to FINAL value and adds urgency fields.

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
  "state_mortality_rate":   float, # Per 100k live births e.g. 18.2 (NY)
                                   # Source: NCHS Health E-Stat 113
  "state_mortality_rank":   int,   # 1-50, higher = worse state e.g. 28 (NY)
  "medicaid_extended":      bool,  # True if state has 12-month Medicaid postpartum coverage
                                   # Source: KFF Postpartum Coverage Tracker
  "racial_disparity_flag":  bool,  # True if Black MMR > 2x White MMR in this state
}
```

### After Tool 5 — Outbound Generator (Paula)
One email object per hospital, separate from the hospital dict. Each object has **three body variants** generated by OpenRouter API (v1) — the GTM engineer picks one from the dashboard. Nothing is sent automatically.

```python
{
  "facility_id":        str,   # Matches hospital dict — used to link email to account
  "subject":            str,   # Email subject line (same for all 3 variants)
  "to_role":            str,   # Recommended contact role
                               # EXACTLY one of:
                               # "CMO" / "VP of Women's Services" /
                               # "Chief Nursing Officer" / "VP of Quality"

  # ── Three email body variants ─────────────────────────────────────────────
  # Generated by OpenRouter API in v1 (Anthropic API in v2).
  # GTM engineer reads all three on the dashboard and picks the one that fits.
  # All three quote commitment_tag and name a specific lagging HCAHPS metric with a number.
  # Generation is grounded in the hospital dict — model must not invent claims.

  "body_moral":         str,   # Variant A — leads with commitment vs. outcome gap
                               # Opening: "You made a commitment. The HCAHPS data shows a gap."
                               # Hook: quotes commitment_tag, names hcahps_discharge_score delta

  "body_clinical":      str,   # Variant B — leads with patient experience failure
                               # Opening: "Women aren't getting the discharge handoff;
                               #   HCAHPS scores reflect it."
                               # Hook: hcahps_discharge_score vs national avg, with numbers

  "body_financial":     str,   # Variant C — leads with state Medicaid extension opportunity
                               # Opening: "Your state extended postpartum Medicaid coverage.
                               #   That reimbursement window is open."
                               # Hook: medicaid_extended status + state_postpartum_care_pct
                               #   + the hospital's HCAHPS lag

  # ── Metadata ──────────────────────────────────────────────────────────────
  "lead_angle_used":    str,   # Which lead_angle from hospital dict drove subject line
                               # and determines which variant is pre-selected on load
  "urgency_tier":       str,   # Copied from hospital dict — "high"/"medium"/"low"
  "generation_method":  str,   # "openrouter_api" or "cached_fallback"
                               # See "Cached Fallback Trigger" section below
}
```

**Lead angle → default variant mapping** (pre-selects on dashboard load):

| lead_angle | Default variant |
|------------|----------------|
| `hcahps_discharge_gap` | `body_clinical` |
| `hcahps_care_transition_gap` | `body_clinical` |
| `state_strength_vs_hospital_lag` | `body_moral` |

**`state_strength_vs_hospital_lag` copy hook (must appear in body_moral when this lead is used):**

> "Your state's postpartum care rate is [state_postpartum_care_pct]%. Your HCAHPS discharge score is [delta] points below national average. The system built for this community isn't following mothers home."

The GTM engineer can always switch variants manually before copying.


## Cached Fallback Trigger

Paula's `outbound_generator.py` falls back to pre-generated static templates and sets `generation_method = "cached_fallback"` when **either** condition is true:

1. **OpenRouter API call fails** — request timeout, non-200 response, or empty/malformed model output.
2. **Required grounding fields are null in the hospital dict** — any of:
   - `hcahps_discharge_score is None`
   - `state_postpartum_care_pct is None`
   - `commitment_tag is None`

When neither condition is true, `generation_method = "openrouter_api"`.

The cached fallback templates live in `data/email_cache.json`, generated nightly by a script Paula owns. Templates are keyed by `lead_angle` and use string interpolation against whatever fields are present.


## ⚠️ Critical Handoff Note — gap_score
gap_score appears in the hospital dict after Tool 3 AND after Tool 4.

- After Tool 3 (calculate_gap_score): value is 0-75. This is **intermediate**. Do not use.
- After Tool 4 (add_urgency): value is 0-100. This is **final**. Paula reads this.

Paula's Outbound Generator must only consume hospital dicts that have passed through `add_urgency()`. If `urgency_tier` is not present in the dict, `add_urgency()` has not run yet — do not proceed.


## Field Rules — Non-Negotiable
These rules apply to every file, every function, every person:

1. **Field names are exact.** `facility_name` not `hospital_name`. `hcahps_discharge_score` not `hcahps_score`. Copy from this doc, do not type from memory.

2. **State is always 2-letter uppercase.** `"NY"` not `"New York"` not `"ny"`.

3. **`compared_to_national` is always one of exactly three strings.** `"Better"` / `"Same"` / `"Worse"`. Capital first letter. No other values.

4. **`urgency_tier` is always one of exactly three strings.** `"high"` / `"medium"` / `"low"`. Lowercase. Paula's email template branches on this — any variation breaks her code.

5. **`commitment_tag` is a specific CMS Birthing-Friendly sentence or None.** Never an empty string `""`. Never a category like `"has commitment"`. If the CMS designation is unavailable, the value is `None` and `has_commitment` is `False`.

6. **`gap_score` after Tool 3 is intermediate.** Only read `gap_score` after `urgency_tier` is present in the dict.

7. **`generation_method` reflects truth.** If the OpenRouter call succeeded with full grounding, value is `"openrouter_api"`. Otherwise `"cached_fallback"`. No other values.


## Missing Data Handling

CMS data has gaps. `gap_calculator.py` must never crash on `None`. Hospitals are **never skipped** for missing data in v1 — they are scored on what is available and flagged with `data_confidence`.

### Per-field rules

| Field | If missing | Effect on scoring |
|-------|-----------|-------------------|
| `hcahps_discharge_score` | `None` — do not impute | Skip discharge gap calculation in Layer 2 entirely |
| `hcahps_discharge_national_avg` | `None` — do not impute | Same as above (the gap calc requires both) |
| `hcahps_care_transition_score` | `None` — do not impute | Treat as neutral — 0 pts, no penalty |
| `state_postpartum_care_pct` | `None` — do not impute | Skip `state_strength_vs_hospital_lag` lead angle |
| `commitment_year` | `None` — tag still valid | No scoring impact |

### data_confidence field

Output of `gap_calculator.py`. Set based on how much HCAHPS data is available:

- `"low"` — both `hcahps_discharge_score` **and** `hcahps_care_transition_score` are `None`
- `"high"` — at least one of those fields is present

**Paula:** when `data_confidence = "low"`, display `"data unavailable"` on the briefing card instead of the gap score number, and the cached fallback trigger fires for email generation.

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
- Multiple commitment sources beyond CMS Birthing-Friendly designation
- Hospital-level outcome data beyond HCAHPS (severe maternal morbidity per hospital, hospital postpartum visit %, hospital readmissions, hospital Medicaid payer mix)
- Anthropic API (v2 only — v1 uses OpenRouter free tier)
- Silent Gap mode (`has_commitment=False`) — this is v2


## v2 Changes (next phase, do not touch now)
- Add `has_commitment: bool` as a required field for silent-gap hospitals
- Add `"silent_gap"` as a valid `lead_angle` value
- Update Gap Calculator to skip Layer 1 when `has_commitment=False`
- Cap score at 75 for silent-gap hospitals
- Paula adds second email template for silent-gap accounts
- Add additional commitment sources such as AIM participation, NNPQC PQC membership, Joint Commission certification, and hospital press releases
- Swap OpenRouter → Anthropic API for better email quality (Sonnet 4.6 / Opus 4.7 / Haiku 4.5)
- Add hospital-level severe maternal morbidity (AIM Data Center)
- Add hospital-level postpartum visit %, readmissions, Medicaid payer mix from CMS cost report
- Add `disparity_worsening_trend: bool` to urgency context (Layer 3)
  — `True` if the Black/White maternal mortality gap in that state is **widening post-2020**,
  not just high. Source: Kamijo et al., Cureus 2025 — post-pandemic racial disparity trend data.
  A widening trend is a stronger urgency signal than a static gap.
  Will replace or stack with `racial_disparity_flag` in `urgency_ranker.py`.


## File Ownership

| File | Owner | Depends on |
|------|-------|-----------|
| `commitment_ingester.py` | Jonel | CMS Hospital General Information / Birthing-Friendly registry |
| `outcome_scorer.py` | Jonel | Output of `commitment_ingester.py` + HCAHPS CSV + Adult Core Set CSV |
| `gap_calculator.py` | Luba | Output of `outcome_scorer.py` |
| `urgency_ranker.py` | Luba | Output of `gap_calculator.py` + KFF/NCHS CSVs |
| `outbound_generator.py` | Paula | Output of `urgency_ranker.py` (final gap_score only) + OpenRouter API + `data/email_cache.json` |
| `human_checkpoint.py` | Paula | Output of `outbound_generator.py` |
| `kff_state_data.csv` | Luba | Downloaded from kff.org |
| `nchs_mortality_export.csv` | Luba | Downloaded from cdc.gov NCHS |
| `email_cache.json` | Paula | Pre-generated nightly fallback templates |


## Wednesday Deliverables

| Person | Done when |
|--------|----------|
| Jonel | `outcome_scorer.py` runs on real CMS HCAHPS + Adult Core Set CSVs, outputs clean list of 50 NY hospital dicts matching this schema |
| Luba | `gap_calculator.py` + `urgency_ranker.py` run on Jonel's output, produce ranked top 10 with final gap scores |
| Paula | `outbound_generator.py` produces three OpenRouter-generated email variants per top-10 account (with cached fallback), `human_checkpoint.py` displays them clearly |


---
*Last updated: April 2026 — Team Female, Pursuit AI-Native Cycle 3*
*Any schema changes must be agreed by all three team members before implementation.*
