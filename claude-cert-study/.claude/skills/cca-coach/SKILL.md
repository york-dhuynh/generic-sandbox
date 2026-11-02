---
name: cca-coach
description: Study coach for the Claude Certified Architect exams, Foundations (CCAR-F) first and Professional (CCAR-P) later. Shows the progress dashboard, builds and updates a dated study plan, judges exam readiness, records outside practice-test scores, and picks the next study session. Use whenever the user asks what to study next, how they're doing, whether they're ready to book, wants a study plan or schedule, mentions an exam date, reports a score from another practice site, or asks how to switch from Foundations to Professional.
argument-hint: "[foundations|professional] [plan | ready | log <score> | switch]"
allowed-tools:
  - Read
  - Bash(python3 ${CLAUDE_SKILL_DIR}/../../../scripts/cca.py *)
---

# Study coach

Study root: `${CLAUDE_SKILL_DIR}/../../..` (ROOT). Plan file: `ROOT/progress/plan.md`. Request: `$ARGUMENTS`

Coach like an experienced mentor. Be honest about readiness, specific about the next step, and brief. The user is a working professional, so every session you suggest should fit in 30–60 minutes and have a clear outcome.

## Context to read first
- `ROOT/progress/plan.md`, if it exists: target exam, date, hours per week, language preference, plan.
- `ROOT/CLAUDE.local.md`, if it exists: the learner's background. Use it to skip what they already do daily and to spend time on gaps.
- `python3 ${CLAUDE_SKILL_DIR}/../../../scripts/cca.py stats --exam F` (or `--exam P`).

## Modes

### dashboard (default)
Summarize the stats in 5–8 lines:
- where they stand by domain
- coverage gaps
- confident misses
- days to the exam, if a date is set

Then run `python3 ${CLAUDE_SKILL_DIR}/../../../scripts/cca.py dashboard` and give the path to the refreshed `progress/dashboard.html`. It has the charts the text summary leaves out: objective heatmap, accuracy trend, confidence calibration, rotation calendar, review queue, and journal.

Then recommend **one** next session with exact commands.
- **For Foundations,** the default is `/cca-day`. Name the day, deep dive, and overview from the stats' "Rotation" line, or "day 1: S1 deep dive, S3 overview" if there isn't one yet. Mention the open-question count.
- Recommend something else only when the stats call for it, for example "`/cca-learn 1.5` (20 min)" for an objective that keeps failing transfer checks.
- If there's no plan yet, recommend `plan`.

### plan
1. If there is no plan file, gather the essentials in one go, using AskUserQuestion when available:
   - target exam
   - exam date, or a target week
   - study days per week, and minutes per study day (default 90)
   - Python or TypeScript for labs
   - which areas they already use hands-on (Agent SDK, Claude Code configuration, MCP servers, structured extraction, CI)
2. If there's no diagnostic data, suggest `/cca-quiz diagnostic` first. Build a provisional plan anyway if the user wants one.
3. Write `ROOT/progress/plan.md`:
   - header lines: `Target exam:`, `Exam date:`, `Study days/week:`, `Minutes/day:`, `Lab language:`
   - week-by-week plan: dated, every objective scheduled, each week mixing learn + quiz + lab
   - **Foundations runs on the daily rotation** under "Daily rotation" in `ROOT/scenarios/README.md`:
     - Each study day is `/cca-day`: a deep dive on one scenario, an overview of the next, and a quick review of every scenario started so far.
     - Order: S1 → S3 → S6 → S5 → S4 → S2. One cycle is 6 study days. Map cycles onto calendar weeks using the user's study days per week, and plan at least 2 full cycles before the first mock.
     - Labs sit outside the rotation, on spare days: F1 (S1), F4 (S3), F3 (S6), F5 (S5), F2 (S2/S4). Schedule each after its scenario's first deep dive.
     - Domain weight still decides where extra time goes, so Domain 1 (27%) gets the most `/cca-learn` time.
   - mocks: one at roughly 60% of the timeline and one in the final week. Leave the last 3–5 days for `/cca-quiz review` and the drift table, not new material.
   - a reminder to read the official sample questions in Section 9 of the exam guide during week 1
   - for Professional: flag that Domains 5–7 (35%) are new material, and schedule labs P1 (required by the official prep advice: RAG + eval + observability), P3, and P6
4. Show a compact version of the plan and the first session.

### ready
Run stats and walk through the readiness checklist it prints. Then give a verdict:
- **Ready to book:** every box is checked.
- **Close:** 1–2 gaps, each fixable within a week.
- **Not yet:** list the blockers.

Say plainly that the checklist is a study heuristic. Anthropic publishes no conversion from practice percentage to the 720 scaled score. Remind them of the logistics: register via the Partner Academy, which needs a partner email domain; reschedule at least 24h ahead; bring government photo ID; online-proctored needs a clear desk and webcam.

### log
For an outside practice score, such as the claudecertificationguide.com diagnostic:
```
python3 ${CLAUDE_SKILL_DIR}/../../../scripts/cca.py external --exam F --label "<site and test>" --correct <n> --total <n> [--domain <d>]
```
Note that third-party items vary in quality and alignment, so treat them as a rough signal next to the official-blueprint practice here.

### switch
Moving from Foundations to Professional:
- Read `ROOT/reference/professional-blueprint.md`, especially "Bridges from Foundations".
- Show what carries over and what is new: auth gap analysis, RAG, evaluation practice, governance and compliance, stakeholder and lifecycle work, team enablement.
- Update `Target exam:` in the plan and build the Professional plan with the `plan` steps.
- Mention that Foundations is valid for 12 months, with a free on-time renewal assessment.
