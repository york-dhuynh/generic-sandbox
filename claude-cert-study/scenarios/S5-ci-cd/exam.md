# S5 · Claude Code for Continuous Integration · exam block

Answer cold: no docs, no notes, no Claude. Allow about 2 minutes per item (20 minutes for the block). Write a letter and a confidence (H/M/L) for each item, then open [answers.md](answers.md). To have Claude run the block, score it, and walk you back through each miss, use `/cca-scenario S5` instead.

## Scenario

You are integrating Claude Code into your Continuous Integration/Continuous Deployment (CI/CD) pipeline. The system runs automated code reviews, generates test cases, and provides feedback on pull requests. You need to design prompts that provide actionable feedback and minimize false positives.

---

### Q1

Your review prompt already lists explicit review criteria and the required output format for each finding: location, issue, severity, and suggested fix. Across the last 200 pull requests, 35% of findings leave out the suggested fix. Similar issues also get different severities: an unchecked null dereference is "high" in one PR and "low" in the next. What is the most effective next step?

A. Restate the format requirements at both the start and the end of the prompt, in bold.
B. Have Claude add a confidence score to each finding and drop those below a threshold.
C. Add a few complete example findings showing the exact format and the severity chosen for each.
D. Move the review job to a larger model that follows long, detailed instructions more consistently.

### Q2

Developers can dismiss a review finding with one click, and they now dismiss about 40% of findings. You want to find out which kinds of code trigger the dismissed findings, so you can fix the prompt systematically rather than one complaint at a time. Each finding currently has `file`, `line`, `message`, and `severity`. What change best enables this analysis?

A. Require developers to type a free-text reason each time they dismiss a finding.
B. Add a `detected_pattern` field recording which code construct each finding is about.
C. Have Claude rate its confidence on every finding so dismissals can be compared to confidence.
D. Store the full review transcript for each PR so analysts can read why each finding was raised.

### Q3

The review prompt includes a "comment accuracy" category with the criterion "check that code comments are accurate." That category has a 60% false-positive rate, mostly comments whose wording differs slightly from the code but whose meaning is still right. The security category has about a 5% false-positive rate. Sampling shows the same comments get flagged on every run. Developers have started ignoring all bot comments, including correct security findings. Which TWO actions should you take? **(Select TWO.)**

A. Add an instruction asking Claude to be extra careful before posting comment-accuracy findings.
B. Temporarily stop posting comment-accuracy findings while you rework that category's criteria.
C. Keep posting comment-accuracy findings, but downgrade all of them to the lowest severity level.
D. Narrow the criterion: flag a comment only when its claimed behavior contradicts the code.
E. Post a comment-accuracy finding only when two independent review runs both report it.

### Q4

Your pipeline runs `claude -p "Review this diff and list each issue with file, line, and fix"`. A script then parses the prose output with regular expressions to post inline PR comments. In 15% of runs the script fails: some findings are missing line numbers, two findings merge into one paragraph, or a summary heading is mistaken for a finding. What is the most reliable fix?

A. Tell Claude to write every finding as `file:line - message`, and give it two examples to copy.
B. Pipe the review into a second `claude -p` call that converts the prose findings into JSON.
C. Switch to `--output-format stream-json` and parse each text event as soon as it arrives.
D. Run with `--output-format json --json-schema <schema>` and read the structured output.

### Q5

The review job runs on every push to a pull request and reviews the full PR diff each time. Each run posts all of its findings as new comments, so a typical PR now has three copies of most findings, and developers' replies on the earlier copies get buried. What change best fixes this?

A. Review only the files changed in the latest commit, and ignore the rest of the pull request's diff.
B. Delete all of the bot's earlier comments on the pull request before posting each new review.
C. Pass the previous review's findings into the new run, and ask for only new or unaddressed issues.
D. Run the review once when the pull request is opened, and skip the review on later pushes.

### Q6

A pipeline step uses Claude Code to write fixes for failing tests. In the same session, it then sends "Now review your changes critically for bugs." The self-review rarely reports anything, yet human reviewers find subtle bugs in about 20% of these PRs. What is the most effective change?

A. Enable extended thinking for the review step so the model examines its own changes more carefully.
B. Change the review prompt to "Assume your changes contain bugs and list at least three of them."
C. Have the same session review each changed file in its own pass instead of the whole diff at once.
D. Run the review in a separate Claude instance that sees the diff but not the session that wrote it.

### Q7

A nightly job runs `claude -p` to generate tests for recently changed modules. The generated tests have three problems:
- They often repeat scenarios the existing test suite already covers.
- They build ad hoc mock databases instead of using the team's fixtures in `tests/fixtures/`.
- Many test trivial getters.

The team's testing standards (including what counts as a valuable test) and fixture conventions are documented on a wiki page that developers read before writing tests. What is the most effective fix?

A. Add "Write only high-value tests and never duplicate existing coverage" to the job's prompt.
B. Have each developer copy the wiki's testing standards into their own `~/.claude/CLAUDE.md` file.
C. Document the standards and available fixtures in the project CLAUDE.md; pass existing tests in context.
D. Generate twice as many tests in each run, and keep only the ones that pass the first time they are executed.

---

## Official sample questions (CCAR-F exam guide v1.0, Section 9)

These three are reproduced from the official guide. They show the real exam's style. Answer them cold too, even if you've read them before. What matters is whether you can explain *why* the key wins.

### Q8

Your pipeline script runs `claude "Analyze this pull request for security issues"` but the job hangs indefinitely. Logs indicate Claude Code is waiting for interactive input. What's the correct approach to run Claude Code in an automated pipeline?

A. Add the `-p` flag: `claude -p "Analyze this pull request for security issues"`
B. Set the environment variable `CLAUDE_HEADLESS=true` before running the command
C. Redirect stdin from `/dev/null`: `claude "Analyze this pull request for security issues" < /dev/null`
D. Add the `--batch` flag: `claude --batch "Analyze this pull request for security issues"`

### Q9

Your team wants to reduce API costs for automated analysis. Currently, real-time Claude calls power two workflows: (1) a blocking pre-merge check that must complete before developers can merge, and (2) a technical debt report generated overnight for review the next morning. Your manager proposes switching both to the Message Batches API for its 50% cost savings. How should you evaluate this proposal?

A. Use batch processing for the technical debt reports only; keep real-time calls for pre-merge checks.
B. Switch both workflows to batch processing with status polling to check for completion.
C. Keep real-time calls for both workflows to avoid batch result ordering issues.
D. Switch both to batch processing with a timeout fallback to real-time if batches take too long.

### Q10

A pull request modifies 14 files across the stock tracking module. Your single-pass review analyzing all files together produces inconsistent results: detailed feedback for some files but superficial comments for others, obvious bugs missed, and contradictory feedback—flagging a pattern as problematic in one file while approving identical code elsewhere in the same PR. How should you restructure the review?

A. Split into focused passes: analyze each file individually for local issues, then run a separate integration-focused pass examining cross-file data flow.
B. Require developers to split large PRs into smaller submissions of 3-4 files before the automated review runs.
C. Switch to a higher-tier model with a larger context window to give all 14 files adequate attention in one pass.
D. Run three independent review passes on the full PR and only flag issues that appear in at least two of the three runs.
