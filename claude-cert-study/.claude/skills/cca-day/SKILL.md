---
name: cca-day
description: Runs today's session of the daily scenario rotation for the Claude Certified Architect – Foundations exam. Each day is a time-boxed deep dive on one scenario, a spoiler-free overview of the next scenario, and a quick interleaved review of every scenario started so far. Anything the deep dive doesn't reach becomes a specific open question, which gets a quick review and a dedicated slot later. Use whenever the user says today's session, daily study, the rotation, "what's today", day N, deep dive, overview, quick review, open questions, or "what am I carrying", or starts a study session without naming another skill.
argument-hint: "[minutes] [plan | deep | overview | review | questions]"
allowed-tools:
  - Read
  - Bash(python3 ${CLAUDE_SKILL_DIR}/../../../scripts/cca.py *)
  - Bash(date *)
  - WebFetch(domain:code.claude.com)
  - WebFetch(domain:platform.claude.com)
  - WebFetch(domain:modelcontextprotocol.io)
  - WebFetch(domain:www.anthropic.com)
---

# Daily rotation

Study root: `${CLAUDE_SKILL_DIR}/../../..` (ROOT). Arguments: `$ARGUMENTS`

`CCA` below always means `python3 ${CLAUDE_SKILL_DIR}/../../../scripts/cca.py`. Run it with that exact path, because that's the form `allowed-tools` pre-approves.

The user studies two scenarios a day. The schedule and its reasons are under "Daily rotation" in `ROOT/scenarios/README.md`.
1. **Deep dive:** today's scenario, as far as the time box allows.
2. **Overview:** tomorrow's scenario, as a map with no items and no keys.
3. **Quick review:** every scenario started so far, interleaved, for retention.

What the user wants from a deep dive: solid understanding of part of the scenario, and *specific* questions about the rest, never a vague sense of "stuff I didn't get to". Everything the deep dive doesn't reach gets a quick-review touch, then a dedicated slot at that scenario's next deep dive. Keep that promise visible: at every handoff, say where each loose end went.

## 0. Plan the day

1. **Arguments:**
   - A number is the minutes available today (default 90).
   - `plan`: show the agenda, then stop.
   - `deep`, `overview`, or `review`: run only that part.
   - `questions`: go to section 4.
2. Run `CCA day --minutes <m>` and `date "+%H:%M"`. Remember the start time: the journal entry at the close needs it.
3. Show the agenda in 3–4 lines: day N (cycle C), then each part with its scenario, minutes, and clock end time. Leave out parts already marked done today.
4. If the output says an earlier day was left unfinished, mention it in one line and carry on with today, unless the user wants to go back (`CCA day --set <N>`).
5. **Morning test.** The user starts each study day with `/cca-test` on today's scenario. Run `python3 ${CLAUDE_SKILL_DIR}/../../../scripts/bank.py history`.
   - **If there's no graded test from today,** suggest taking one first: about 20 minutes. Take its time out of the deep dive's minutes.
   - **If there is one,** read its misses (`bank.py review <session>` lists them). Work those objectives back first in the deep dive, and name them in the agenda.
6. Start the first part that isn't done.

## 1. Deep dive (time-boxed)

Read `${CLAUDE_SKILL_DIR}/../cca-scenario/SKILL.md` now and follow it in the mode the plan names:

| Plan says | Run |
|---|---|
| guide block | sections 1–4 on the scenario's `exam.md` |
| resume the paused guide block | section 1 step 6 (resume), then 2–4 |
| leftover(s) first, then a fresh block | the Leftovers step in section 0, then section 5 |

Ask for `show` or `try` once, in the brief, if the user hasn't said. Default to `try`.

**Time box.** The deep dive ends at its clock time from the agenda.
- Before each work-back item, run `date "+%H:%M"`. With fewer than 6 minutes left, say time's up and go to the wrap-up (cca-scenario section 4).
- If the user says "keep going", extend by 15 minutes and check again. The overview and review shrink to fit, but don't skip them.
- Never cut the block itself short, because scoring needs every answer. If the box ends mid-block, finish the block, then wrap up.

The wrap-up is cca-scenario section 4. It settles pre-questions and turns every unreached item into an open question. Keep it to about 5 minutes.

Then run `CCA day --mark deep`, adding `--partial` if the block wasn't finished. Close the part in three lines:
- **Solid now:** the rules worked back, by queue ID.
- **Carrying:** the open questions, by ID with their text.
- **Where they go:** quick review starts tonight. Leftover items open the next <S#> deep dive on day N+6.

## 2. Overview (no spoilers)

**Goal:** get oriented in tomorrow's scenario and leave with three pre-questions, without seeing an item or a key, so tomorrow's block is still a cold read.

1. Run `CCA overview <S#>`. That output is the only source. **Don't read the scenario's `exam.md` or `answers.md`.** Tool output is visible to the user, and both files would spoil the block.
2. Show the frame only, then ask: "If you were writing this exam, what three things would you ask about this system?" Wait for the answer.
3. Show the "What the frame puts in play" table, then the question families. Say which families they predicted and which they didn't.
4. Ask the question the scenario is built around (the last line of the output) and let them take a first swing in a sentence. Don't correct it. It gets settled in the deep dive.
5. Ask which terms in the two tables they couldn't define in one sentence.
6. Write three pre-questions:
   - one from the question the scenario is built around
   - one or two from families that cover the scenario's heaviest domain, the user's weakest objectives ("Weakest" in `CCA stats --exam F`), or the terms they couldn't define

   Each must meet the open-question standard in cca-scenario section 4. Store no answers. Add each with `CCA queue add --scenario <S#> --kind pre --prompt "…"`.
7. Run `CCA day --mark overview`. Show the three pre-questions and say "carry these into tomorrow's deep dive".

Keep it to about 15 minutes. Don't teach deciding rules. If the user asks for one, say it's tomorrow's first question to settle, and make it a pre-question if it isn't one already.

## 3. Quick review (retention)

1. Run `CCA queue due`. Its default set is today's review scenarios, at most 3 entries each.
2. **Overview-only scenarios** (listed under "No review entries yet"): ask from memory for the frame's key constraint and the question the scenario is built around. Use one exchange each, with no score. Correct anything wrong in a line, from `CCA overview <S#>`.
3. **Each due entry,** in the order printed (already interleaved across scenarios):
   1. Show the scenario and the prompt only. The user answers in a sentence or two.
   2. Run `CCA queue show <ID>` and compare with the stored `answer`. If there's none, check the source first: the `ref`'s entry, or the official doc. Then store the answer with `CCA queue update <ID> --answer "…"`.
   3. Give a verdict. It's **right** only if they state the rule *and* why it wins. Naming the option isn't enough. A partial answer is **wrong**: say in one line what was missing.
   4. Give feedback in at most two lines. If it needs more, say it gets its time at the next <S#> deep dive, and move on.
   5. Run `CCA queue mark <ID> --result right|wrong`.
4. Stop at the time box even if entries remain. The leftovers come first next time.
5. Run `CCA day --mark review`.

Review entries aren't exam-style items, so they don't go into `log.jsonl`.

## Close every sitting (even a partial one)

1. Ask for a one-line takeaway in the user's own words: "What clicked today?" If they skip it, leave it out.
2. Log the sitting: `CCA journal add --kind session --minutes <minutes since the start time from section 0> --text "<summary>"`.
   - Format: `Day N · S1 deep dive: block 7/10, 4 worked back, 3 open · S3 overview · review 5/6 right · "<takeaway>"`
   - Include only the parts done in this sitting.
3. Run `CCA dashboard` to refresh `progress/dashboard.html`.
4. Close in a few lines:
   - today's review: how many right and wrong, and any that went solid
   - **carry these:** the open questions and pre-questions (prompts only), and the path `progress/notebook.md`
   - next study day, from the `CCA day` output: the deep dive and the overview
   - the dashboard path, which they can open in a browser
   - **an optional evening test:** `/cca-test` on today's scenario, to see what stuck
   - **tomorrow's questions:** if tomorrow's scenario has fewer than 20 unseen verified bank questions (`bank.py status`), offer to generate them in the background tonight. Ask first, because it uses the user's Claude plan.

## 4. Questions (`questions`)

Run `CCA queue list` and show it grouped: open questions, pre-questions, then in review.
- Offer to talk through any of them.
- An **open or pre-question** the user explains correctly is settled: `CCA queue update <ID> --kind recall --answer "…"`. It stays in review until solid.
- **Don't resolve a pre-question by explaining it** before the scenario's deep dive. That would spoil the block. Talk it through only after the guide block has been sat.

## Rules

- One question per message. Keep replies tight.
- The accuracy rules at the end of cca-scenario apply here too: never invent product facts, answer per the guide, and teach the drift.
- If the user disputes a stored answer, re-check the source. Fix the entry with `CCA queue update`, or drop it with `CCA queue drop <ID>` if it was wrong.
