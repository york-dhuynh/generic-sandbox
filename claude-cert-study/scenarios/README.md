# Scenario study guide (CCAR-F)

Depth first: take one scenario at a time, the way the exam presents it, and go all the way down before moving on.

1. Sit the scenario's block cold.
2. Find out what you got right.
3. For every miss and every guess, work backwards from the correct answer until you can explain why it wins and predict the other questions the exam could build from the same rule.

## Why scenarios

- **Every Foundations item sits inside a scenario.** The exam draws 4 of these 6 at random and asks about 15 items in each. Any one scenario has a two-in-three chance of appearing, so none of them can be skipped.
- **The scenario frame decides answers.** Each frame states a constraint that rules out otherwise reasonable options:
  - S1: "80%+ first-contact resolution while knowing when to escalate"
  - S5: "minimize false positives"
  - S6: "handle edge cases gracefully"
- **The score is still by domain.** The guide weights domains, not scenarios, and each scenario mixes two or three domains. Study by scenario and keep score by domain. `python3 scripts/cca.py stats --exam F` shows both.

## The loop, for each scenario

| Step | What you do | Where |
|---|---|---|
| 1. Sit the block | Read the frame and answer 10 items cold, about 2 minutes each. Write a letter plus H/M/L confidence. No docs. | `exam.md` |
| 2. Score | Check against the key table. | top of `answers.md` |
| 3. Reverse-engineer | For every miss **and every guess**, work through the six questions below. | `answers.md`, one entry per item |
| 4. Generate the family | Before reading the three listed variants, write your own: the same rule in a new setting, a flipped condition, and the neighboring objective. | `answers.md` "Other ways…" |
| 5. Prove transfer | Answer one *fresh* question per miss that tests the same rule in a situation you haven't seen. | `/cca-scenario` writes these |
| 6. Debrief | Read the scenario playbook (frame phrases, design sketch, question families, traps). | end of `answers.md` |

**The six reverse-engineering questions** (step 3):
1. **Question type.** What is it asking for: root cause, first step, most effective, most reliable, where does it go, or which design?
2. **The clue.** Which words in the stem or frame point to the key? Quote them.
3. **Why the key.** Which principle makes it right *here*?
4. **Why each distractor.** Which misconception would pick it? Be honest about which one you held.
5. **The rule.** One line you'd carry into the exam.
6. **Flip it.** Change one fact in the stem. Which option wins now?

Step 6 is how you find the other questions the exam could ask. Most exam items are the same few rules with one condition changed.

**If you miss the transfer question too**, the gap is the concept, not the item. Run `/cca-learn <objective>`, then come back.

## Daily rotation: two scenarios a day

Each study day has three parts, in this order. `/cca-day` runs them and keeps track of where you are.

| Part | Time on a 90-minute day | What happens |
|---|---|---|
| 1. Deep dive | the rest, about 60–70 min | Today's scenario, through the loop above, as far as the time goes |
| 2. Overview | 15 min | Tomorrow's scenario as a map. You see the frame, what it puts in play, and the question families. No items and no answers, so tomorrow's block is still a cold read. You leave with 3 pre-questions |
| 3. Quick review | about 3 min per scenario | Every scenario you've started, up to 3 questions each, mixed together |

| Study day | Deep dive | Overview | Quick review |
|---|---|---|---|
| 1 | S1 | S3 | S1, S3 |
| 2 | S3 | S6 | S1, S3, S6 |
| 3 | S6 | S5 | adds S5 |
| 4 | S5 | S4 | adds S4 |
| 5 | S4 | S2 | all six |
| 6 | S2 | – | all six |
| 7 | S1 | – | all six |
| 8 | S3 | – | all six |

From day 7 on, the deep dive keeps rotating in the same order and every day reviews all six. A study day is a day you actually study, so if you skip a calendar day, the rotation waits for you.

**What a deep dive leaves you with.** You won't cover everything, and that's fine. When time is up, everything you touched ends up in one of three places:
- **Worked back:** every miss or guess you finished becomes a recall question in review.
- **Open question:** every item you didn't reach, and anything still fuzzy, becomes a specific question. It names the situation, asks for a decision or a reason, and can be answered in a sentence or two. "MCP errors" isn't one. "S1, 19 tools after connecting an ops server: scope the tools or rewrite the descriptions first, and what in the stem decides it?" is.
- **Pre-question settled:** yesterday's overview questions get answered in the wrap-up, or become open questions.

Open questions come up in quick review the next day, which is your quick chance at them. The items you didn't reach also open that scenario's next deep dive, six study days later, which is their dedicated day. The current list is always in `progress/notebook.md`, without answers, so you can keep thinking about them between sessions.

**How the review stays quick.** Each review question moves through three steps:
1. Right → it comes back the next day.
2. Right again → it comes back a week later.
3. Right a third time → it's solid and leaves the queue.

Wrong at any step sends it back to daily. Each scenario gets at most 3 questions a day, oldest first, so a missed day doesn't snowball. "Right" means you stated the rule and why it wins, not just which option.

**Time.** `/cca-day 60` gives you a 60-minute day, and the deep dive absorbs the cut. If the deep-dive time ends while you're mid-block, finish the block (it needs every answer to score), then wrap up.

**Labs** sit outside the rotation. Do one on a spare day, after its scenario's first deep dive. The Order table below pairs each lab with its scenario.

## With Claude, or on your own

- **On the daily rotation:** `/cca-day`. It works out the day, then runs the deep dive (through `/cca-scenario`), the overview, and the review. `/cca-day plan` shows the day without starting it. `/cca-day questions` goes through what you're carrying.
- **One scenario at a time:** `/cca-scenario S1`. Claude runs the block under exam conditions, scores it, and logs it. It then walks you back through each miss, either explaining it or letting you try first (your choice), and writes a fresh transfer question per miss. `/cca-scenario next` picks the scenario for you. `/cca-scenario status` shows progress.
- **On your own:** open `exam.md`, write your answers down, then open `answers.md`. Results aren't logged this way. Run the block through `/cca-scenario` if you want it on the dashboard.
- **After a block is done:** the fixed items are now familiar, so `/cca-scenario S1 fresh` generates a new 10-item block for the same scenario, weighted toward your weak objectives.

## Order

| # | Scenario | Main domains | Items | Official samples | Lab | Why this position |
|---|---|---|---|---|---|---|
| 1 | [S1 Customer Support Resolution Agent](S1-customer-support/) | 1, 2, 5 | 10 | 3 | F1 | Domain 1 core: loops, hooks, enforcement, escalation |
| 2 | [S3 Multi-Agent Research System](S3-multi-agent-research/) | 1, 2, 5 | 10 | 3 | F4 | Domain 1 core: coordinator, subagents, context passing |
| 3 | [S6 Structured Data Extraction](S6-structured-extraction/) | 4, 5 | 10 | none | F3 | Domain 4 core: schemas, validation, batches |
| 4 | [S5 Claude Code for CI](S5-ci-cd/) | 3, 4 | 10 | 3 | F5 | Domains 3 and 4: headless runs, review prompts |
| 5 | [S4 Developer Productivity](S4-developer-productivity/) | 2, 3, 1 | 10 | none | F2 (partly) | Agent SDK + built-ins + MCP. Easy to mistake for a Claude Code scenario |
| 6 | [S2 Code Generation with Claude Code](S2-code-generation/) | 3, 5 | 10 | 3 | F2 | Closest to daily use, so it goes last, but don't skip it |

The order puts the biggest domain and the likeliest gaps first. Doing the lab right after its scenario block works well: the block shows you what you don't know, and the lab makes it stick.

## About the items

- **The official samples** (Q8–Q10 in S1, S2, S3, S5) are reproduced from the CCAR-F exam guide v1.0, Section 9, with their official keys. They are the closest thing to real exam items, so weigh them highest.
  - The guide keys 9 of its 12 samples as A. The real exam won't be skewed that way, and the practice items here are spread across all letters.
- **The practice items** were written to the kit's standard (`reference/question-writing.md`):
  - Keys come from the exam guide, and any product fact they depend on was checked against official docs.
  - Where the guide and current docs disagree, the item is keyed per the guide and the entry says so (`reference/exam-vs-current-docs.md`).
  - If you think a key is wrong, say so in `/cca-scenario`. Claude re-checks the sources and fixes the file if you're right.
- **Third-party questions** don't belong here. Use them only as an occasional calibration check (`/cca-coach log`).

## Quick reference: question type → first tiebreaker

| The stem asks… | Reach for |
|---|---|
| "root cause" / "most likely cause" | The component the stem's evidence points to (logs, numbers, what changed). Usually upstream of the symptom |
| "first step" / "most effective first" | The least machinery that fixes the stated cause |
| "most reliable" / money, compliance, safety | Deterministic code (hook, gate, schema) over prompt wording |
| "where should this go" | Scope: shared through version control → project; personal → user |
| "which approach" / "how should you design" | The mechanism whose documented purpose matches the need |
| "Select TWO" | Judge each option alone; eliminate the named misconceptions first |

The full list of keying principles, with the official samples behind each, is in [answer-heuristics.md](../reference/answer-heuristics.md).
