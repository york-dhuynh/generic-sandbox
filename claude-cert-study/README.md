# Claude Certified Architect study kit

Claude Code skills for studying for **Claude Certified Architect – Foundations (CCAR-F)** now and **Professional (CCAR-P)** later. The content is built from Anthropic's official exam guides (v1.0, July 2026) and current official docs. Third-party sites are used only as extra practice.

## Start

Open a Claude Code session **in this folder**, so its skills, settings, and CLAUDE.md load:

```bash
cd claude-cert-study && claude
```

In VS Code, open `claude-cert-study` as its own workspace folder. A session started in the parent folder only picks up these skills after Claude touches a file in here.

First session:
1. Read [scenarios/README.md](scenarios/README.md) (5 minutes), especially "Daily rotation". Foundations is studied two scenarios a day: a deep dive on one, an overview of the next, and a quick review of everything started so far.
2. Run `/cca-day`. Day 1 is an S1 deep dive, an S3 overview, and a quick review of both. The official sample questions are built into the S1, S2, S3, and S5 blocks.
3. Run `/cca-coach plan` to map the rotation onto your calendar and exam date.
4. Check `CLAUDE.local.md` and correct anything wrong about your background.

Every day after that:
1. Start with `/cca-test`, a 10-question browser test on today's scenario that shows where to focus.
2. Run `/cca-day`. It knows which day you're on, works your test misses first, logs the sitting, and refreshes the dashboard.
3. Optionally, end with another `/cca-test`.

If you build a test and don't take it, it stays open: the next `/cca-test` on that scenario reopens it instead of building another, and the dashboard lists it under "Not taken yet". The test page keeps your answers in the browser, and its clock runs only while the page is open. `python3 scripts/practice_test.py list` shows every test and every attempt.

To take a test again, run `/cca-test retake` (or `retake S3`, or `retake <session>`). You get the same questions in a new order. Without a session, it picks the one you practiced longest ago. Grading a retake shows which questions you missed again and which flipped. Retakes appear on the practice chart as diamonds. They stay out of accuracy by domain, because you've already seen the answers.

To see your progress, run `python3 scripts/cca.py dashboard --open`. Every command that logs progress rebuilds it, so the page's **Refresh** button (a reload) always shows the latest. It writes `progress/dashboard.html`, a self-contained page with:
- practice test scores over time, and links to any tests you haven't taken yet
- domain and scenario accuracy against the 75% line
- an objective heatmap
- the accuracy trend
- confidence calibration
- the rotation calendar
- the review queue
- what you're carrying
- the readiness checklist
- the journal

To get a quick cross-domain baseline before you start, `/cca-quiz diagnostic` gives you 10 items, 2 per domain.

## Commands

| Command | What it does |
|---|---|
| `/cca-test` | Practice test in your browser: fresh, verified questions for today's scenario (or `S3`, `15` questions). Click Copy results, paste the line back, and Claude grades it and talks it through |
| `/cca-day` | Today's rotation day: deep dive, overview, quick review. Also `60` (minutes), `plan`, `questions` |
| `/cca-scenario S1` | Depth-first scenario study: sit the block, score it, reverse-engineer each miss, prove transfer. Also `next`, `status`, `S1 fresh` |
| `/cca-coach` | Dashboard and next session. Also `plan`, `ready`, `log <score>`, `switch` (to Professional) |
| `/cca-learn 1.5` | Teaches one objective from official docs, then checks you with 2–3 items. Accepts topics too: `/cca-learn tool_choice` |
| `/cca-quiz` | Adaptive questions aimed at your weak spots. Also `diagnostic`, `review`, `domain 2`, `task 1.4`, `scenario S6`, `professional` |
| `/cca-mock-exam` | Full mock: 60 items, 4 random scenarios, 120 minutes, report at the end. Built from the verified question bank when it has enough unseen items. `block S1` gives a 15-item scenario block. Also `review <session>`, `resume`, and `professional` for 63 items |
| `/cca-lab` | Hands-on labs F1–F5 and P1–P6 with acceptance checks. `start`, `hint`, `review` |
| `/cca-verify "<claim>"` | Checks a claim against official docs in an isolated subagent |

Claude also picks the right skill from plain requests like "quiz me on hooks" or "am I ready to book?". The mock exam starts only when you ask for it by name.

## Verified question bank

`scripts/bank.py` writes practice questions with Claude and keeps only the ones that survive independent checks. It runs on your Claude Code login (`claude -p`, no API key), so its usage counts toward your plan.

```bash
python3 scripts/bank.py generate --scenario S1 --n 15   # write and verify; prints no question text
python3 scripts/bank.py status                          # what's verified, unseen, quarantined
```

Then take the questions with `/cca-mock-exam block S1`, or `/cca-mock-exam` once four scenarios have 15 unseen questions each.

Each question goes through four stages:
1. **Written hard by Opus**, quoting the saved official docs.
2. **Rule checks:**
   - every quote must really exist in the docs
   - the answer can't be the longest option
   - no wording giveaways
   - no near-duplicates
3. **Blind solving:** Opus and Sonnet each answer without the key, under every shuffle of the options. All of them must agree with the key.
4. **Difficulty probe:** a model sees only the options, with the question hidden, under every shuffle.
   - The official samples are guessable this way every time.
   - "Medium" and "hard" questions mean harder than the official samples on this one measure.
   - `--harden` gives easy questions one rewrite, kept only if it passes every check again. Most rewrites fail, so it is off by default.

Grading logs every question and adds the score, with its 95% range, to the dashboard's "Practice exams over time" chart. You review each question after taking it. A disputed question leaves the bank. The research behind this is in [reference/practice-exam-research.md](reference/practice-exam-research.md).

## How it decides what's true

1. The **official exam guide** decides what is tested and how answers are keyed.
2. **Official docs** (code.claude.com, platform.claude.com, modelcontextprotocol.io) decide how things work today.
3. Anthropic engineering posts, Academy courses, and GitHub repos come next.
4. **Third-party prep** (claudecertificationguide.com and others) is practice only.

The guide is already behind the product in a few places, for example Task vs Agent, commands merged into skills, and what `allowed-tools` means. These are tracked in [reference/exam-vs-current-docs.md](reference/exam-vs-current-docs.md). Answer the exam per the guide and build per the docs.

## Layout

```
.claude/skills/      cca-day, cca-scenario, cca-coach, cca-learn, cca-quiz, cca-mock-exam, cca-lab, cca-verify
scenarios/           the scenario study guide: method README + S1–S6, each with exam.md and answers.md
.claude/rules/       labs.md: coach-don't-solve rule, loaded only for files in labs/
.claude/settings.json  pre-approves fetching official doc domains; blocks reading .env files
reference/           condensed blueprints, official source map, drift log, answer heuristics, item-writing standard
scripts/cca.py       progress log, stats, adaptive and mock draws, rotation, review queue, journal (stdlib Python)
scripts/dashboard.py builds progress/dashboard.html from the logs (also `cca.py dashboard`)
scripts/bank.py      verified question bank: generate with `claude -p`, build forms, grade, review
scripts/practice_test.py  browser practice tests from the bank; pasting results back grades them (/cca-test)
progress/bank/       items.json, keys.json (answers: don't open before grading), forms/, docs/ snapshot, runs.jsonl
progress/tests/      the test pages (<session>.html), no answer keys inside
progress/            log.jsonl, plan.md, mocks/<session>/, scenarios/<session>, rotation.jsonl, queue.json,
                     journal.jsonl, notebook.md (your open questions, no answers), dashboard.html — created as you go
labs/                your lab work (created by /cca-lab)
CLAUDE.local.md      your learner profile (git-ignored)
```

## Notes

- **Answer letters:** the draw step's tool output contains the answer letters, so leave that collapsed tool call closed. Randomized letters keep Claude from always keying A or B.
- **Scores:** practice percentages are not scaled scores. Anthropic publishes no raw-to-720 conversion. The readiness checklist in `/cca-coach ready` is a study heuristic.
- **Eligibility:** exams are open to Claude Partner Network members and need a company email domain. Register through the Anthropic Partner Academy.
- **Costs:** labs call the Claude API with your `ANTHROPIC_API_KEY`. Use a small model while iterating.
- The directory also works as a Domain 3 example: project skills with `context: fork`, `disable-model-invocation`, and `argument-hint`; a path-scoped rule; project settings; CLAUDE.md with CLAUDE.local.md.
