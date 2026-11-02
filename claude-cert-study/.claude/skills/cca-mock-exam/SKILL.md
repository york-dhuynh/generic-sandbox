---
name: cca-mock-exam
description: Timed practice exams for the Claude Certified Architect exams. Foundations (CCAR-F) mocks are 60 items across 4 of 6 scenarios, built from the verified question bank when it has enough unseen items. A scenario block is 15 bank items for one scenario. Professional (CCAR-P) is 63 standalone items. Exams are weighted to the official blueprint and give no feedback until the end. They finish with a score, its 95% interval, a per-domain report, and a review of every item with its key and doc quotes. Supports resuming.
argument-hint: "[foundations|professional] [block S1-S6] [resume] [review SESSION]"
disable-model-invocation: true
allowed-tools:
  - Read
  - Bash(python3 ${CLAUDE_SKILL_DIR}/../../../scripts/cca.py *)
  - Bash(python3 ${CLAUDE_SKILL_DIR}/../../../scripts/bank.py *)
  - Bash(date *)
  - WebFetch(domain:code.claude.com)
  - WebFetch(domain:platform.claude.com)
  - WebFetch(domain:modelcontextprotocol.io)
  - WebFetch(domain:www.anthropic.com)
---

# Mock exam

Study root: `${CLAUDE_SKILL_DIR}/../../..` (ROOT). Arguments: `$ARGUMENTS`

A mock is worth doing only if it feels like the real exam: realistic items, blueprint weights, no hints, real time pressure. Hold to that even when the user asks for hints mid-exam. Offer the hint after grading instead.

`BANK` below means `python3 ${CLAUDE_SKILL_DIR}/../../../scripts/bank.py`. Run it with that exact path, because that's the form `allowed-tools` pre-approves.

## Bank exams (Foundations; use these first)

Bank items were written by Claude, checked by rules, and solved blind by independent Claude runs under every option rotation. Only unanimous items are verified. They are the most trustworthy practice items in the kit, and the only ones whose scores go on the dashboard's "Practice exams over time" chart. The method is in `ROOT/reference/practice-exam-research.md`.

**Never run `BANK inspect` or read `progress/bank/keys.json` before a form is graded.** `BANK show` prints items without keys.

1. **Build the form.**
   - **A block** (`block S1`): `BANK form --block <S#> --n 15`.
   - **A full mock:** `BANK form --mock`.
   - **If the bank is short**, the command says so. Run `BANK status` and offer either of these:
     - **Generate more:** `BANK generate --scenario <S#> --n 15`. Run it in the background. It takes several minutes and counts against the user's Claude plan usage, and it never prints item text.
     - **The unverified in-session mock below.** Say plainly that its keys were only self-checked.
   - Note the session ID the command prints.
2. **Brief the user** as in Setup below. A block is 15 items in about 30 minutes; a mock is 60 items in 120 minutes.
3. **Give each item:**
   - Run `BANK show <session> <n>` and show its output as printed: scenario frame (when the scenario changes), stem, options.
   - Record the answer with `BANK answer <session> <n> <letters> [--conf high|medium|low] [--flag]`. Say nothing about correctness.
   - At block boundaries, or every 15 items, run `date "+%H:%M"` and report elapsed time.
4. **Grade:** `BANK grade <session>`. It scores the form, gives the 95% interval and the domain split, logs every item to `progress/log.jsonl`, and marks the items seen. Then run `python3 ${CLAUDE_SKILL_DIR}/../../../scripts/cca.py dashboard`.
5. **Review.** The user reviews the questions after taking them; that's their quality check on the bank.
   - Go through misses first, then flagged items, then the rest if the user wants. Show one item at a time with `BANK review <session> --n <k>`: their answer, the key, the rule, why each option wins or loses, and the doc quotes.
   - Ask whether the key holds up.
   - **If the user disputes it,** re-check the quoted page (WebFetch the official URL) and the exam guide.
     - **The user is right, or the quote doesn't support the key:** `BANK dispute <id> --note "<why>"`, then `BANK resolve <id> retire`.
     - **The key holds:** explain why in two lines, with the quote.
   - Also check guide-vs-docs conflicts against `ROOT/reference/exam-vs-current-docs.md`.
6. **Report:** score, interval, weakest domains, and the rules from misses. Point to the dashboard chart. Readiness on bank exams means three fresh full mocks whose pooled interval's low end is 80% or higher (`BANK history`).

`resume` with bank forms: run `BANK status`, find the newest file in `ROOT/progress/bank/forms/` whose `"graded"` is null, and continue from the first unanswered item number. Don't read the form's item list aloud.

`review SESSION` as an argument jumps straight to step 5 for an already graded form. `BANK review --quarantine` lists items the checkers disagreed on. Those are never scored, so the user can read them freely.

## Unverified in-session mock (fallback)

Use this when the bank can't build the form and the user doesn't want to wait for generation, and always for Professional. Tell the user these items were written and checked by one Claude session only.

### Resume

If the arguments include `resume`, find the newest folder in `ROOT/progress/mocks/` that has no `report.md`. Read its `plan.md`, `answers.md`, and any `items-*.md`, tell the user where they left off and how much time is recorded, then continue from the next unanswered item.

### Setup

1. Pick the exam: `professional`/`pro`/`P` means P, otherwise F.
2. Draw the plan, using `--exam P` for Professional. This creates `progress/mocks/<session-id>/` with `plan.md` and an empty `answers.md`, and prints the session ID and folder:
```
python3 ${CLAUDE_SKILL_DIR}/../../../scripts/cca.py draw --exam F --mock --save
```
   Read `plan.md`. It holds every item's objective, scenario, type, and key letter.
3. Read these before writing items:
   - the blueprint for the exam
   - `ROOT/reference/question-writing.md`
   - `ROOT/reference/answer-heuristics.md`
   - `ROOT/reference/exam-vs-current-docs.md`
   - `ROOT/reference/official-sources.md`
4. Record the start time with `date "+%Y-%m-%d %H:%M"` and write it to `answers.md`.
5. Brief the user:
   - **Time:** 120 minutes, self-timed.
   - **Rules:** no docs, notes, or Claude help.
   - **Answers:** a letter, or two letters for "Select TWO", optionally with H/M/L confidence.
   - **Commands:** `flag` marks an item for review, `pause` saves and stops, `end` grades now.
   - **Feedback:** none until the end.

### Running the exam

Work in blocks: one scenario of 15 items for Foundations, or 15–16 items for Professional.

For each block:
1. **Write the whole block to `items-<n>.md` before showing any item.** For each item include: number, objective, scenario, stem, options, the key from the plan, a 2–3 line rationale, and one official URL. Committing the key in writing first stops the key from drifting to fit the user's answer.
2. Self-review every item against the checklist in question-writing.md. Plan keys are fixed, so rewrite an item rather than move its key.
3. Show items one at a time, with only the number, scenario frame (Foundations), stem, and options. Never show the objective, key, or rationale.
4. After each answer, append `<n>: <letters> [conf] [flag]` to `answers.md`. Say nothing about correctness. If the user prefers, show 2–3 items per message, but keep the same no-feedback rule.
5. At each block boundary, run `date "+%H:%M"`. Report elapsed time in one line, and warn when 60 and 100 minutes have passed.

For Foundations, introduce each scenario with a 3–5 sentence frame based on the official scenario description. Every item in that block builds on the frame.

### Grading

When all items are answered, time is up, or the user says `end`:
1. Score each answered item against the key. Multiple-response items need both letters right. Unanswered items count as wrong.
2. Write `results.jsonl` in the session folder, one line per item:
   `{"task": "1.4", "result": "wrong", "confidence": "high", "scenario": "S1", "lesson": "<rule>", "doc": "<url>"}`
   Include `lesson` and `doc` for misses, and leave out `scenario` for Professional. Then log the whole mock in one call. The import is all-or-nothing and names any bad line:
```
python3 ${CLAUDE_SKILL_DIR}/../../../scripts/cca.py import --exam F --source mock --session <session-id> --file <session folder>/results.jsonl
```
3. Write `report.md` in the session folder with:
   - raw score and percent, plus time used
   - a per-domain table: items, correct, percent, blueprint weight
   - per-scenario results (Foundations)
   - confident misses, listed first: each with the key, why, the rule, and the doc link
   - other misses, in the same format
   - flagged-but-correct items, because those were lucky guesses worth re-studying
   - a note that practice percent is not a scaled score. Anthropic publishes no raw-to-scaled conversion. The study heuristic is ≥80% on fresh mocks as a safety margin.
4. Run `python3 ${CLAUDE_SKILL_DIR}/../../../scripts/cca.py stats --exam F` and give the user a short summary: score, weakest two domains, the top 3 rules to remember, and the next step (usually `/cca-learn` on the weakest objective, then `/cca-quiz review`).
