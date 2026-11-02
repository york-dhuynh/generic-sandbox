# How Architect exam answers are keyed

Every principle below comes from a rationale in the official exam guides. "F-Q4" is Foundations sample question 4 and "P-S1" is Professional sample 1. Read the guide's Section 9 for the full items.

These are tie-breakers between plausible options. They do not replace knowing the material.

## The principles

1. **Fix the root cause the stem gives you.** If logs show the coordinator split "creative industries" into three visual-arts subtasks, blame the decomposition, not the downstream agents that did their jobs (F-Q7). If a single pass over 14 files gives uneven depth, the cause is attention dilution, so split the passes (F-Q12).

2. **Pick the proportionate first step: least machinery that solves the stated problem.** Fix minimal tool descriptions before adding few-shot, routing layers, or tool consolidation (F-Q2). Try explicit escalation criteria + few-shot before training a classifier (F-Q3). Separate batch-eligible and blocking workloads rather than adding fallbacks (F-Q11). Classifiers, routing layers, second models, and consensus voting are usually distractors when a prompt, description, or config fix hasn't been tried.

3. **Deterministic beats probabilistic when the rule must hold.** Identity before refunds, spending limits, compliance: use a programmatic gate or hook, not a stronger prompt or more few-shot (F-Q1, task 1.4/1.5). This flips principle 2: when the stem says errors have financial or compliance consequences, code beats prompts even though it is more machinery.

4. **Least privilege means removal.** Remove tools a role never needs. Logging and confirmation prompts are detective or compensating controls, not least privilege (P-S1). Give a scoped tool for the common case and route the rare case through the coordinator (F-Q9).

5. **Structured, specific information beats generic signals.** Structured error context (type, attempted query, partial results, alternatives) enables recovery. Generic statuses, swallowed errors, and aborting everything do not (F-Q8). Explicit categorical criteria beat "be conservative".

6. **Sentiment and self-reported confidence are poor proxies for complexity.** Self-rated confidence is miscalibrated exactly where the agent is wrong (F-Q3). Sentiment is a different problem from case complexity.

7. **Bigger model or bigger context window is rarely the fix.** A larger context window doesn't fix attention quality (F-Q12). A bigger model doesn't change authorization scope (P-S1). Blindly downsizing hurts quality (P-S2).

8. **Match the mechanism to its documented purpose and scope.**
   - Shared with the team via VCS → project files (`.claude/commands/`, `.mcp.json`, project CLAUDE.md). Personal → `~/.claude/...` (F-Q4).
   - Conventions by file type across directories → `.claude/rules/` with `paths:` globs (F-Q6).
   - Architectural or multi-file work → plan mode, when the complexity is already stated (F-Q5).
   - Non-interactive CI → `-p` (F-Q10).
   - Latency-tolerant bulk work → Batches; blocking → synchronous (F-Q11).

9. **Options naming features that don't exist are wrong.** The guide's own distractors include `CLAUDE_HEADLESS=true`, a `--batch` flag, and `.claude/config.json` with a commands array (F-Q4, F-Q10). If an option sounds plausible but you've never seen it in docs, be suspicious. Use `/cca-verify` while studying.

10. **Keep the context that matters; cut the noise.** Put stable content first and enable caching (P-S2). Trim tool output to relevant fields, keep a case-facts block, put key findings first (task 5.1). Do not truncate needed policy text.

11. **Look at what changed.** A symptom that starts right after a change points at the changed component (P-S3: document refresh → retrieval/indexing).

12. **Don't move the burden to humans or hide problems.** Making developers split PRs (F-Q12), requiring consensus that suppresses intermittent real bugs (F-Q12), and returning empty-as-success (F-Q8) are all distractor patterns.

## Distractor checklist

When two options look right, check each against these traps:

- Over-engineering: classifier, router, second model, ML pipeline, consensus voting
- Probabilistic fix for a deterministic requirement: "strengthen the prompt", "add few-shot"
- Treating the symptom downstream when the stem's logs point upstream
- Detective or compensating control offered as least privilege
- Self-confidence or sentiment as the routing signal
- Bigger model or context window
- A nonexistent flag, env var, or config file
- Wrong scope: user-level where team sharing is required, or the reverse
- Silently swallowing errors, or failing the whole workflow on one error
- Shifting work to users or developers
