---
name: cca-quiz
description: Exam-style practice questions for the Claude Certified Architect exams, Foundations (CCAR-F, scenario-based) and Professional (CCAR-P, standalone). Questions are graded with a rationale for every option and an official Anthropic doc link, and every answer is logged to track weak areas. Use whenever the user says quiz me, practice questions, drill, test me, diagnostic, or "review what I missed", or names an exam domain, task statement (like 1.5 or P3.8), or scenario (S1–S6), even without the word quiz.
argument-hint: "[diagnostic | review | domain N | task 1.4 | scenario S3] [count] [professional]"
allowed-tools:
  - Read
  - Bash(python3 ${CLAUDE_SKILL_DIR}/../../../scripts/cca.py *)
  - WebFetch(domain:code.claude.com)
  - WebFetch(domain:platform.claude.com)
  - WebFetch(domain:modelcontextprotocol.io)
  - WebFetch(domain:www.anthropic.com)
---

# CCA practice quiz

Study root: `${CLAUDE_SKILL_DIR}/../../..` (called ROOT below). Run the `cca.py` commands exactly as written. The full path matches this skill's pre-approved permission, so no prompt appears. Fetches from the official doc domains are pre-approved too.

Arguments: `$ARGUMENTS`

## 1. Work out the request

- **Exam:** Professional (`--exam P`) if the arguments say `professional`, `pro`, or `P`, or name a `P`-prefixed objective. Otherwise use `Target exam:` in `ROOT/progress/plan.md`, and default to Foundations (`--exam F`).
- **Mode:**
  - `diagnostic`: 2 items per domain, for a first baseline.
  - `review`: fresh questions on objectives missed recently.
  - `domain N`, `task X.Y`, or `scenario SN`: filtered set.
  - Otherwise adaptive: the tracker weights picks toward weak, untried, and low-confidence objectives.
- **Count:** the number in the arguments, else 5. Diagnostic sets its own count.

## 2. Draw the items

Run the matching command, swapping in `--exam P` for Professional:
```
python3 ${CLAUDE_SKILL_DIR}/../../../scripts/cca.py draw --exam F --quiz 5                 # adaptive
python3 ${CLAUDE_SKILL_DIR}/../../../scripts/cca.py draw --exam F --quiz 5 --domain 2      # or --task 2.2, --scenario S1, --review
python3 ${CLAUDE_SKILL_DIR}/../../../scripts/cca.py draw --exam F --diagnostic
```
Each row gives an objective, a scenario (Foundations only; Professional items are standalone), and the key letter(s). Use the keys as given, because random placement stops the habit of keying A or B. A `multi(2)` row means 5 options (A–E) with "Select TWO". The printed seed reproduces the draw if a set is interrupted.

Scenarios are matched to objectives by fit. If a pairing still feels forced, keep the objective and adapt the setting inside the scenario, for example a team that also uses Claude Code alongside its Agent SDK tool. Never drift to a different objective to make the scenario fit.

## 3. Load what the items need

Read these before writing any item, because they hold the authoritative scope and the item standard:
- `ROOT/reference/foundations-blueprint.md` or `ROOT/reference/professional-blueprint.md`
- `ROOT/reference/question-writing.md`
- `ROOT/reference/answer-heuristics.md`
- `ROOT/reference/exam-vs-current-docs.md`
- the rows for the drawn objectives in `ROOT/reference/official-sources.md`
- `ROOT/CLAUDE.local.md` if it exists. It describes the learner, which helps you pick realistic stem settings and the misconceptions worth testing.

If a key depends on a product fact you aren't certain of, fetch the official page from official-sources.md before showing the item, or switch to an angle you can support. A confidently wrong practice item does more harm than skipping one.

## 4. Ask one item at a time

Write each item to the standard in question-writing.md and self-review it, then show it:

Foundations:
```
**Q2 of 5 · Scenario S3: Multi-Agent Research System** (objective 1.3)
<stem>
A. …  B. …  C. …  D. …   (each option on its own line)
Answer with a letter, plus confidence H/M/L if you like.
```
Professional:
```
**Q2 of 5 · Professional · standalone** (objective P3.7)
<stem with its own context>
A. … (each option on its own line)
```
For Foundations, give the scenario frame in 2–3 sentences the first time it appears in a set and refer back to it afterwards. In diagnostics, leave out the objective number so it can't hint at the answer.

## 5. Grade and log

After each answer:
1. Give feedback in the format from question-writing.md. Be direct when the answer is wrong. When the user was wrong with high confidence, name the misconception plainly.
2. Log it right away so progress survives an interrupted session:
```
python3 ${CLAUDE_SKILL_DIR}/../../../scripts/cca.py log --exam F --source quiz --task 1.3 --result wrong --confidence high --scenario S3 \
  --lesson "Subagents get context only through their prompt; pass findings explicitly" \
  --doc https://code.claude.com/docs/en/agent-sdk/subagents
```
   - Use `--source diagnostic` or `--source review` to match the mode.
   - Leave out `--scenario` for Professional.
   - Always include `--lesson` on a miss. It's the one-line rule the user should carry into the exam.
   - Include `--confidence` whenever the user gave one, because low-confidence correct answers get re-drilled.
3. If the user disputes a key, take it seriously and re-check the guide and docs. If the user is right, say so. Run `python3 ${CLAUDE_SKILL_DIR}/../../../scripts/cca.py undo --exam F` to remove the bad entry, then log the corrected result.
4. Any time you find a guide-vs-docs conflict, while writing, verifying, or after a dispute, add a row to `ROOT/reference/exam-vs-current-docs.md` with the official source URL. Mention it in the feedback.

## 6. Close the set

Show a short summary:
- the score, and the objectives missed
- the rule to remember for each miss, in one line each
- one suggested next step, such as `/cca-learn 1.3`, `/cca-quiz review`, or the related lab from `/cca-lab list`

After a diagnostic, run `python3 ${CLAUDE_SKILL_DIR}/../../../scripts/cca.py stats --exam F` and point the user to `/cca-coach plan`.
