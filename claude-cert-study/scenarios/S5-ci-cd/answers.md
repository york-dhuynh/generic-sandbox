# S5 · Claude Code for Continuous Integration · answers and reverse engineering

Score yourself with the key, then work through every miss and every guess. A guess is a low-confidence answer, even when it was right. For each one, cover the explanation, read the clue, and try to say why the key wins before reading on.

## Answer key

| Q | Key | Objective | Rule in one line |
|---|---|---|---|
| 1 | C | 4.2 Few-shot | When explicit instructions still give inconsistent output, add examples |
| 2 | B | 4.4 Feedback loops | To analyze patterns later, add a structured field that names the pattern now |
| 3 | B, D | 4.1 Explicit criteria | Pause the noisy category to restore trust; fix it with a specific categorical criterion |
| 4 | D | 3.6 CI/CD | Code consumes the output, so enforce a schema with `--output-format json --json-schema` |
| 5 | C | 3.6 CI/CD | Each CI run is stateless; pass prior findings and report only new or unaddressed issues |
| 6 | D | 4.6 Multi-instance review | The author's own session is a weak reviewer; use an independent instance |
| 7 | C | 3.6 / 3.1 CI context | Standards and fixtures go in project CLAUDE.md; existing tests go in context |
| 8 | A | 3.6 CI/CD *(official)* | Non-interactive CI runs use `-p` |
| 9 | A | 4.5 Batches *(official)* | Batch only what nobody is waiting on |
| 10 | A | 1.6 / 4.6 Multi-pass *(official)* | Many files in one pass dilute attention; use per-file passes plus an integration pass |

---

## Q1 · Key C · Objective 4.2 · Few-shot prompting

**Question type:** most effective next step, after instructions have already been tried.

**The clue:** "already lists explicit review criteria and the required output format", but findings still leave out fields and severities still vary. Detailed instructions alone are producing inconsistent results. That is the guide's trigger for few-shot.

**Why C:** The guide calls few-shot examples the most effective technique for consistently formatted, actionable output when detailed instructions alone are inconsistent. Examples *show* the complete shape (location, issue, severity, suggested fix) and how a given kind of issue maps to a severity. The model can then generalize that judgment to issues the examples don't cover.

**Why not the others:**
- **A** is more of the same instruction, which is already being read inconsistently. Emphasis isn't specificity. Current docs also note that piling on emphasis tends to make Claude over-apply a rule.
- **B** filters findings by self-reported confidence. That doesn't make the remaining findings complete or their severities consistent, and self-confidence is poorly calibrated.
- **D** is the "bigger model" reflex. The proportionate step is to show the model what you want before buying more capacity.

**Work it backwards:** First ask whether instructions have been tried. If the stem says yes and the output is still inconsistent in format or judgment, the next lever is examples. If the stem says the instructions are vague ("be thorough"), the first fix is explicit criteria (Q3).

**Other ways the exam could ask this:**
- *Same rule, new setting:* an extraction pipeline (S6) returns null for a field that appears in different places across invoice layouts. Few-shot examples covering the varied document structures fix it.
- *Flip a condition:* if the prompt said only "review this code" with no criteria and no format, the first step is explicit criteria and a defined output format (4.1), not examples.
- *Neighboring objective (3.6 / 4.3):* if the only problem were *missing fields*, a schema that marks `suggested_fix` as required guarantees the field is present. A schema enforces structure; examples teach judgment, such as which severity to choose. Know which problem the stem describes.

**Current docs:** the guide says 2–4 examples, and the prompting guide says 3–5 (drift row 11). Never let the count decide an item; "a few" satisfies both.

**Source:** [Prompting best practices · Use examples effectively](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)

---

## Q2 · Key B · Objective 4.4 · Feedback loop design

**Question type:** which design enables a specific analysis.

**The clue:** "which kinds of code trigger the dismissed findings" and "fix the prompt systematically". You need a structured signal tied to the code construct that you can group and count.

**Why B:** The guide's feedback-loop pattern is to add a `detected_pattern` field to structured findings so dismissals can be analyzed by the construct that triggered them. Once dismissals group by pattern (for example, "80% of dismissed findings are `logger.warn` inside retry loops"), you can write a targeted criterion or a few-shot example for that exact pattern.

**Why not the others:**
- **A** shifts the work onto developers and produces free text that is hard to aggregate. Friction also means many dismissals will come with no reason at all.
- **C** relies on self-reported confidence, which is miscalibrated. Even if it were accurate, it wouldn't tell you *which code construct* produces the false positives.
- **D** stores unstructured data that doesn't scale. Someone would have to read transcripts to rebuild the pattern a field could have recorded.

**Work it backwards:** When the goal is to find patterns across many outputs, add a structured field at generation time that names the thing you'll group by. Options that collect more prose or ask for a confidence score don't give you that.

**Other ways the exam could ask this:**
- *Same rule, new setting:* an extraction pipeline (S6) extracts `calculated_total` alongside `stated_total`, so discrepancies get flagged automatically instead of being found by hand.
- *Flip a condition:* if developers dismiss findings because the findings are *correct but low priority* (not false positives), the fix is severity criteria with concrete examples, not pattern tracking.
- *Neighboring objective (4.1):* the analysis shows one category produces most dismissals. Temporarily disable that category while you rewrite its criterion (Q3).

**Source:** CCAR-F guide task 4.4 · [Run Claude Code programmatically · structured output](https://code.claude.com/docs/en/headless) (the field goes in your `--json-schema`)

---

## Q3 · Keys B, D · Objective 4.1 · Explicit criteria and false positives

**Question type:** Select TWO. One option restores trust now and the other fixes the cause.

**The clue:**
- "Developers have started ignoring all bot comments, **including correct security findings**". One noisy category is eroding trust in every category.
- The criterion is vague: "check that code comments are accurate".
- "The same comments get flagged on every run". The false positives are systematic, not random.

**Why B and D:** Both are skills listed in the guide.
- **B:** temporarily disable high-false-positive categories to restore developer trust while you improve the prompts for those categories.
- **D:** write specific categorical criteria. The guide's own example is "flag comments only when claimed behavior contradicts actual code behavior" instead of "check that comments are accurate".

**Why not the others:**
- **A** is a general instruction, like "be conservative". The guide says these fail to improve precision compared with specific criteria.
- **C** leaves the noise in front of developers. A lower severity label doesn't restore trust, and it misclassifies the real contradictions too.
- **E** is consensus, and it can't filter systematic false positives. The stem says the same comments are flagged on every run, so two runs will agree on the same false positives. Consensus also suppresses real findings that only show up some of the time, as official sample Q10 points out.

**Work it backwards:** Separate "stop the damage" from "fix the cause". Options that adjust care, severity, or vote counts don't change what the model treats as an issue. Only a sharper criterion does that, and only pausing the category stops the damage while you write it.

**Other ways the exam could ask this:**
- *Same rule, new setting:* in S1, "be conservative about escalating" fails, and explicit escalation criteria with examples fix it.
- *Flip a condition:* as a single-answer item, the question type picks between the two keys. "What should you do first to restore trust this week?" points to B. "What fixes the root cause?" points to D.
- *Neighboring objective (4.2):* after narrowing the criterion, add examples that separate acceptable patterns (slightly outdated wording that's still true) from genuine contradictions.

**Source:** CCAR-F guide task 4.1 · [Prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) · [Claude Code best practices](https://code.claude.com/docs/en/best-practices) ("A reviewer that's asked to find problems will always find *something*")

---

## Q4 · Key D · Objective 3.6 · Structured output in CI

**Question type:** most reliable fix for a pipeline integration.

**The clue:** "parses the prose output with regular expressions" and "the script fails". Code is consuming free text, so the format has to be guaranteed, not requested.

**Why D:** The guide pairs `--output-format json` with `--json-schema` to produce machine-parseable structured findings that can be posted automatically as inline PR comments. The output must conform to your schema, so the script reads fields instead of guessing at prose.

**Why not the others:**
- **A** is probabilistic. Format instructions and examples reduce variation but don't eliminate it, and the regex stays fragile.
- **B** adds a second model call that is just as unvalidated. It also adds latency, cost, and a second place for the format to break.
- **C** confuses streaming with structure. `stream-json` delivers events as they happen, but it doesn't impose a schema on the content, so the text events are still prose.

**Work it backwards:** When code consumes the output, choose the option that enforces a schema. In Claude Code CI, that means these two flags. In the API (S6), it means tool use with a JSON schema.

**Current docs:** with `--json-schema`, the result is in the response's `structured_output` field. If a run ends without valid structured output (for example, Claude declined the request), the field is absent, so check for it before posting. A schema guarantees structure, not correctness; see drift row 6.

**Other ways the exam could ask this:**
- *Same rule, new setting (S6):* an API extraction service gets malformed JSON 3% of the time. Use tool use with a JSON schema, or structured outputs.
- *Flip a condition:* if the review were a summary for humans in a chat channel, plain text is fine. Schema enforcement matters when code consumes the output.
- *Neighboring objective (3.6):* the job never finishes because Claude Code is waiting for input. That's `-p` (Q8).

**Source:** [Run Claude Code programmatically · Get structured output](https://code.claude.com/docs/en/headless) · [CLI reference](https://code.claude.com/docs/en/cli-reference)

---

## Q5 · Key C · Objective 3.6 · Re-review after new commits

**Question type:** fix a duplication problem.

**The clue:** each run "posts all of its findings as new comments", so copies pile up on every push. Each run has no memory of what the previous run said.

**Why C:** The guide's skill is to include prior review findings in context when a review re-runs after new commits, and to tell Claude to report only new or still-unaddressed issues. That removes the duplicates without losing coverage.

**Why not the others:**
- **A** loses coverage. A change in one file can break another, and Claude still can't tell which earlier findings were fixed, so files touched again get duplicate comments.
- **B** destroys the developers' reply threads and still re-posts every open finding on each push, with fresh notifications. The run still doesn't know what was already raised or discussed.
- **D** misses every issue introduced after the first push.

**Work it backwards:** A CI run is stateless. Anything the model needs to know about earlier runs (prior findings, existing tests, team standards) has to be passed in. When a stem describes repeated or duplicated output, look for the option that supplies the missing history.

**Other ways the exam could ask this:**
- *Same rule, new setting:* nightly test generation keeps proposing tests that already exist. Provide the existing test files in context (Q7).
- *Flip a condition:* if the PR had been rebased and largely rewritten, the prior findings would be stale and a fresh full review is the right call. That mirrors 1.7: when earlier results are stale, start fresh instead of resuming.
- *Neighboring objective (1.7):* when resuming an agent session after code changes, tell the agent which files changed so it re-analyzes just those.

**Source:** CCAR-F guide task 3.6 · [Run Claude Code programmatically](https://code.claude.com/docs/en/headless)

---

## Q6 · Key D · Objective 4.6 · Independent review instances

**Question type:** most effective change.

**The clue:** "In the same session, it then sends 'Now review your changes critically'". The reviewer is the author, still carrying the reasoning that produced the bugs.

**Why D:** The guide says a model retains reasoning context from generation, which makes it less likely to question its own decisions. An independent instance without that context catches subtle issues better than self-review instructions *or extended thinking*. Current Claude Code docs say the same thing: "A fresh reviewer does help, because it hasn't seen your reasoning."

**Why not the others:**
- **A** is extended thinking, which the guide names as less effective than an independent instance. More reasoning on the same assumptions still rests on those assumptions.
- **B** forces the reviewer to produce findings. That invents false positives without removing the bias. A reviewer told to find problems will always find *something*.
- **C** splits the review into passes, which fixes attention dilution, not self-review bias. The same session still carries the reasoning that wrote the code.

**Work it backwards:** Ask who is reviewing. If it's the author in the same context, swap the reviewer, not the prompt or the thinking budget.

**Other ways the exam could ask this:**
- *Same rule, new setting:* in an extraction pipeline, have a separate instance validate the extractions instead of asking the extractor to double-check itself.
- *Flip a condition:* if a review of a 14-file PR was uneven in depth and contradicted itself, the problem is attention dilution, and the fix is per-file passes plus an integration pass (Q10). Self-review isn't the issue there.
- *Neighboring objective (3.6):* run the independent reviewer as its own `claude -p` CI job with `--json-schema` output, so its findings post as inline comments.

**Source:** [Claude Code best practices](https://code.claude.com/docs/en/best-practices) (independent reviewer; "a fresh reviewer … hasn't seen your reasoning") · CCAR-F guide task 4.6

---

## Q7 · Key C · Objectives 3.6 / 3.1 · Context for CI-invoked Claude Code

**Question type:** most effective fix for several symptoms at once.

**The clue:** three symptoms, each caused by missing information:
- Duplicate tests: Claude can't see what's already covered.
- Ad hoc mocks: Claude doesn't know the fixtures exist.
- Trivial tests: Claude doesn't know what the team counts as valuable.

The standards live on a wiki page that Claude never reads.

**Why C:** The guide names CLAUDE.md as the mechanism for giving CI-invoked Claude Code its project context: testing standards, fixture conventions, and review criteria. It also says to document what makes a test valuable and which fixtures exist, and to provide existing test files in context so generation doesn't duplicate covered scenarios. Project CLAUDE.md is version-controlled, so every run gets it, CI included.

**Why not the others:**
- **A** is a vague instruction. Claude still can't see which tests exist or which fixtures are available.
- **B** is the classic hierarchy bug from 3.1. `~/.claude/CLAUDE.md` applies only to that person's own sessions on their own machine. The CI job doesn't run as any developer, so it never sees those files.
- **D** treats passing as valuable. Duplicate and trivial tests pass fine, and doubling the output doubles the cost.

**Work it backwards:** For each symptom, ask what information was missing and where it should live:
- Shared, durable standards belong in project CLAUDE.md.
- Per-run facts, such as which tests exist now, go into the prompt context.

**Current docs (drift row 19):** the headless docs now recommend `--bare` for scripted and CI runs. Bare mode skips auto-loading CLAUDE.md, so in that mode you pass the same content with `--append-system-prompt-file`. The GitHub Actions docs still say to define project standards in CLAUDE.md. **On the exam, CLAUDE.md is the answer.**

**Other ways the exam could ask this:**
- *Same rule, new setting (S2):* a new teammate's Claude Code ignores conventions that everyone else's follows, because they live in someone's `~/.claude/CLAUDE.md`. Move them to the project CLAUDE.md.
- *Flip a condition:* if the conventions apply only to test files scattered across many directories, use `.claude/rules/` with a `paths:` glob such as `**/*.test.ts` (3.3).
- *Neighboring objective (3.5):* generated tests mishandle null values. Give specific test cases with example input and expected output.

**Source:** [GitHub Actions · Define project standards in CLAUDE.md](https://code.claude.com/docs/en/github-actions) · [Memory (CLAUDE.md hierarchy)](https://code.claude.com/docs/en/memory) · [Run Claude Code programmatically · bare mode](https://code.claude.com/docs/en/headless)

---

## Q8 · Key A · Objective 3.6 · *Official sample*

**Official rationale (condensed):** `-p` (or `--print`) is the documented way to run Claude Code non-interactively. It processes the prompt, prints the result to stdout, and exits without waiting for input. The other options use features that don't exist (`CLAUDE_HEADLESS`, `--batch`) or a Unix workaround that doesn't address Claude Code's command syntax.

**The clue:** "waiting for interactive input", in a pipeline.

**Work it backwards:** CI plus a hang points to `-p`. Any option naming a flag or environment variable you've never seen in the docs is probably invented. Two of these distractors are.

**Other ways the exam could ask this:**
- *Same rule, new setting:* a cron script runs `claude "Summarize yesterday's commits"` and never exits. The fix is again `-p`.
- *Flip a condition:* if the job finishes but a script can't parse what it printed, the fix is `--output-format json --json-schema` (Q4).
- *Neighboring objective (3.6):* the `-p` run works, but its findings ignore the team's review criteria. Supply them through project CLAUDE.md (Q7).

**Source:** CCAR-F guide §9 Q10 · [Run Claude Code programmatically](https://code.claude.com/docs/en/headless)

---

## Q9 · Key A · Objective 4.5 · *Official sample*

**Official rationale (condensed):**
- The Message Batches API saves 50% but can take up to 24 hours with no guaranteed latency SLA. That makes it wrong for blocking pre-merge checks and right for overnight reports.
- **B** relies on batches "often" finishing faster, which isn't acceptable for a blocking workflow.
- **C** is a misconception, because `custom_id` correlates results.
- **D** adds needless complexity.

**The clue:** "a blocking pre-merge check that must complete before developers can merge" next to "generated overnight".

**Work it backwards:** For each workload, ask whether someone is waiting on it. If yes, use the synchronous API. If no, batch it.

**Other ways the exam could ask this:**
- *Same rule, new setting:* weekly dependency audits and nightly test generation go to batches. Interactive `@claude` replies on a PR stay synchronous.
- *Flip a condition (SLA math):* "Findings must be available within 30 hours of a commit, and batches can take up to 24 hours. How often must you submit?"
  - The worst case is the submission interval plus 24 hours, and that sum must stay within 30.
  - So you need to submit at least every 6 hours. The guide's own example uses 4-hour windows, which leaves margin for collecting results.
  - If the SLA were 12 hours, batches couldn't guarantee it at any submission interval, so the work must stay synchronous.
- *Neighboring objective (4.5, failures):* a few requests in a batch fail because their documents are too large. Resubmit only those `custom_id`s, with the documents chunked. Results can come back in any order, so always match on `custom_id`.

**Current docs:** most batches finish within an hour, but results are only guaranteed by 24 hours, and requests not processed by then expire (unbilled). On the exam, answer "no SLA, up to 24 hours" (drift row 9).

**Source:** CCAR-F guide §9 Q11 · [Batch processing](https://platform.claude.com/docs/en/build-with-claude/batch-processing)

---

## Q10 · Key A · Objectives 1.6 / 4.6 · *Official sample*

**Official rationale (condensed):** splitting the review into focused passes fixes the root cause, attention dilution across many files. File-by-file passes give consistent depth, and a separate integration pass catches cross-file issues. B shifts the burden onto developers. C misunderstands that a bigger context window doesn't fix attention quality. D suppresses real bugs that only some runs catch.

**The clue:** inconsistent depth and contradictory verdicts on *identical code* within a single pass over 14 files.

**Work it backwards:** If quality is uneven *within one pass* over a lot of material, the cause is attention dilution. Split the work into focused passes, and add one pass for whatever crosses the boundaries between them.

**Other ways the exam could ask this:**
- *Same rule, new setting:* test generation for a 20-file module produces thorough tests for a few files and nothing for the rest. Generate per file, then add a separate pass for integration tests.
- *Flip a condition:* if the PR had two files and the review was *consistently* shallow, splitting won't help. The fix is explicit criteria or few-shot examples (Q1, Q3).
- *Neighboring objective (4.6):* the review is consistent but misses subtle bugs in code Claude itself just wrote. Use an independent instance (Q6).

**Source:** CCAR-F guide §9 Q12 · [Claude Code best practices](https://code.claude.com/docs/en/best-practices)

---

## Scenario playbook

### What the frame tells you
| Phrase in the frame | What it puts in play |
|---|---|
| "integrating Claude Code into your CI/CD pipeline" | Non-interactive runs (`-p`), and output that code reads (`--output-format json`, `--json-schema`) |
| "automated code reviews" | Explicit criteria, per-file + integration passes, an independent reviewer instance |
| "generates test cases" | Testing standards and fixtures in project CLAUDE.md, existing tests in context |
| "provides feedback on pull requests" | Inline comments from structured findings, and de-duplication on re-review |
| "design prompts that provide **actionable** feedback" | A complete finding (location, issue, severity, fix), taught with few-shot |
| "**minimize false positives**" | Specific categorical criteria, pausing noisy categories, `detected_pattern` analysis |
| Cost or latency added in the stem | Batches for work nobody waits on, synchronous calls for blocking checks |

### The pipeline to hold in your head
```
PR opened / new push
   │
   ▼
CI job:  claude -p "<review prompt>" --output-format json --json-schema findings.schema.json
   │     context: project CLAUDE.md (criteria, test standards, fixtures)
   │              + prior findings (re-review) + existing tests (test generation)
   │     passes:  per-file local passes ──► cross-file integration pass
   │     reviewer: an independent instance, never the session that wrote the code
   ▼
structured_output.findings[] { file, line, issue, severity, suggested_fix, detected_pattern }
   │
   ├─► inline PR comments  (blocking pre-merge check → synchronous API)
   └─► dismissals grouped by detected_pattern ─► sharpen criteria / pause a noisy category

overnight debt report · nightly test generation ─► Message Batches (50% cheaper, ≤24h, custom_id)
```

### Question families
| Family | What the stem looks like | Deciding rule | Objectives |
|---|---|---|---|
| Pipeline hangs | "waiting for interactive input" | `-p` (watch for invented flags and env vars) | 3.6 |
| Output can't be parsed | "regex", "format varies", "script breaks" | `--output-format json` + `--json-schema` | 3.6 |
| Duplicate comments | "same comments on every push" | Prior findings in context; report only new or unaddressed | 3.6 |
| Poor generated tests | "duplicates coverage", "ignores fixtures", "trivial tests" | Project CLAUDE.md standards + existing tests in context | 3.6, 3.1 |
| Noisy reviews | "be conservative didn't help", "developers ignore the bot" | Specific categorical criteria for what to report and what to skip | 4.1 |
| One category drags trust | "60% false positives in X", "even security findings ignored" | Pause that category; rewrite its criterion | 4.1 |
| Inconsistent format or severity | "instructions already explicit, still inconsistent" | Few-shot examples | 4.2 |
| Why findings get dismissed | "which code triggers dismissals" | `detected_pattern` field | 4.4 |
| Self-review misses bugs | "same session reviews its own changes" | Independent instance | 4.6 |
| Large PR, uneven review | "14 files", "contradictory feedback" | Per-file passes + integration pass | 1.6, 4.6 |
| Cutting cost | "switch everything to batches" | Batch only latency-tolerant work; do the SLA math | 4.5 |

### The tension S5 is built around
**"Actionable feedback" vs "minimize false positives."**
- Reporting more catches more bugs but buries developers in noise.
- Cutting volume bluntly makes the bot quiet but blind.

The exam resolves this by improving precision through specification, not suppression:
- explicit criteria for what to report and what to skip
- examples that teach format and separate acceptable patterns from real issues
- a temporary pause for a broken category
- structured fields you can analyze

Confidence thresholds, caps, consensus votes, "be conservative", and capital-letter warnings all reduce output without changing what the model counts as an issue, and several of them hide real bugs.

### Traps that recur in S5
- **Invented flags and environment variables:** `CLAUDE_HEADLESS`, `--batch`. If you've never seen it in the docs, distrust it.
- **Confidence filters, "be conservative", or emphasis** offered as the fix for false positives.
- **Consensus or majority voting:** it suppresses real bugs that only some runs catch, and can't remove systematic false positives.
- **Bigger model or bigger context window** for what is really an attention or criteria problem.
- **Shifting the burden to developers:** splitting PRs, typing dismissal reasons, deleting their threads.
- **Self-review or extended thinking** offered where an independent reviewer is needed.
- **Batches on a blocking path.**
- **User-level config for CI:** the CI runner isn't you, so `~/.claude/` doesn't travel.
