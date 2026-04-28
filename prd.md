# PRD — ECHO (Maternal Accountability Intelligence Agent)

> Product Requirements Document. Written before code.
> The "what and why." CLAUDE.md will be the "how."

## Problem Statement

**Who is affected:** GTM Engineers and Solutions Engineers at postpartum software companies (remote monitoring, care navigation, fourth trimester platforms) who sell into hospital and health system buyers.

**What's broken:** Hospitals publicly commit to maternal quality improvement through federal programs like the CMS Birthing-Friendly designation, then send women home with a paper pamphlet and a six-week appointment. The fourth trimester is where the system goes silent. GTM Engineers selling postpartum software are walking into hospitals that have made the commitment but don't know the outcomes have not followed. There is no tool that surfaces this gap at the hospital territory level.

**How we know it's real:**
- 2,265 hospitals have earned the CMS Birthing-Friendly designation (CMS Provider Data Catalog, 2025)
- Maternal mortality rate in the US was 17.9 per 100,000 live births in 2024; Black women die at 3x the rate of White women, with the gap widening post-pandemic (NCHS Health E-Stat 113, March 2026; Kamijo et al., Cureus 2025)
- Postpartum visit completion rates vary from 20% to 90% across states (NCQA, FFY 2014 Adult Core Set reporting), demonstrating wide quality variation
- Brooklyn validation sample: 5 of 5 Birthing-Friendly hospitals scored below the national average on HCAHPS discharge communication (the literal fourth trimester handoff metric)
- Maternal health data lives in at least 9 federal and non-federal sources that don't cross-reference each other

## Target User

**Primary user:** GTM Engineer or Solutions Engineer at a postpartum software company (Maven, Pomelo Care, Mahmee, Babyscripts, Midi, Elektra, similar). They work a territory of 30 to 200 hospital accounts. Their day is finite. Their first decision every morning is which accounts deserve outreach today.

**Secondary user:** Sales leadership at the same company who needs visibility into territory health and how the GTM team is prioritizing.

**How they solve this today:** Manually. They use territory lists from CRMs, public news searches, and gut instinct. No one is cross-referencing CMS Birthing-Friendly designations against state-level postpartum outcome data daily. The synthesis work doesn't exist as a tool.

**User needs:**
- As a GTM Engineer, I need a daily list of the 10 hospitals in my territory most worth contacting today, because I cannot manually monitor 200 accounts every morning.
- As a GTM Engineer, I need to see *why* a hospital is on the list so I can decide whether the data justifies the outreach, because pulling the trigger on the wrong account costs a meeting.
- As a GTM Engineer, I need to see source links beneath every claim so I can pressure-test the data before I write the email, because I am the one who has to defend it on the call.
- As a GTM Engineer, I need to override the agent's calls when I have context the data doesn't show, because not every flagged account is the right call today.

## Solution

**One-liner:** ECHO is an agent that finds hospitals where public maternal health commitments don't survive discharge, and arms GTM Engineers with the daily 10 most critical accounts to contact.

**Core user flow:**
1. GTM Engineer opens dashboard → sees Today's Critical 10 ranked by mismatch severity
2. GTM Engineer clicks an account → sees the briefing card with mismatches, supporting commitments, context signals, and confidence
3. GTM Engineer reviews the 10, suppresses any that don't fit, picks call order, picks lead angle, drafts outreach in their own tool

## Feature Scope

### User Journey: GTM Engineer reviews today's critical accounts

**Context:** This is the morning ritual. The GTM Engineer opens ECHO, decides who to call today, and gets out.

**Step 1: Reviewing the daily 10**
- [P0] User can see a ranked list of 10 hospitals scored CRITICAL, HIGH, ELEVATED, or WATCH
- [P0] User can see hospital name, location, CCN identifier, and a one-sentence top mismatch summary per row
- [P0] User can see severity badge, outcome delta vs. state average, and confidence percentage per row
- [P0] User can see the territory toolbar showing the count and source ("New York · 101 hospitals · monitored against CMS Birthing-Friendly registry")
- [P1] User can filter by severity tier
- [P1] User can see a stats strip showing critical mismatches today, high severity count, and average confidence
- [P2] User can export the list to CSV

**Step 2: Drilling into a briefing card**
- [P0] User can click any of the 10 accounts to see a full briefing card
- [P0] User can see hospital metadata: name, location, parent system, CCN, beds and deliveries per year if available
- [P0] User can see each commitment-outcome mismatch with the commitment, the outcome, the recency, and the gap visualization
- [P0] User can see source links beneath every commitment and outcome claim
- [P0] User can see the Birthing-Friendly designation date as the commitment
- [P0] User can see context signals (state postpartum Medicaid coverage, maternity care desert status, recent leadership changes if known)
- [P0] User can see a confidence breakdown per mismatch with a brief explanation of why confidence is reduced when applicable
- [P0] User can see "data unavailable" displayed neutrally with a confidence flag when an outcome metric is missing
- [P1] User can see a judgment call callout flagging context the agent thinks the human should weigh
- [P2] User can see all tracked commitments for the hospital (only Birthing-Friendly designation in v1)

**Step 3: Acting on the daily 10**
- [P0] User can suppress an account from today's list with optional reason
- [P0] User can move accounts up or down in priority
- [P1] User can add an account to a watchlist for tomorrow
- [P2] User can hand off to an external CRM via "Open in [CRM]" button

> **Briefing card field list:** specified by the existing mockup HTML. Mockup will be updated to match v1 scope (NY-only, Birthing-Friendly only, state-level metrics, mismatch lead only). No additional design pass needed.

### Out of Scope (for v1)
- **Outreach drafting.** ECHO does not write the email. The GTM Engineer drafts the outreach in their own tool. v2 may add Anthropic API-generated draft openers.
- **Hospital-level outcome data.** v1 uses state-level aggregates as proxies for postpartum outcomes. v2 may integrate AIM Data Center for hospital-level granularity.
- **Multiple commitment sources.** v1 uses CMS Birthing-Friendly designation only. v2 may add AIM bundle participation, NNPQC PQC membership, Joint Commission Perinatal Care certification, and hospital newsroom press releases.
- **Multiple outreach angles.** v1 leads with commitment-outcome mismatch only. v2 may add cost-of-poor-outcomes, peer benchmarking, and regulatory pressure angles. The architecture supports angle-swapping by reweighting Luba's scoring formula.
- **National territory display.** v1 demos NY-only (101 Birthing-Friendly hospitals). Backend ingests national data and could display all states; the NY filter is a demo choice, not a data limitation.
- **Patient-facing surface.** ECHO never communicates with patients. The agent's only audience is the GTM Engineer.
- **Leapfrog Hospital Survey data.** Licensed data not included in v1.
- **Real-time alerts or sub-daily cadence.** v1 refreshes daily.
- **Customer discovery validation.** No external user interviews in v1 scope. Acknowledged as next-phase work.
- **Visual design mockup as separate deliverable.** Existing mockup HTML serves as spec.

## Data Sources

| Data | Source | Format | Notes |
|------|--------|--------|-------|
| Birthing-Friendly hospital registry | CMS Provider Data Catalog | CSV (free) | 2,265 hospitals, geocoded; filter to NY for v1 demo (101 hospitals) |
| State-level postpartum care visit completion | CMS Medicaid Adult Core Set (PPC-AD) | CSV (free, all 50 states) | Variation 20-90% across states; primary outcome metric |
| State-level all-cause readmissions | CMS Medicaid Adult Core Set (PCR-AD) | CSV (free, all 50 states) | Includes postpartum populations |
| State-level postpartum depression screening | CMS Medicaid Adult Core Set (PDS-AD) | CSV (free, all 50 states) | |
| State-level low-risk cesarean delivery | CMS Medicaid Maternity Core Set (LRCD-AD) | CSV (free, all 50 states) | Via state vital records |
| State-level severe maternal morbidity | CDC WONDER | API/CSV (free) | State and county aggregates |
| State-level maternal mortality | NCHS Health E-Stat 113 (March 2026) | PDF/structured (free) | 2024 data; cite undercount caveat (excludes suicide/overdose) |
| Postpartum Medicaid coverage status | KFF Medicaid Postpartum Coverage Extension Tracker | CSV (free) | All 50 states + DC; updated March 2026 |
| State perinatal quality collaborative status | National Network of PQCs (NNPQC) | Web (free) | State-level membership and funding status |
| Maternity care desert classifications | March of Dimes Peristats | Web/CSV (free) | County-level access deficit data |
| State-level HCAHPS discharge communication | CMS HCAHPS State-level | CSV (free) | "Discussed help after discharge" and "written symptom info" metrics |
| AIM Postpartum Discharge Transition metric definitions | AIM/HRSA template | Excel (free) | Defines metric structure; hospital-level data is access-controlled, v2 only |
| AIM SMM code list | AIM/HRSA | Excel (free) | ICD-10 codes for severe maternal morbidity definition |

> **Adult Core Set source URL:** https://www.medicaid.gov/medicaid/quality-of-care/performance-measurement/adult-and-child-health-care-quality-measures/adult-core-set-reporting-resources

## Success Metrics

| Goal | Signal | Metric | Target |
|------|--------|--------|--------|
| Demo Day usability | Judges understand ECHO's value in under 60 seconds | Time from demo start to "I get it" reaction | Under 60 seconds |
| Architecture defensibility | Interviewer asks "where does the data come from" and gets a clean answer | Number of source links visible per briefing card | At least 1 source link per claim, no exceptions |
| Mismatch logic validity | Birthing-Friendly NY hospitals show measurable outcome gaps | Percent of NY-101 hospitals with at least one defensible mismatch | At least 50% (validation sample showed 5 of 5) |
| Build completion | All 6 tools shipped and integrated | Tools complete and producing output by Demo Day | 6 of 6 |
| Honest framing | Confidence flags appear when data is missing | Percent of briefing cards with at least one confidence indicator | 100% of cards show confidence breakdown |

## ROI Snapshot

| Category | Without ECHO | With ECHO | Delta |
|----------|------------------|----------------|-------|
| **Time** | GTM Engineer spends estimated 2–4 hours per week manually researching territory accounts across CMS, CDC, KFF, March of Dimes | Daily 10 surfaced in seconds; review takes 5–10 minutes | Estimated 1.5–3.5 hours per week per GTM Engineer |
| **Coverage** | Manual review covers maybe 10–20% of territory accounts in detail | Agent monitors 100% of Birthing-Friendly hospitals daily | Full territory coverage vs. partial |
| **Build cost** | — | ~3 weeks build time across 3-person team | Demo Day deliverable |

**One-line pitch:** ECHO replaces manual cross-referencing of fragmented federal maternal health data with a daily ranked list of the 10 hospitals in a GTM Engineer's territory where public commitments aren't matching measured outcomes.

## Stakeholder Concerns

**Sales (the imagined buyer):**
- The buyer at a postpartum software company (VP Sales, Head of GTM) is the same person whose team would use ECHO
- Sales cycle for a B2B internal tool is typically a pilot followed by team rollout — multi-week, not one-call
- Top objections likely: "we already have a CRM for this" (answer: ECHO produces signal CRMs don't, the CRM still owns pipeline), "the data is too narrow" (answer: v1 is intentionally scoped, v2 expands sources), "you haven't talked to a real GTM Engineer" (answer: scope discipline; customer discovery is the next phase)

**Customer Success / Support:**
- Onboarding for a real GTM Engineer would require importing their territory and tuning the urgency formula to their preferences. Out of scope for v1.
- Most common confusion will be "why is this hospital ranked above that one" — the briefing card's confidence breakdown and judgment call callout are designed to answer that

**Operations / Engineering:**
- All v1 data sources are free public CSVs and APIs. No paid licenses. No HIPAA-sensitive data. No PII.
- Daily refresh runs against static or slowly-changing federal data. No real-time pipeline required for v1.
- If CMS or CDC sources change URLs or formats (real risk given proposed FY27 HHS reorganization), the data layer is the only piece that needs updating

**Legal / Compliance:**
- All data sources are public and free to use
- No PII, no patient data, no HIPAA exposure
- Hospital names are public; CCN identifiers are public; outcome data is published by CMS/CDC for public use
- Outreach drafting is left to the human, which means the platform isn't generating claims it can't defend

**Marketing / Communications:**
- One-sentence description: "ECHO finds hospitals where public maternal health commitments aren't matching measured outcomes, and surfaces the daily 10 a GTM Engineer should contact today."
- Visual hook: the briefing card showing a hospital's commitment date next to the outcome gap, with source links beneath every claim
- Sensitivity concern: maternal mortality and racial disparity data carry real weight; the language across the dashboard should be precise and non-sensationalized
- Story arc: hospitals committed publicly → the data shows the commitment isn't translating → ECHO surfaces the gap → the human walks into the room

**End Users:**
- Biggest reason a GTM Engineer would distrust ECHO: opaque scoring. Mitigated by per-mismatch confidence breakdowns and visible source links.
- Ethical risk: ECHO surfacing accounts in a way that feels accusatory toward hospitals. Mitigated by the judgment call callout and by leaving outreach to the human.
- Accessibility: dashboard should meet basic web accessibility standards (semantic HTML, keyboard navigation, sufficient color contrast)

## Open Questions

- [ ] **Honesty stance for v1 limitations.** Do we lean fully into honest framing in the dashboard copy and demo script, or smooth over what's curated vs. automated? Suggestion: lean honest. (Question 9 in team_questions.md)
- [ ] **One-page v2 roadmap doc.** Five PRD sections reference v2 (commitment scope expansion, hospital-level metrics, outreach drafting, alternative angles, customizable cadence). A short v2 roadmap as a v1 deliverable would make the demo more defensible.
- [ ] **Mockup update.** Paula updates the existing mockup HTML this week to match v1 scope. Team reviews together so Jonel can confirm the data layer schema matches what the briefing card expects.
