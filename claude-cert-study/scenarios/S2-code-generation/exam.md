# S2 · Code Generation with Claude Code · exam block

Answer cold: no docs, no notes, no Claude. Allow about 2 minutes per item (20 minutes for the block). Write a letter and a confidence (H/M/L) for each item, then open [answers.md](answers.md). To have Claude run the block, score it, and walk you back through each miss, use `/cca-scenario S2` instead.

## Scenario

You are using Claude Code to accelerate software development. Your team uses it for code generation, refactoring, debugging, and documentation. You need to integrate it into your development workflow with custom slash commands, CLAUDE.md configurations, and understand when to use plan mode vs direct execution.

---

### Q1

Your team's convention is that every new API handler throws the shared `ApiError` class and logs with a `requestId` field. Claude follows this reliably for you. Two teammates who joined last week report that Claude generates handlers with plain `throw new Error()` and no request logging. The project's `CLAUDE.md` covers only build and test commands. What is the most likely cause, and the fix?

A. The teammates' sessions cached an older `CLAUDE.md`; have them run `/clear` and start new sessions.
B. The convention is too detailed for `CLAUDE.md`; move it into a skill teammates invoke before writing handlers.
C. The teammates use a different default model; pin the team's model in the project settings file.
D. The convention lives in your user-level `~/.claude/CLAUDE.md`; move it into the project `CLAUDE.md`.

### Q2

A production error report includes a stack trace pointing to `formatCurrency()` in `src/utils/money.ts`, which throws when the amount is `null`. The fix is a null check plus a regression test. A teammate suggests starting every task in plan mode "to be safe". How should you approach this task?

A. Enter plan mode to explore how `formatCurrency()` is used across the codebase before making any edit.
B. Ask Claude to interview you about the currency-formatting requirements before it writes any code.
C. Use direct execution: give Claude the stack trace and ask for the null check and a regression test.
D. Have an Explore subagent map every caller of `formatCurrency()`, then choose an approach from its summary.

### Q3

You ask Claude to generate changelog entries from commit messages. Your instructions describe the format in three paragraphs of prose: past tense, user-facing language, grouped by component, internal refactors omitted. After four rounds of rewording the instructions, about a third of the entries still mix tenses or include internal refactors. What should you try next?

A. Rewrite the formatting rules in capital letters and label each one as critical.
B. Ask Claude to double-check every entry against the rules before it returns the list.
C. Show 2–3 real commit messages beside the exact entries they should produce.
D. Move the formatting rules into a path-scoped rule file that loads for the changelog.

### Q4

You've spent three hours in one session tracing how orders flow through a legacy monolith. Early on, Claude identified specific classes such as `OrderReconciler` and `LedgerWriter`. Now its answers contradict what it found earlier, and it describes "typical repository patterns" instead of naming those classes. Two subsystems are still left to trace. What should you do?

A. Paste a recap of the earlier findings into the chat and ask Claude to keep it in mind.
B. Switch to a model with a larger context window and keep tracing in the same session.
C. Start a new session and re-trace the order flow from the beginning so findings are fresh.
D. Save findings to a scratchpad file, run `/compact`, and use subagents for the rest.

### Q5

Your team has a project skill, `/audit-deps`, that scans every package manifest, queries vulnerability data, and prints several hundred lines of findings. Developers report two problems:
- The output floods their main conversation, so later answers lose focus.
- People often invoke it without saying which workspace to audit.

Which TWO changes address these problems? **(Select TWO.)**

A. Add `context: fork` so the audit runs in an isolated subagent and only its result comes back.
B. Add `disable-model-invocation: true` so the skill runs only when someone types `/audit-deps`.
C. Move the skill to `~/.claude/skills/audit-deps/` so each developer controls their own copy.
D. Copy the skill's instructions into the project `CLAUDE.md` so the audit steps are always loaded.
E. Add `argument-hint: "[workspace]"` so autocomplete shows that a workspace argument is expected.

### Q6

Yesterday you ran a long named session, `payments-review`, in which Claude read about 20 files in the payments module and built a detailed picture of its retry logic. Overnight, a teammate merged a PR that changed 3 of those files. You want to continue the analysis today. What is the best approach?

A. Resume `payments-review` and carry on as before, since resuming restores the full history.
B. Start a new session and have Claude re-read all 20 files to rebuild its picture from scratch.
C. Resume `payments-review` and tell Claude which 3 files changed so it re-reads and re-checks them.
D. Resume with `--fork-session` so the changed files are analyzed on a branch of the original session.

### Q7

You need Claude to add data-retention handling for a healthcare client. Records must be archived or purged on schedules that depend on record type and jurisdiction. You don't know the regulations well, and your first two attempts produced code that missed requirements you hadn't thought to mention. What should you do before the next attempt?

A. Switch to plan mode so Claude can explore the codebase and design the archival job first.
B. Have Claude interview you on the requirements until it can write a spec, then build.
C. Write a longer prompt listing every retention rule you can think of, then rerun the task.
D. Write tests from your current understanding first, then have Claude iterate until they pass.

---

## Official sample questions (CCAR-F exam guide v1.0, Section 9)

These three are reproduced from the official guide. They show the real exam's style. Answer them cold too, even if you've read them before. What matters is whether you can explain *why* the key wins.

### Q8

You want to create a custom /review slash command that runs your team's standard code review checklist. This command should be available to every developer when they clone or pull the repository. Where should you create this command file?

A. In the `.claude/commands/` directory in the project repository
B. In `~/.claude/commands/` in each developer's home directory
C. In the `CLAUDE.md` file at the project root
D. In a `.claude/config.json` file with a commands array

### Q9

You've been assigned to restructure the team's monolithic application into microservices. This will involve changes across dozens of files and requires decisions about service boundaries and module dependencies. Which approach should you take?

A. Enter plan mode to explore the codebase, understand dependencies, and design an implementation approach before making changes.
B. Start with direct execution and make changes incrementally, letting the implementation reveal the natural service boundaries.
C. Use direct execution with comprehensive upfront instructions detailing exactly how each service should be structured.
D. Begin in direct execution mode and only switch to plan mode if you encounter unexpected complexity during implementation.

### Q10

Your codebase has distinct areas with different coding conventions: React components use functional style with hooks, API handlers use async/await with specific error handling, and database models follow a repository pattern. Test files are spread throughout the codebase alongside the code they test (e.g., `Button.test.tsx` next to `Button.tsx`), and you want all tests to follow the same conventions regardless of location. What's the most maintainable way to ensure Claude automatically applies the correct conventions when generating code?

A. Create rule files in `.claude/rules/` with YAML frontmatter specifying glob patterns to conditionally apply conventions based on file paths
B. Consolidate all conventions in the root `CLAUDE.md` file under headers for each area, relying on Claude to infer which section applies
C. Create skills in `.claude/skills/` for each code type that include the relevant conventions in their `SKILL.md` files
D. Place a separate `CLAUDE.md` file in each subdirectory containing that area's specific conventions
