# S2 · Code Generation with Claude Code · answers and reverse engineering

Score yourself with the key, then work through every miss and every guess. A guess is a low-confidence answer, even when it was right. For each one, cover the explanation, read the clue, and try to say why the key wins before reading on.

## Answer key

| Q | Key | Objective | Rule in one line |
|---|---|---|---|
| 1 | D | 3.1 CLAUDE.md hierarchy | "Works for me, not for them" means the instruction lives in a personal file; team standards go in the project `CLAUDE.md` |
| 2 | C | 3.4 Plan vs direct | A well-scoped fix with a known location gets direct execution; plan mode is for stated complexity |
| 3 | C | 3.5 Iterative refinement | When prose is read inconsistently, 2–3 concrete input/output examples beat more prose |
| 4 | D | 5.4 Context degradation | Persist findings outside the context, compact, and isolate further exploration in subagents |
| 5 | A, E | 3.2 Skills | `context: fork` isolates verbose output; `argument-hint` signals the expected argument |
| 6 | C | 1.7 Session resumption | Resume and name the changed files when only a few changed; start fresh when most results are stale |
| 7 | B | 3.5 Interview pattern | In an unfamiliar domain, let Claude ask the questions before it builds |
| 8 | A | 3.2 Commands *(official)* | Shared via version control means the project `.claude/` directory |
| 9 | A | 3.4 Plan mode *(official)* | Stated architectural, multi-file complexity means plan mode first |
| 10 | A | 3.3 Path rules *(official)* | Conventions by file type across directories go in `.claude/rules/` with `paths:` globs |

---

## Q1 · Key D · Objective 3.1 · CLAUDE.md hierarchy

**Question type:** root cause and fix. The stem gives you an asymmetry to explain.

**The clue:** "Claude follows this reliably for you" but not for "two teammates who joined last week", and the project `CLAUDE.md` "covers only build and test commands". The convention has to be loading from somewhere only you have.

**Why D:** `~/.claude/CLAUDE.md` holds personal preferences for all of *your* projects. Only you see it, and it never reaches the repository. A team standard written there works perfectly on your machine and doesn't exist on anyone else's. The project `CLAUDE.md` (or `.claude/CLAUDE.md`) is shared through version control, so that's where team conventions belong. The guide names this as the classic hierarchy bug.

**Why not the others:**
- **A** invents a caching problem. CLAUDE.md files load at session start, and the teammates have no file containing the rule in the first place.
- **B** gets the scope right (shareable) and the mechanism wrong. Skills load on demand, and a convention every handler must follow belongs in always-loaded instructions. Requiring a manual invocation also shifts the burden to developers.
- **C** blames the model for a missing instruction. No model follows a rule it was never given.

**Work it backwards:** When behavior differs between people on the same repository, compare what each person loads. The scope that differs is the user-level layer.

**Other ways the exam could ask this:**
- *Same rule, new setting:* a personal MCP server in your `~/.claude.json` works for you, but CI and teammates can't see the tool. Team servers go in the project `.mcp.json` (task 2.4).
- *Flip a condition:* if the instruction were your personal preference (for example, "explain diffs to me in bullet points"), the user-level file is exactly right. Moving it to the project would impose it on everyone.
- *Neighboring objective (3.1, diagnosis):* "How do you confirm which instruction files Claude actually loaded?" The guide's answer is `/memory`.

**Current docs:** `/memory` lists memory file locations and opens them for editing. `/context` shows which `CLAUDE.md` files actually loaded, under **Memory files**. On the exam, answer `/memory` (drift row 10).

**Source:** [Claude Code memory](https://code.claude.com/docs/en/memory)

---

## Q2 · Key C · Objective 3.4 · Plan mode vs direct execution

**Question type:** choose an approach, with a social-pressure distractor ("plan mode 'to be safe'").

**The clue:** "stack trace pointing to `formatCurrency()`", one named file, and the fix is fully described ("a null check plus a regression test"). The location is known, the scope is one function, and there's one valid approach.

**Why C:** The guide reserves plan mode for large-scale or multi-file changes, multiple valid approaches, and architectural decisions. A single-file fix with a stack trace is its own example of direct execution. Hand Claude the stack trace and the desired outcome, including the test that proves the fix.

**Why not the others:**
- **A** spends exploration on a task whose answer is already known. Plan mode's value is designing *before* committing, and here there's nothing to design.
- **B** uses the interview pattern, which suits unfamiliar domains with unknown requirements (compare Q7). The requirement here is obvious: don't throw on `null`.
- **D** adds an Explore subagent for discovery that isn't needed. The stack trace already did the discovery.

**Work it backwards:** Before choosing a mode, ask whether you can state the change in one sentence. If you can, use direct execution. If the stem says "dozens of files", "service boundaries", or "multiple approaches", use plan mode.

**Other ways the exam could ask this:**
- *Same rule, new setting:* add one input-validation check to a single form field. Direct execution.
- *Flip a condition:* if the null came from a schema change that affects 45 call sites across three services, plan first, then execute. This is official sample Q9's logic.
- *Neighboring objective (3.4, Explore subagent):* you need to understand an unfamiliar subsystem before planning, and discovery would flood your context. Use an Explore subagent and keep only its summary.

**Source:** CCAR-F guide task 3.4 · [Common workflows: plan before editing](https://code.claude.com/docs/en/common-workflows) · [Permission modes](https://code.claude.com/docs/en/permission-modes)

---

## Q3 · Key C · Objective 3.5 · Iterative refinement

**Question type:** next step, after a failed approach repeated four times.

**The clue:** "three paragraphs of prose" and "after four rounds of rewording", yet a third of the output is still inconsistent. The prose is being read inconsistently, and more prose won't fix that.

**Why C:** The guide says that when prose instructions are interpreted inconsistently, 2–3 concrete input/output examples are more effective than more description. A real commit next to its exact changelog line shows tense, voice, grouping, and omission all at once. Including one internal refactor that maps to *no* entry teaches the omission rule directly.

**Why not the others:**
- **A** turns up the volume on the same prose. Emphasis doesn't make a rule less ambiguous.
- **B** asks for self-review. The model checks its output against the same rules it already reads inconsistently.
- **D** fixes *loading*, which isn't the problem. The rules are already in the conversation. They're just being interpreted unevenly.

**Work it backwards:** If an instruction is clearly present and still produces inconsistent output, the gap is in interpretation. Show, don't tell.

**Other ways the exam could ask this:**
- *Same rule, new setting:* Claude formats generated API docs differently on every run despite a style description. Give two complete examples of a finished doc block.
- *Flip a condition:* if the entries were *correct* but Claude ignored the rule only in files under `docs/`, the issue is loading, and a path-scoped rule could be right (3.3).
- *Neighboring objective (3.5, test-driven iteration):* when correctness can be checked by running code, write the tests first and share the failures. Tests serve as examples Claude can run.

**Current docs:** the prompting guide recommends 3–5 examples; the exam guide says 2–4. Don't let the count decide an item (drift row 11).

**Source:** CCAR-F guide task 3.5 · [Prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) · [Claude Code best practices](https://code.claude.com/docs/en/best-practices)

---

## Q4 · Key D · Objective 5.4 · Large codebase exploration

**Question type:** what to do next, with work still remaining ("two subsystems are still left").

**The clue:** "three hours in one session", answers that "contradict what it found earlier", and "typical repository patterns" instead of named classes. These are the guide's exact signs of context degradation.

**Why D:** It does all three things the guide prescribes, in order:
1. Persist what matters outside the conversation (a scratchpad file).
2. Shrink the noisy history (`/compact`).
3. Keep the rest of the verbose exploration out of the main context (subagents return summaries).

The findings survive, and the context that was drowning them is cleared.

**Why not the others:**
- **A** adds more text to a context that is already degrading. The recap competes with the same noise.
- **B** is the "bigger window" reflex. More room doesn't restore attention to findings buried mid-conversation.
- **C** throws away three hours of correct work. Starting fresh only makes sense *with* the findings carried over.

**Work it backwards:** When Claude starts losing specifics in a long session, the fix has two parts: save the specifics somewhere durable, and reduce what's competing with them. Pick the option that does both.

**Other ways the exam could ask this:**
- *Same rule, new setting:* an Agent SDK exploration tool crashes halfway through a multi-agent analysis. Each agent exports its state, and the coordinator resumes from a manifest (task 5.4, crash recovery).
- *Flip a condition:* if you were starting the investigation fresh, the best first move is to delegate verbose discovery to subagents from the outset, so degradation never builds up.
- *Neighboring objective (1.7):* if you had to stop for the day, a named session plus a written summary lets you resume or restart cleanly (Q6).

**Current docs:** most current models have a 1M-token window and Claude Code compacts automatically, so running out is now rare. The docs still recommend `/compact` with a focus, `/clear` between unrelated tasks, and subagents to keep noisy output out of the main conversation. Degradation in a long, noisy session is still what the exam tests.

**Source:** CCAR-F guide task 5.4 · [Context window](https://code.claude.com/docs/en/context-window) · [Best practices: keep cost and context down](https://code.claude.com/docs/en/best-practices)

---

## Q5 · Keys A, E · Objective 3.2 · Skills frontmatter

**Question type:** Select TWO. Each answer has to fix one of the two stated problems.

**The clue:** two named problems, each pointing to one frontmatter field:
- "Output floods their main conversation" points to `context: fork`.
- "Invoke it without saying which workspace" points to `argument-hint`.

**Why A and E:**
- `context: fork` runs the skill in a forked subagent with its own context. Only the result returns to the conversation, which is exactly what the guide says the field is for.
- `argument-hint` is shown during autocomplete to signal the expected argument. When people forget an argument, the hint tells them what to type.

**Why not the others:**
- **B** changes *who* can trigger the skill (users only, not Claude). That isn't either stated problem.
- **C** moves a team tool to personal scope. Teammates lose the shared version, and neither problem is fixed.
- **D** loads hundreds of lines of procedure into every session, which makes the context problem worse. Skills exist so procedures load only on demand.

**Work it backwards:** Match each symptom to the field whose documented purpose fixes it. Distractors use real fields with the wrong purpose.

**Other ways the exam could ask this:**
- *Same rule, new setting:* a `/migrate-endpoint` skill must not run destructive shell commands. The exam answer is to restrict tools with `allowed-tools`.
- *Flip a condition:* if Claude kept triggering the skill on its own at the wrong times, `disable-model-invocation: true` becomes the right answer.
- *Neighboring objective (3.2, scope):* one developer wants a personal variant of a team skill. Put it in `~/.claude/skills/` under a *different name*, so teammates are unaffected and the project version isn't shadowed.

**Current docs:** `allowed-tools` *pre-approves* tools for the turn that invokes the skill. Restricting tools is done with `disallowed-tools`. On the exam, treat `allowed-tools` as the restriction mechanism (drift row 3). When personal and project skills share a name, the personal one wins, which is why the variant needs a different name.

**Source:** [Claude Code skills](https://code.claude.com/docs/en/skills)

---

## Q6 · Key C · Objective 1.7 · Session state and resumption

**Question type:** best approach, with a proportion to weigh (3 of 20 files changed).

**The clue:** "a long named session", "about 20 files", and "changed 3 of those files". Most of the analysis is still valid. A small, known part is stale.

**Why C:** A resumed session restores its history, including the old tool results, so Claude still holds yesterday's contents of the 3 changed files. The guide's rule: when resuming after code changes, tell the agent which files changed so it re-analyzes just those. You keep the 17 files' worth of valid analysis and refresh the rest.

**Why not the others:**
- **A** resumes with stale tool results and no warning. Claude will reason from code that no longer exists.
- **B** throws away valid work. Starting fresh is right when *most* prior results are stale, and it should come with an injected structured summary.
- **D** misuses forking. `--fork-session` creates a branch to explore a different approach from a shared starting point. It doesn't refresh stale content, so the branch has the same old file reads.

**Work it backwards:** Ask how much of the saved context is still true. Mostly true: resume and name the changes. Mostly stale: start fresh with a summary. Exploring an alternative: fork.

**Other ways the exam could ask this:**
- *Same rule, new setting:* an Agent SDK code-analysis agent resumes a session after a dependency upgrade touched 2 modules. Resume, and tell it which modules changed.
- *Flip a condition:* if the teammate's PR had rewritten 15 of the 20 files, start a new session and inject a structured summary of yesterday's conclusions instead of resuming.
- *Neighboring objective (1.7, forking):* you want to compare two refactoring strategies from the same analysis. Fork the session (`--fork-session`, or `fork_session` in the SDK) and try each branch.

**Current docs:** sessions can be named with `--name`/`-n` or `/rename` and resumed with `claude --resume <name>`. `/branch` and `--fork-session` copy a conversation into a new session. The guide's `--resume <session-name>` is still valid (drift row 8).

**Source:** [Manage sessions](https://code.claude.com/docs/en/sessions) · [CLI reference](https://code.claude.com/docs/en/cli-reference)

---

## Q7 · Key B · Objective 3.5 · Interview pattern

**Question type:** what to do *before* the next attempt. It asks about process, not code.

**The clue:** "You don't know the regulations well" and "requirements you hadn't thought to mention". The missing information is in neither the code nor your head as a list. It has to be drawn out.

**Why B:** The guide's interview pattern is for unfamiliar domains. Have Claude ask questions first so hidden requirements surface before implementation. The Claude Code best practices describe the same move: ask Claude to interview you until it could write the spec, then build from the spec.

**Why not the others:**
- **A** explores the *codebase*. The gap is in the *requirements*, which aren't in the code.
- **C** repeats the failure mode. You can only list the rules you already know, and the misses came from the ones you don't.
- **D** uses test-driven iteration, which is excellent when you know the requirements. Here the tests would encode the same blind spots.

**Work it backwards:** Identify where the missing information lives. If it's in the code, explore. If it's in a check you can run, write tests. If it's in a domain you only half know, get Claude to interview you.

**Other ways the exam could ask this:**
- *Same rule, new setting:* building a tax-calculation module for a country whose rules you don't know. Have Claude interview you before writing the spec.
- *Flip a condition:* if the requirements were fully known and the problem was regressions on edge cases, write the tests first and share the failures.
- *Neighboring objective (3.5, issue batching):* you have three bugs that interact. Describe them together in one detailed message. If they're independent, fix them one at a time.

**Source:** CCAR-F guide task 3.5 · [Claude Code best practices](https://code.claude.com/docs/en/best-practices)

---

## Q8 · Key A · Objective 3.2 · *Official sample*

**Official rationale (condensed):** project-scoped commands go in `.claude/commands/` in the repository, version-controlled and available to everyone who clones or pulls. `~/.claude/commands/` (B) is personal. `CLAUDE.md` (C) is for instructions, not command definitions. `.claude/config.json` with a commands array (D) doesn't exist.

**The clue:** "available to every developer when they clone or pull the repository" means the file must be in the repository.

**Work it backwards:** "Shared via VCS" means the project's `.claude/` directory. "Just me" means `~/.claude/`. An option naming a config file you've never seen in docs is probably fictional.

**Other ways the exam could ask this:**
- *Same rule, new setting:* a team MCP server everyone should get on clone goes in the project `.mcp.json`, with `${VAR}` expansion for secrets.
- *Flip a condition:* if the command were your own experiment, `~/.claude/commands/` is right.
- *Neighboring objective (3.1):* Q1. The same scope logic applies to instructions.

**Current docs:** custom commands have been merged into skills. `.claude/commands/review.md` and `.claude/skills/review/SKILL.md` both create `/review`, and skills are preferred. On the exam, `.claude/commands/` is the keyed answer (drift row 2).

**Source:** CCAR-F guide §9 Q4 · [Claude Code skills](https://code.claude.com/docs/en/skills)

---

## Q9 · Key A · Objective 3.4 · *Official sample*

**Official rationale (condensed):** plan mode is designed for large-scale changes, multiple valid approaches, and architectural decisions, which describes a monolith-to-microservices split exactly. Incremental direct execution (B) risks late rework. Detailed upfront instructions (C) assume you already know the structure. Waiting for complexity to appear (D) ignores that the stem already states it.

**The clue:** "dozens of files" and "decisions about service boundaries". The complexity is *stated*, not hypothetical.

**Work it backwards:** This is the mirror of Q2. Count files, look for words like architecture, boundaries, or "multiple approaches", and choose the mode that matches.

**Other ways the exam could ask this:**
- *Same rule, new setting:* migrating 45 files from one logging library to another, with several valid adapter designs. Plan mode.
- *Flip a condition:* a one-file fix with a stack trace calls for direct execution (Q2).
- *Neighboring objective (3.4, combine):* once the plan is approved, execute directly. Plan the migration, then implement each step.

**Source:** CCAR-F guide §9 Q5 · [Common workflows](https://code.claude.com/docs/en/common-workflows)

---

## Q10 · Key A · Objective 3.3 · *Official sample*

**Official rationale (condensed):** `.claude/rules/` with glob patterns (for example `**/*.test.tsx`) applies conventions automatically by file path, regardless of directory, which matters because test files are spread everywhere. A root-level `CLAUDE.md` (B) relies on inference. Skills (C) depend on invocation or Claude choosing to load them. Subdirectory `CLAUDE.md` files (D) are tied to one directory and can't follow scattered files.

**The clue:** "spread throughout the codebase" and "regardless of location". The convention follows a *file type*, not a folder.

**Work it backwards:** Ask whether the convention follows a directory or a file pattern. Directory: a subdirectory `CLAUDE.md` works. Pattern across directories: use `.claude/rules/` with `paths:` globs.

**Other ways the exam could ask this:**
- *Same rule, new setting:* Terraform conventions for every `terraform/**/*` file across several service folders. A path-scoped rule.
- *Flip a condition:* if every file in `packages/billing/` (and only there) needs a convention, a `CLAUDE.md` in that directory is simple and correct.
- *Neighboring objective (3.1):* the root `CLAUDE.md` has grown into a monolith of topics. Split it into topic files in `.claude/rules/`.

**Current docs:** skills now support a `paths` frontmatter field for auto-activation. Path-scoped rules remain the documented home for conventions, and the exam keys rules (drift row 4).

**Source:** CCAR-F guide §9 Q6 · [Claude Code memory: path-specific rules](https://code.claude.com/docs/en/memory)

---

## Scenario playbook

### What the frame tells you
| Phrase in the frame | What it puts in play |
|---|---|
| "Your **team** uses it" | Scope: shared vs personal, project vs user, what reaches teammates through VCS |
| "code generation, refactoring, debugging, and documentation" | Task size varies, so you need to match the mode to the task |
| "custom slash commands" | `.claude/commands/` vs `~/.claude/commands/`; skills and their frontmatter |
| "CLAUDE.md configurations" | The hierarchy (user / project / subdirectory), `@import`, `.claude/rules/` |
| "when to use plan mode vs direct execution" | Explicitly tested in both directions |
| Primary domains 3 and 5 | Configuration plus context management: long sessions, degradation, resumption |

### The setup to hold in your head
```
~/.claude/CLAUDE.md            personal, all your projects, NOT shared
~/.claude/commands|skills/     personal commands/skills (same name as project: personal wins)
repo/CLAUDE.md                 team standards, always loaded, shared via VCS
repo/.claude/rules/*.md        topic files; `paths:` globs load them per file pattern
repo/.claude/commands|skills/  team commands/skills, on demand
  └─ skill frontmatter: context: fork · argument-hint · allowed-tools (exam: restricts)
repo/sub/CLAUDE.md             loads when Claude works in that directory

Task arrives ─► state the change in one sentence?
                 ├─ yes → direct execution
                 └─ no (many files, boundaries, several approaches) → plan mode → then execute
Long session ─► findings to a scratchpad → /compact → subagents for verbose discovery
Next day     ─► resume + name changed files (few stale) | fresh + summary (mostly stale) | fork (try an alternative)
```

### Question families
| Family | What the stem looks like | Deciding rule | Objectives |
|---|---|---|---|
| Works for me, not for them | "teammates don't get the convention" | Personal file vs project file | 3.1 |
| Where does this file go | "available to everyone on clone" | Shared means project `.claude/`; personal means `~/.claude/` | 3.2, 2.4 |
| Conventions by file type | "test files spread everywhere" | `.claude/rules/` with `paths:` globs | 3.3 |
| Monolithic CLAUDE.md | "900-line CLAUDE.md, instructions missed" | Split into topic rule files or `@import` | 3.1 |
| Skill misbehaves | "floods context", "missing argument", "runs dangerous commands" | `context: fork`, `argument-hint`, `allowed-tools` | 3.2 |
| Plan or direct | "dozens of files" vs "stack trace, one function" | Match the mode to the stated scope | 3.4 |
| Inconsistent output | "rewrote the instructions four times" | Concrete input/output examples | 3.5 |
| Unknown requirements | "unfamiliar domain, missed requirements" | Interview pattern | 3.5 |
| Correctness checkable by tests | "regressions on edge cases" | Test-driven iteration: tests first, share failures | 3.5 |
| Long session drifts | "typical patterns", contradictions | Scratchpad, `/compact`, subagents | 5.4 |
| Resume after changes | "teammate changed 3 files overnight" | Resume and name the changes, or start fresh with a summary | 1.7 |

### The tension S2 is built around
**Scope and size.** Almost every S2 item asks one of two questions:
- *Who* should this apply to? The answer decides the user, project, or path scope.
- *How big* is this task? The answer decides plan mode or direct execution.

The official samples test one side of each (shared command, big refactor, cross-directory convention). Expect the exam to test the other side too: the personal preference, the one-line fix, the single-directory convention.

### Traps that recur in S2
- **Fictional configuration:** `.claude/config.json`, a "commands array", or env vars you've never seen. If it isn't in the docs, it's a distractor.
- **Always use plan mode:** plan mode is a tool for stated complexity, not a safety blanket.
- **More prose:** rewording, capital letters, and "double-check" options lose to examples.
- **Bigger context window:** never the fix for degradation in a long session.
- **Skill vs CLAUDE.md:** always-on standards go in CLAUDE.md or rules. On-demand procedures go in skills. Options that swap the two are distractors.
- **Exam keys vs current docs:** `.claude/commands/` (drift 2), `allowed-tools` as a restriction (drift 3), `/memory` (drift 10). Answer per the guide.
