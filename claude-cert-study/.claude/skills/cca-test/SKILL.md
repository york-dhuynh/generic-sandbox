---
name: cca-test
description: Daily practice test in the browser for the Claude Certified Architect – Foundations exam. Builds a test of fresh, verified question-bank items for one scenario, by default today's rotation scenario. It opens as a local page with no answer keys in it. When the user pastes back the "/cca-test results ..." line the page copies, it grades the test, logs it, and talks through the results to set the day's direction. It can also retake a test already taken, with the questions in a new order. Use when the user wants a practice test, a morning or evening test, a retake, or a quick check of where they stand, or pastes a line starting with "/cca-test results".
argument-hint: "[S1-S6] [number of questions] | retake [S1-S6 | SESSION] | results SESSION ANSWERS..."
allowed-tools:
  - Read
  - Bash(python3 ${CLAUDE_SKILL_DIR}/../../../scripts/practice_test.py *)
  - Bash(python3 ${CLAUDE_SKILL_DIR}/../../../scripts/bank.py *)
  - Bash(python3 ${CLAUDE_SKILL_DIR}/../../../scripts/cca.py *)
  - Bash(date *)
  - WebFetch(domain:code.claude.com)
  - WebFetch(domain:platform.claude.com)
  - WebFetch(domain:modelcontextprotocol.io)
  - WebFetch(domain:www.anthropic.com)
---

# Practice test

Study root: `${CLAUDE_SKILL_DIR}/../../..` (ROOT). Arguments: `$ARGUMENTS`

The user starts each study day with a test to decide where to focus, and sometimes ends the day with another to see what stuck. Every graded test goes on the dashboard's "Practice exams over time" chart.

Three short names are used below. Run each with the exact path given, because that's the form `allowed-tools` pre-approves:
- `PT` = `python3 ${CLAUDE_SKILL_DIR}/../../../scripts/practice_test.py`
- `BANK` = `python3 ${CLAUDE_SKILL_DIR}/../../../scripts/bank.py`
- `CCA` = `python3 ${CLAUDE_SKILL_DIR}/../../../scripts/cca.py`

**Never read `ROOT/progress/bank/keys.json`, run `BANK inspect`, or show question text in chat before a test is graded.** The page is the only place the user sees the questions.

## Start a test (`/cca-test`, `/cca-test S3`, `/cca-test S1 15`)

1. **Scenario:** the one named in the arguments. Otherwise use today's deep-dive scenario: run `CCA day` and read the "Deep dive" row. This follows the recommended order S1 → S3 → S6 → S5 → S4 → S2.
2. **Length:** a number in the arguments, otherwise 10.
3. Run `date "+%H:%M"` and `BANK history`. A graded test on the same scenario earlier today makes this the day's second test. Remember that for the debrief.
4. Run `PT new --scenario <S#> --n <n>`. It builds the page, opens it in the browser, and marks the questions as seen.
   - **If the user hasn't taken a test on that scenario yet,** `PT new` reopens that test instead of building another, and says so. Tell the user which test it is (the build date), and that any answers they already gave are kept.
     - If they want a different test, add `--another`. The open one stays open.
     - To drop it, run `PT void <SESSION>`. Its questions stay used, because the user may have read them. Add `--release` only if the user says they never read them; that puts the questions back in the fresh pool. Then run `PT new` again.
   - `PT list` shows every browser test and whether it was taken.
   - **If the bank is short,** the command says so. Offer to generate more in the background: `BANK generate --scenario <S#> --n 20`. It takes several minutes and counts against the user's Claude plan. Don't start it without a yes.
5. Tell the user in 2–3 lines:
   - the test is open in their browser. Don't offer a `file://` link: those don't open from the VS Code chat. If the page didn't appear, run `open <page path>` yourself (on macOS).
   - how many questions, about 2 minutes each
   - set a confidence level on each question
   - when done, click **Finish**, then **Copy results**, and paste the line here

## Retake a test (`/cca-test retake`, `/cca-test retake S3`, `/cca-test retake <SESSION>`)

The user may retake tests often. A retake is the same questions in a new order, as a new session.
1. Run `date "+%H:%M"`, then `PT retake <SESSION>`, or `PT retake --scenario <S#>` (default: today's deep-dive scenario). Without a session, it picks the test on that scenario practiced longest ago. If a retake of that test is already open, it reopens it instead.
2. Tell the user, as in step 5 above, that the test is open. Add one line: it's attempt N, and the last attempt scored X on that date.
3. If the last attempt was today, mention once that a retake right after reviewing mostly measures memory of those answers, and one a few days later says more about what stuck. Don't repeat it on later retakes.

## Grade and debrief (`/cca-test results SESSION …`)

1. **Grade:** run `PT submit <SESSION> <every answer token exactly as pasted, including time=…>`, then `CCA dashboard`.
2. **Score:** give it in one line with its 95% interval.
   - On a 10-question test, chance alone moves the score about ±25 points, so the trend across tests matters more than any one score.
   - **If this is the day's second test on the scenario,** compare it with the first honestly. If the intervals overlap, say it isn't a clear change yet.
   - **If it's a retake,** the grade output ends with the earlier attempts and which questions changed. Compare with the last attempt, not with first tries on other tests. A retake score shows what was kept, not exam readiness, and it stays out of the domain accuracy figures.
3. **Domains:** say which domains held and which didn't, from the grade output.
   - **On a retake,** work "Missed again" first. Those rules didn't stick after a review, so explain from a different angle and have the user state the rule in their own words. Then cover "Missed now, right last time". Mention "Right now" questions only in passing.
4. **Misses, one at a time, user-paced.** Go high-confidence misses first, then the other misses, then lucky guesses (right with low confidence).
   - Run `BANK review <SESSION> --n <k>`.
   - **On a high-confidence miss,** first ask: "What made <their letter> look right?" Then give the rule, the clue in the stem, and the doc quote. Confident errors corrected with feedback stick best, so spend the most time here.
   - **On other misses,** give the key, the rule, why their pick loses, and the quote.
   - **Ask whether the key holds up.** The user's review is the bank's quality check.
     - **If they dispute it,** re-check the quoted page and the exam guide.
     - **If they're right, or the quote doesn't support the key:** `BANK dispute <id> --note "…"`, then `BANK resolve <id> retire`.
   - **After each miss is settled,** add it to spaced review: `CCA queue add --scenario <S#> --kind recall --task <task> --ref "<SESSION> Q<k>" --prompt "<a new one-line situation that calls for the rule>" --answer "<rule + why it wins>"`.
5. **Set direction.** This is the point of a morning test.
   - **Morning:** name the 1–2 objectives that most need work, and tie them to today's plan, for example: "In today's S1 deep dive, work back 1.5 and 2.2 first. If time is left, run `/cca-learn 2.2`."
   - **Evening:** name what improved and what to carry. Any miss that isn't settled becomes an open question (`CCA queue add … --kind open`).
6. **Log it:** `CCA journal add --kind note --text "<morning|evening> test <S#>: <score> (<interval>); missed <objectives>"`.

## Keeping the bank stocked

Each test needs fresh questions, so a morning and an evening test use about 20 per scenario per day. Check `BANK status` after grading. If tomorrow's scenario (the next study day in `CCA day`) has fewer than 20 unseen verified questions, offer to generate them in the background now, so they're ready by morning.
