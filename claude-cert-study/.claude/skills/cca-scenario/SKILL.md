---
name: cca-scenario
description: Scenario-first, depth-first study for the Claude Certified Architect – Foundations exam using the guide in scenarios/. Runs one exam scenario (S1–S6) as a timed block with no feedback, scores and logs it, then reverse-engineers every miss and guess (the key, the clue in the stem, why each distractor fails, the rule, other ways the exam could ask it) and checks transfer with a fresh variant question. Use whenever the user names a scenario (S1–S6, "the support scenario", "the CI one", "extraction"), says scenario study, depth first, next scenario, work backwards, or reverse engineer, or asks to go through the scenario guide.
argument-hint: "[S1-S6 | next | status] [fresh] [show|try]"
allowed-tools:
  - Read
  - Bash(python3 ${CLAUDE_SKILL_DIR}/../../../scripts/cca.py *)
  - Bash(date *)
  - WebFetch(domain:code.claude.com)
  - WebFetch(domain:platform.claude.com)
  - WebFetch(domain:modelcontextprotocol.io)
  - WebFetch(domain:www.anthropic.com)
---

# Scenario study, depth first

Study root: `${CLAUDE_SKILL_DIR}/../../..` (ROOT). Arguments: `$ARGUMENTS`

A bare `cca.py` below means `python3 ${CLAUDE_SKILL_DIR}/../../../scripts/cca.py`. Run it with that exact path, because that's the form `allowed-tools` pre-approves.

The user studies one scenario at a time:
1. Sit it the way the exam presents it.
2. For every answer they missed or guessed, start from the correct answer and work backwards until they can explain it and predict what else the exam could ask.

The method is in `ROOT/scenarios/README.md`. Read it at the start of a session.

## 0. Pick the scenario

| Argument | Scenario folder |
|---|---|
| S1 / support | `S1-customer-support` |
| S2 / code generation | `S2-code-generation` |
| S3 / research | `S3-multi-agent-research` |
| S4 / productivity | `S4-developer-productivity` |
| S5 / CI | `S5-ci-cd` |
| S6 / extraction | `S6-structured-extraction` |

All folders are under `ROOT/scenarios/`.

- **`status`:** run `python3 ${CLAUDE_SKILL_DIR}/../../../scripts/cca.py stats --exam F`, show the scenario table, say which guide blocks are done and which is next, then stop.
- **`next` or no scenario:** run stats. Take the first scenario in the README's order whose guide block shows "not started". If all six are done, take the scenario with the lowest Last-15 accuracy and use `fresh`.
- **`fresh`, or a scenario whose guide block is already done:** run a generated block (section 5). The fixed items are familiar by now and would overstate the score. Tell the user that's why.
- **Leftovers come first** whenever the guide block is already done. Run `python3 ${CLAUDE_SKILL_DIR}/../../../scripts/cca.py queue list --scenario <S#> --kind open`.
  - **Entries with a `ref`** are items the user sat but never worked back. Work each one back with section 3 steps 1–4, then run `cca.py queue update <ID> --kind recall --answer "<rule + why it wins>"`. Find the item from the ref's session:
    - `<S#>-block-…` is in the scenario's `answers.md`.
    - `<S#>-fresh-…` is in `ROOT/progress/scenarios/<session>-items.md`.
  - **Entries without a `ref`:** ask the user to answer first, then settle the question with the sources and resolve it the same way.
  - Then start the fresh block.
- **Review style:** `show` means you explain each miss. `try` means the user attempts the backwards reasoning first. If neither is given, ask once in the brief. If the user doesn't care, default to `try`, because working it out yourself sticks better.

## 1. Sit the block under exam conditions

1. Read only the scenario's `exam.md`. **Do not read `answers.md` until every item is answered.** Tool output is visible to the user, and reading it early would show the keys.
2. Run `date "+%Y%m%d-%H%M"`. The session ID is `<S#>-block-<stamp>`.
3. Brief the user in a few lines:
   - 10 items, about 20 minutes.
   - Answer with a letter, or two letters for Select TWO, plus H/M/L confidence.
   - `flag` marks an item, `pause` stops and saves.
   - No feedback until the end.
4. Show the scenario frame exactly as written. Then show one item at a time: number, stem, options. Show the official samples (Q8–Q10) the same way as the others.
5. Record each answer. Give no hints and no reaction, not even "got it, next". Just show the next item.
6. On `pause`, write the answers so far to `ROOT/progress/scenarios/<session>.md` and stop. On a later run with `resume`, read that file and continue.

## 2. Score and log

1. Now read `answers.md`. Score against the key table. A Select TWO item needs both letters.
2. Show a table (Q · yours · key · confidence · ✅/❌), the score, and the time used (`date`).
3. Log the block in one call:
   - Write `ROOT/progress/scenarios/<session>.jsonl`, one line per item:
     `{"task": "1.4", "result": "wrong", "confidence": "high", "scenario": "S1", "lesson": "<the rule from the key table>", "doc": "<the item's source URL>"}`
     Include `lesson` and `doc` on misses.
   - Import it:
```
python3 ${CLAUDE_SKILL_DIR}/../../../scripts/cca.py import --exam F --source scenario --session <session> --file <that jsonl>
```
4. Build the review queue in this order:
   1. confident (H) misses
   2. other misses
   3. correct answers with L confidence or a flag (lucky guesses)

   Skip correct, confident answers unless the user asks for them.

## 3. Work backwards, one item at a time

For each queued item:

1. Restate the item in one line, then give the key.
2. **In `try` mode,** ask: "What in the stem or the scenario points to <key>? And what made <their letter> look right?" Wait for the answer. Then compare it with the entry in `answers.md`: confirm what they got and correct what they missed.
   **In `show` mode,** go straight to the breakdown.
3. Give the breakdown from the `answers.md` entry, framed around the user's actual choice:
   - question type
   - the clue (quote the stem)
   - why the key wins
   - why *their* pick loses (on a confident miss, name the misconception plainly in one sentence)
   - the other distractors, one line each
   - the rule
4. Give the other ways the exam could ask it, using the three variants in the entry. In `try` mode, first ask the user to predict the answer to the *flip a condition* variant, then reveal it.
5. **Transfer check.** Write one new item that tests the same rule in a situation the block didn't use. Don't reuse a listed variant word for word.
   - Get the key letter from `python3 ${CLAUDE_SKILL_DIR}/../../../scripts/cca.py draw --exam F --quiz 1 --task <task> --scenario <S#>`.
   - Write it to the standard in `ROOT/reference/question-writing.md` and self-review it before showing it.
   - Grade it with the feedback format in that file.
   - Log it with `cca.py log --exam F --source scenario --task <task> --scenario <S#> --session <S#>-transfer-<stamp> …`, adding `--lesson` and `--doc` on a miss.
   - If it's missed too, the gap is the concept. Note `/cca-learn <task>` for the debrief, and add an open question for the part that's still unclear (section 4 standard).
6. **Queue it for review.** Add one recall entry:
   - `python3 ${CLAUDE_SKILL_DIR}/../../../scripts/cca.py queue add --scenario <S#> --kind recall --task <task> --ref "<session> Q<n>" --prompt "<cue>" --answer "<rule + why it wins>"`
   - The cue is a one-line situation that calls for the rule. It doesn't quote the item and doesn't name the answer.
   - Example cue: "A billing dispute passes 40 turns and gets summarized, and the agent starts quoting wrong amounts. What fixes it, and why not a better summarizer prompt?"
7. Move on to the next item. If the user stops early, say what's left. The block is already logged, and section 4 turns what's left into open questions.

Keep each step tight: one item per message, and no wall of text.

## 4. Debrief the scenario

Nothing should leave the session as a vague "didn't get to it". Everything ends up worked back, or as a specific question with a date to come back.

1. Summarize from the "Scenario playbook" section of `answers.md`, filtered to what this user missed:
   - the frame phrases that decided answers
   - the question families they've now seen
   - the traps they fell into
2. **Settle pre-questions** from the overview. Run `cca.py queue list --scenario <S#> --kind pre`, and ask the user to answer each one in a sentence.
   - **Covered today and answered well:** `cca.py queue update <ID> --kind recall --answer "…"`.
   - **Not covered:** `cca.py queue update <ID> --kind open --answer "…"`, with the answer from the playbook. Don't reveal the answer now.
3. **Unreached items.** For every item still in the review queue (section 2, step 4), add an open entry: `cca.py queue add --scenario <S#> --kind open --task <task> --ref "<session> Q<n>" --prompt "<question>" --answer "<rule from the key table>"`. These are the leftovers that open the scenario's next deep dive.
4. **Ask "What's still fuzzy?"** Turn each answer into a specific open question and add it with no `--ref`. If the user's answer is vague, rewrite it with them until it meets the standard.
5. Write `ROOT/progress/scenarios/<session>.md` with:
   - the score
   - each miss and its rule
   - the transfer results
   - the open questions, by queue ID
   - the next step

   If a pause file exists, replace it.
6. Recommend the next step:
   - **Run from `/cca-day`:** the rotation decides it, so just hand back.
   - **Block ≥ 80% and every transfer item right:** the next scenario in the README's order, and its lab if it isn't done (`/cca-lab list`).
   - **Otherwise:** `/cca-learn <weakest objective>`, then `/cca-scenario <S#> fresh`.

**The open-question standard.** An open question:
- names the situation: the scenario and the condition that matters
- asks for a decision or a reason (which, why, when), not a topic
- can be answered in one or two sentences
- may name the competing options, but doesn't say which wins

"MCP errors" and "I'm shaky on hooks" don't meet it. "S1, 19 tools after connecting an ops server: scope the tools or rewrite the descriptions first, and what in the stem decides it?" does.

## 5. Fresh block (generated)

1. Draw the objectives:
```
python3 ${CLAUDE_SKILL_DIR}/../../../scripts/cca.py draw --exam F --quiz 10 --scenario <S#>
```
   This picks objectives that fit the scenario, weighted toward the user's weak spots.
2. Before writing, read:
   - `ROOT/reference/question-writing.md`
   - `ROOT/reference/answer-heuristics.md`
   - `ROOT/reference/exam-vs-current-docs.md`
   - the drawn objectives' rows in `ROOT/reference/official-sources.md`
   - the scenario's `exam.md` and `answers.md`, to reuse the frame and avoid repeating their items
3. Write all 10 items to `ROOT/progress/scenarios/<S#>-fresh-<stamp>-items.md` before showing any. Writing first locks in the keys. The `-items` suffix keeps the debrief, which is written to `<session>.md`, from overwriting them. Use the same structure as `answers.md`:
   - for each item: key, objective, question type, clue, why, why not, rule, three variants, source
   - stems and options in a separate section at the top
4. Run sections 1–4 against that file, with session ID `<S#>-fresh-<stamp>`. Show only the stems and options during the block.

## Accuracy

- Never invent product facts: flags, fields, file locations, defaults. If a fresh item's key depends on one you aren't sure of, fetch the official page first or test a different angle.
- If the user disputes a key, re-check the exam guide (`ROOT/reference/foundations-blueprint.md`) and the item's source page.
  - **If the user is right:** say so, fix `answers.md` (and `exam.md` if the stem is at fault), then log a corrected entry with `cca.py log … --result correct --lesson "key corrected: <why>"`.
  - **If it's a guide-vs-docs conflict:** add a row to `ROOT/reference/exam-vs-current-docs.md` with the official source.
- When the guide and current docs disagree, the exam answer follows the guide. Say both.
