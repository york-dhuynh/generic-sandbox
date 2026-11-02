# S4 · Developer Productivity with Claude · answers and reverse engineering

Score yourself with the key, then work through every miss and every guess. A guess is a low-confidence answer, even when it was right. For each one, cover the explanation, read the clue, and try to say why the key wins before reading on.

## Answer key

| Q | Key | Objective | Rule in one line |
|---|---|---|---|
| 1 | A | 2.5 Built-in tools | Explore incrementally: Grep for entry points, Read to follow imports, never read everything upfront |
| 2 | A, E | 2.4 MCP configuration | Shared server → committed `.mcp.json`; secrets → `${VAR}` expansion; personal experiments stay out of the repo |
| 3 | C | 5.4 Codebase exploration | Isolate verbose discovery in subagents and persist findings outside the conversation |
| 4 | C | 1.6 Task decomposition | Open-ended work: map, prioritize by impact, then follow a plan that adapts |
| 5 | A | 1.3 Subagent definition | Restrict a subagent's tools in its definition; a prompt can't enforce read-only |
| 6 | B, C | 2.5 Built-in tools | Grep searches file **contents**; Glob matches file **paths** |
| 7 | D | 1.7 Session resumption | After code changes, resume and name the changed files for targeted re-analysis |
| 8 | B | 2.4 MCP tool descriptions | A thin MCP description loses to a familiar built-in; describe what the tool does better |
| 9 | D | 1.1 Agentic loops | Open-ended questions need model-driven tool choice, not a pre-configured decision tree |
| 10 | B | 3.5 Iterative refinement | In an unfamiliar domain, have Claude interview you before it writes code |

---

## Q1 · Key A · Objective 2.5 · Built-in tools

**Question type:** change a strategy. The logs show the process, and you have to find the step that's wrong.

**The clue:** "Glob to list every file", then "Read on the files in alphabetical order", and "after 70 Read calls … still hasn't reached the payments code". The agent is reading before it knows where to look.

**Why A:** The guide's pattern is to build understanding incrementally. Grep the contents for distinctive names to find entry points, then Read only those files and follow their imports outward. Searching narrows 2,400 files to a handful before anything goes into context.

**Why not the others:**
- **B** is still exhaustive reading, just filtered by extension. A TypeScript monorepo is mostly `*.ts`, so nothing improves.
- **C** reads everything in two big directories upfront. It's guessing where the answer lives, and it still floods the context.
- **D** treats the context limit as the problem. The real waste is reading irrelevant files, and a bigger budget just postpones the failure.

**Work it backwards:** When an exploring agent burns context without finding the answer, look at the order of operations. Search (Grep) comes before reading (Read). The option that searches first wins.

**Other ways the exam could ask this:**
- *Same rule, new setting:* "Which module calls `chargeCard`?" Grep for the function name, then Read the matches. Don't open the payments directory file by file.
- *Flip a condition:* if the call sites go through a wrapper module (`payments/index.ts` re-exports `chargeCard` as `charge`), first list the wrapper's exported names, then Grep for each of those names. Grepping only the original name misses callers.
- *Neighboring objective (5.4):* if the investigation is long and early search output starts crowding the context, push verbose searching into a subagent that returns a summary (Q3).

**Current docs:** in Claude Code on macOS, Linux, and WSL, Glob and Grep are left out of the default tool set and Claude searches with `find` and `grep` through Bash. Naming `Glob` or `Grep` in the Agent SDK's tool options, or in a subagent's `tools` without Bash, brings them back. The S4 frame lists Grep and Glob as built-in tools, so answer per the guide.

**Source:** [Tools reference](https://code.claude.com/docs/en/tools-reference) · [Best practices](https://code.claude.com/docs/en/best-practices)

---

## Q2 · Keys A, E · Objective 2.4 · MCP configuration

**Question type:** Select TWO. Each correct option has to stand on its own.

**The clue:** "every engineer who clones … should get the same server configuration" means the config must be shared through version control. "Each engineer has their own GitHub token" means secrets must stay out of the repo. "without affecting teammates" means the experimental server doesn't belong in the shared file at all.

**Why A and E:** Project scope is a `.mcp.json` file at the repository root, checked into version control, so everyone who clones gets the same servers. `${VAR}` expansion in `.mcp.json` pulls each engineer's own token from their environment at runtime, so the file stays shareable and secret-free. An Agent SDK app picks up `.mcp.json` when the `project` setting source is enabled, which it is by default.

**Why not the others:**
- **B** commits a secret to the repository and shares one identity across the whole team.
- **C** gives every teammate an unreviewed server. "Personal and optional" in a name doesn't keep it out of anyone's setup. Personal experiments go in user-level (or local) scope.
- **D** works mechanically, but nothing keeps the configuration identical. Every engineer re-creates it by hand and the setups drift apart. Shared means committed.

**Work it backwards:** Sort each piece of configuration by who should get it. Everyone gets the project file. Each person's secret goes in an environment variable the project file references. Only you get your personal experiment, in user scope. Then pick the options that put each piece in the right place.

**Other ways the exam could ask this:**
- *Same rule, new setting:* a database MCP server needs a connection string. Commit `.mcp.json` with `${DATABASE_URL}` and have each engineer set the variable.
- *Flip a condition:* if only one engineer needs the GitHub server, it belongs in their user scope (`~/.claude.json`), not the committed file.
- *Neighboring objective (2.4, build vs reuse):* the team plans to write a custom Jira MCP server. Prefer the existing community server, and build custom only for team-specific workflows.

**Current docs:** Claude Code has three scopes: **local** (the default; private to you in one project), **project** (`.mcp.json`), and **user** (all your projects). Local and user are both stored in `~/.claude.json`. The guide only distinguishes project (`.mcp.json`) from user (`~/.claude.json`); see drift row 5. The exam answer is the same either way: `.mcp.json` for the team, `~/.claude.json` for you.

**Source:** [Claude Code MCP: scopes and environment variable expansion](https://code.claude.com/docs/en/mcp) · [Agent SDK MCP](https://code.claude.com/docs/en/agent-sdk/mcp)

---

## Q3 · Key C · Objective 5.4 · Large codebase exploration

**Question type:** most effective change, with diagnostic evidence ("context-usage logs").

**The clue:** the guide's degradation signs, quoted almost directly: "a typical repository pattern" instead of the specific class found earlier, and inconsistent answers. The logs name the cause: raw Grep output and full file reads from early exploration fill the conversation.

**Why C:** The guide gives two fixes for this. Subagents isolate verbose exploration, so only their summaries come back. A scratchpad file persists key findings (`LedgerGateway` handles data access) outside the conversation, so they survive however long the session runs.

**Why not the others:**
- **A** is the bigger-context answer. Early findings would still be buried under hours of raw output. A bigger window holds more noise but doesn't improve attention on what matters.
- **B** is a probabilistic patch on the symptom. The agent can't refer back to what has been diluted in its context.
- **D** shifts the burden to engineers and throws away the findings. A fresh session with *no* context starts the investigation over.

**Work it backwards:** "Vague, generic, or inconsistent answers late in a long session" points to context degradation. Ask what's filling the context, then move it out (subagents) and keep what matters somewhere durable (a scratchpad).

**Other ways the exam could ask this:**
- *Same rule, new setting:* a multi-phase migration study. Summarize each phase's findings before spawning the next phase, so phase 3 starts from a summary rather than phase 1's raw output.
- *Flip a condition:* if the session crashes midway, the answer is crash recovery. Each agent exports its state to a file, and the coordinator loads a manifest on resume.
- *Neighboring objective (5.1):* in a conversational agent, the same idea appears as a persistent case-facts block outside the summarized history (S1).

**Current docs:** Claude Code's best practices now say running out of context is rare with 1M-token windows and automatic compaction. Subagents are still recommended for keeping long output, such as a wide search, out of the main conversation. `/compact` with a focus is the in-session tool. The guide's 5.4 still tests degradation signs, scratchpads, and subagent isolation, so answer per the guide.

**Source:** [Agent SDK subagents (context isolation)](https://code.claude.com/docs/en/agent-sdk/subagents) · [Best practices: know what subagents cost](https://code.claude.com/docs/en/best-practices)

---

## Q4 · Key C · Objective 1.6 · Task decomposition

**Question type:** approach to an open-ended task.

**The clue:** "add meaningful test coverage" with no list of targets, an alphabetical file-by-file run, and the result: tests on "trivial getters" while "pricing and refund modules" stay untested. Effort went where the order led, not where the value is.

**Why C:** The guide's pattern for open-ended tasks like this is to map the structure, find the high-impact areas, and then follow a prioritized plan that adapts as you learn. Pricing and refunds carry business risk, so they come first. A plan that adapts can re-rank areas as the agent discovers dependencies and test fixtures.

**Why not the others:**
- **A** is a fixed sequential pipeline. That fits predictable, multi-aspect work, but this task needs judgment about where coverage matters, and directory order repeats the original failure.
- **B** shifts the burden to the engineer. Listing every function that needs tests is the analysis the agent should do.
- **D** is a plausible-sounding heuristic, but it isn't the guide's pattern. It skips stable but critical code such as pricing logic untouched for a year.

**Work it backwards:** Ask whether the task can be fully specified upfront. If not, it's open-ended. Explore first, prioritize by impact, and keep the plan adaptive. If you could write down every step in advance, a fixed pipeline would fit.

**Other ways the exam could ask this:**
- *Same rule, new setting:* "document this legacy system". Map the modules, find the ones engineers struggle with most, then document those first.
- *Flip a condition:* if the task were "for each of these 12 API handlers, add input validation, then update the docs, then add a test", a fixed sequential pipeline (prompt chaining) fits, because every step is known.
- *Neighboring objective (1.6, review):* for a large code review, decompose into per-file local passes plus a separate cross-file integration pass. That's official sample Q10 in the S5 block (guide Q12).

**Source:** CCAR-F guide task 1.6 · [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)

---

## Q5 · Key A · Objective 1.3 · Subagent definition and tool restrictions

**Question type:** most reliable fix. "Reliable" signals that a probabilistic answer isn't enough.

**The clue:** the prompt says read-only and the subagent wrote anyway, through Bash. The `AgentDefinition` "omits the `tools` field". The real gap is in the definition, not the wording.

**Why A:** In the Agent SDK, an `AgentDefinition`'s `tools` field limits the subagent to the listed tools. If you omit it, the subagent inherits every available tool, including Bash, Write, and Edit. Listing `Read`, `Grep`, and `Glob` makes the explorer read-only by construction. A tool you leave out isn't in its session at all.

**Why not the others:**
- **B** is still a prompt. The current prompt already says "never modify files" and failed twice, and a stronger warning is the same mechanism.
- **C** uses few-shot examples, which improve judgment but can't guarantee a boundary. Read-only is a hard rule, not a style preference.
- **D** is a detective, after-the-fact control. Damage happens first and gets cleaned up later, which isn't least privilege.

**Work it backwards:** "The prompt says X but the agent does not-X" plus "most reliable" means moving the rule out of the prompt and into configuration or code. For tool access, that's the subagent's tool list.

**Other ways the exam could ask this:**
- *Same rule, new setting:* a `test-runner` subagent needs to run tests but never edit source. Give it `["Bash", "Read", "Grep"]`, without Write or Edit.
- *Flip a condition:* if the explorer had the right tools but kept producing shallow explanations, the fix is in its prompt (goals and quality criteria), not its tools.
- *Neighboring objective (1.3, context passing):* the explorer gives answers that ignore the files the main agent already identified. Subagents don't inherit the parent's conversation, so pass those paths and findings explicitly in the delegation prompt.

**Current docs:** the subagent tool appears as `Agent` in `tool_use` blocks, but the guide calls it the **Task** tool (drift row 1). `AgentDefinition` also has `disallowedTools`, which removes specific tools from an inherited set.

**Source:** [Agent SDK subagents: tool restrictions and AgentDefinition](https://code.claude.com/docs/en/agent-sdk/subagents)

---

## Q6 · Keys B, C · Objective 2.5 · Built-in tools

**Question type:** Select TWO. It tests whether you know each tool's job.

**The clue:** two different jobs. Finding call sites is a search *inside* files. Listing test files is a match on file *names and paths*.

**Why B and C:** Grep searches file **contents**, so `formatLegacyDate` finds the call sites. Glob matches file **paths** by pattern, and `**/*.test.ts` lists every test file at any depth, wherever it lives in the tree.

**Why not the others:**
- **A** swaps the tools. Glob matches paths, so a bare function name finds only a file *named* `formatLegacyDate`, not the files that call it.
- **D** reads everything upfront, the anti-pattern from Q1. A content search is exactly how you avoid missing call sites without reading every file.
- **E** swaps the tools the other way. Grep's pattern is a regex applied to file contents, so `*.test.ts` doesn't list test files. (The Grep tool does take a separate `glob` filter, but that narrows which files to search; it isn't how you list files.)

**Work it backwards:** For each task, ask whether you're looking for text inside files or for files by name. Inside means Grep; by name means Glob. Then check each option for a swap.

**Other ways the exam could ask this:**
- *Same rule, new setting:* "find all Terraform files under `infra/`" is a Glob job (`infra/**/*.tf`). "Find every place a resource sets `force_destroy = true`" is a Grep job.
- *Flip a condition:* if the next step is editing a call site and the Edit fails because the text appears more than once in the file, the guide's answer is to fall back to Read + Write.
- *Neighboring objective (2.5, wrappers):* if callers import the helper through a re-export under another name, list the wrapper's exported names, then Grep for each of them.

**Current docs:** Edit needs `old_string` to appear exactly once. Current docs say Claude either supplies a longer string with enough surrounding context to make it unique, or sets `replace_all: true`. The guide's answer for a failed non-unique match is to fall back to Read + Write, so answer per the guide. Also see the Glob/Grep default-tool-set note under Q1.

**Source:** [Tools reference: Glob, Grep, and Edit behavior](https://code.claude.com/docs/en/tools-reference)

---

## Q7 · Key D · Objective 1.7 · Session state and resumption

**Question type:** what to do to get a reliable result after a known change.

**The clue:** "rewrote two of those twelve files", plus "resumes the session by ID". The session's analysis is mostly valid, but two files' worth of tool results are stale.

**Why D:** The guide says that when you resume after code changes, you should tell the agent which files changed so it can re-analyze them in a targeted way. The other ten files' analysis is still good. Re-reading the two changed files brings the agent's view up to date before it acts.

**Why not the others:**
- **A** assumes something that isn't true. Sessions persist the *conversation*, not the filesystem. Claude Code may notice a changed file when it edits it, but nothing re-validates the analysis and refactoring candidates it drew from the old reads.
- **B** misuses forking. A fork branches the conversation to explore an *alternative* approach from a shared baseline, and the forked branch carries the same stale reads.
- **C** throws away valid work. Starting over with no context re-reads ten unchanged files to fix a problem in two.

**Work it backwards:** Ask how much of the earlier context is stale. If a little is stale, resume and point the agent at the stale part. If most of it is stale, start fresh with an injected summary. Pick the option that matches the amount of change in the stem.

**Other ways the exam could ask this:**
- *Same rule, new setting:* a long CI investigation session resumes after a dependency bump. Tell the agent the lockfile and two config files changed.
- *Flip a condition:* if the merged PR had restructured most of the package, so the earlier tool results are broadly stale, start a **fresh** session and inject a structured summary of the earlier conclusions instead of resuming.
- *Neighboring objective (1.7, fork):* the engineer wants to compare two refactoring strategies without losing the first. Fork the session so both branches start from the same analysis.

**Source:** CCAR-F guide task 1.7 · [Agent SDK sessions](https://code.claude.com/docs/en/agent-sdk/sessions)

---

## Q8 · Key B · Objective 2.4 · MCP tool descriptions

**Question type:** first step.

**The clue:** the description reads "Searches code." That's two words for a tool that does something Grep can't (semantic search across 40 repositories, with call graphs), while the agent defaults to the built-in it knows.

**Why B:** Tool descriptions are the main signal the model uses to choose a tool. The guide calls this case out specifically: rich MCP tool descriptions stop the agent from preferring built-ins like Grep over a more capable MCP tool. Saying what it indexes, what it returns, and when it beats Grep fixes the root cause cheaply.

**Why not the others:**
- **A** overcorrects. Grep is still the right tool for local text searches, and removing it trades one wrong choice for another.
- **C** uses a deterministic block for a judgment call. Hard enforcement fits rules that must always hold. "Which search tool fits this question" isn't one of those.
- **D** adds token overhead without fixing the underlying description, the same reasoning as official sample Q9 in the S1 block (guide Q2).

**Work it backwards:** "First step" plus a quoted, minimal description means fixing the description. The stem quotes it so you notice how thin it is.

**Other ways the exam could ask this:**
- *Same rule, new setting:* two MCP tools, `get_ticket` and `search_tickets`, are confused because both say "Jira tickets". Rewrite both descriptions with inputs, outputs, and when to use each.
- *Flip a condition:* if the agent made dozens of exploratory calls just to learn what projects and schemas exist, expose that catalog as an MCP **resource** so the agent can read it once instead of probing with tool calls.
- *Neighboring objective (2.3):* if the agent had 60 MCP tools and picked poorly across all of them, the issue is tool count and scope, not one description.

**Source:** CCAR-F guide task 2.4 · [Define tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools) · [Writing tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents)

---

## Q9 · Key D · Objective 1.1 · Agentic loops

**Question type:** design choice. Match the mechanism to the kind of question.

**The clue:** the decision tree works when the question names its location ("what's in `src/auth`?") and fails when "the relevant code is somewhere other than the question suggests". You can't know the path in advance.

**Why D:** The guide contrasts model-driven tool choice with pre-configured decision trees. In an agentic loop, the model sees each result and picks the next call: Grep for "timeout", read the HTTP client, notice the connection pool, follow it. Open-ended investigation needs that adaptivity, because the path depends on what the code reveals.

**Why not the others:**
- **A** adds branches to the wrong design. The tree still can't follow evidence it didn't anticipate, and it gets more brittle with every branch.
- **B** scales the fixed sequence. Reading more files in a predetermined order is still blind to what the first reads showed.
- **C** pairs a classifier with predefined sequences. That's more machinery around the same fixed paths, and it's the over-engineering distractor.

**Work it backwards:** Ask whether the steps depend on what earlier steps find. If yes, the model should choose them in a loop. If the steps are always the same, a fixed workflow is fine and cheaper.

**Other ways the exam could ask this:**
- *Same rule, new setting:* a support agent hard-coded to "always call `lookup_order` first" fails on billing questions with no order. Let the model choose tools based on the request.
- *Flip a condition:* for a repetitive task with identical steps every time ("for each new service, generate the same five boilerplate files"), a fixed workflow is the proportionate design. An agent adds cost and variance.
- *Neighboring objective (1.1, loop control):* once it's a loop, continue while `stop_reason` is `"tool_use"` and stop on `"end_turn"`. Don't parse the text for "done" (S1 Q1).

**Source:** CCAR-F guide task 1.1 · [Agent SDK agent loop](https://code.claude.com/docs/en/agent-sdk/agent-loop) · [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)

---

## Q10 · Key B · Objective 3.5 · Iterative refinement

**Question type:** next step after repeated misses.

**The clue:** a messaging platform the developer "has never used", and requirements the developer "recognized only after reading the code". Neither side had pinned down the requirements before generation started.

**Why B:** The guide's interview pattern: in an unfamiliar domain, have Claude ask questions first. The interview brings up the decisions nobody has made yet (dead-letter handling, idempotency, retry policy, and whatever the next attempt would have missed) *before* code exists. That replaces generate-and-discover with a spec.

**Why not the others:**
- **A** uses emphasis ("be thorough", "follow every convention"). That doesn't supply requirements nobody has stated, and current prompting guidance warns that aggressive emphasis ("CRITICAL: You MUST…") can make recent models overtrigger.
- **C** is trial and error, with the developer's review as the only check. It's slow, and it only catches what the developer happens to notice.
- **D** fixes the three known misses but not the unknown ones. Attempt three will miss something else.

**Work it backwards:** If attempts keep failing on things nobody said, the gap is in the input, not the instructions. Ask whether the developer knows the full requirements. If not, gather them first by interviewing.

**Other ways the exam could ask this:**
- *Same rule, new setting:* an engineer asks for a "compliant audit-log module" in a regulated domain they're new to. Have Claude interview them about retention, PII, and access rules first.
- *Flip a condition:* if the requirements were clear but Claude kept reading a prose convention inconsistently ("use our standard handler shape"), give it 2–3 concrete input/output examples instead.
- *Neighboring objective (3.5, test-driven iteration):* if the behavior can be specified precisely, write the tests first and iterate by sharing failures.

**Source:** CCAR-F guide task 3.5 · [Best practices: brainstorm with Claude first](https://code.claude.com/docs/en/best-practices)

---

## Scenario playbook

### What the frame tells you
| Phrase in the frame | What it puts in play |
|---|---|
| "using the Claude Agent SDK" | `AgentDefinition`, subagent tool lists, sessions (`resume`, `fork_session`), the agent loop. **Not** just Claude Code features |
| "explore unfamiliar codebases, understand legacy systems" | Incremental exploration, context degradation, scratchpads, explorer subagents |
| "generate boilerplate code" | Iterative refinement: the interview pattern, concrete examples, test-first |
| "automate repetitive tasks" | Fixed workflow vs agentic loop; decomposition |
| "built-in tools (Read, Write, Bash, Grep, Glob)" | Which tool fits which job; Edit fallbacks; tool restrictions |
| "integrates with … MCP servers" | `.mcp.json` vs user scope, `${VAR}` secrets, MCP descriptions vs built-ins, resources, community vs custom servers |

### The design to hold in your head
```
engineer ──► main agent (agentic loop: model picks each next tool)
               │  tools: Read, Write, Edit, Bash, Grep, Glob, mcp__* (scoped per role)
               │
               ├─► explorer subagent   tools: [Read, Grep, Glob]   → returns a summary
               ├─► test-runner         tools: [Bash, Read, Grep]   → returns results
               │      (subagents get only their prompt: pass paths and findings explicitly)
               │
               ├─► MCP servers  ← .mcp.json (team, committed, ${VAR} secrets)
               │                ← ~/.claude.json (personal experiments)
               │      rich tool descriptions · resources for catalogs/schemas
               │
               └─ state: scratchpad findings file · session resume/fork · crash manifest
```

### Question families
| Family | What the stem looks like | Deciding rule | Objectives |
|---|---|---|---|
| Wasteful exploration | "listed every file, read alphabetically" | Grep for entry points, Read to follow imports | 2.5 |
| Wrong tool for the job | "Glob for a function name", "Grep for `*.test.ts`" | Grep = contents, Glob = paths | 2.5 |
| Edit failures | "Edit fails: text appears more than once" | Guide: fall back to Read + Write | 2.5 |
| Team vs personal MCP | "every engineer who clones", "try it myself" | `.mcp.json` for the team, user scope for personal, `${VAR}` for secrets | 2.4 |
| MCP tool ignored | "still uses Grep", thin description | Rich MCP tool description | 2.4 |
| Exploratory call spam | "dozens of calls to learn the schema" | Expose a catalog as an MCP resource | 2.4 |
| Build vs reuse | "write our own Jira server" | Community server first; custom only for team-specific needs | 2.4 |
| Long-session drift | "typical pattern" instead of the class found earlier | Subagents for verbose discovery, scratchpad, summarize between phases | 5.4 |
| Subagent overreach | "read-only prompt, but it edited files" | Restrict `tools` in the `AgentDefinition` | 1.3 |
| Open-ended task | "add tests to legacy code" | Map → prioritize by impact → adaptive plan | 1.6 |
| Stale session | "teammate merged changes overnight" | Resume and name the changed files; if mostly stale, start fresh with a summary | 1.7 |
| Fixed path fails | "decision tree works only when the question names the folder" | Model-driven tool choice in a loop | 1.1 |
| Requirements surprise | "unfamiliar platform, missed what nobody said" | Interview first; examples or tests when the spec is known | 3.5 |

### The tension S4 is built around
**How much should you decide for the agent, and how much should it decide for itself?**
- Hard boundaries go in configuration: what a subagent may touch (`tools`), where shared config lives (`.mcp.json`), and how secrets are supplied (`${VAR}`).
- Investigation goes to the model: which file to read next, which tool fits, and which area matters most. Decision trees, alphabetical scans, and fixed sequences are distractors when the path depends on what the code reveals.

Most S4 items ask which side of that line the stem's problem falls on.

### Traps that recur in S4
- **S4 is the Agent SDK, not just Claude Code.** The frame says you're *building* a tool with the SDK. Expect `AgentDefinition`, subagent `tools`, `resume`/`fork_session`, and the agent loop. Don't reflexively answer with Claude Code-only features such as plan mode or slash commands unless the stem puts you in the team's Claude Code setup.
- **Swapped tools:** Glob for contents or Grep for file names is a favorite distractor.
- **Read everything first** looks thorough, and it's always wrong for exploration.
- **Bigger context window** for drift caused by noise. Isolate and persist instead.
- **Prompt-only read-only:** a prompt can't remove a tool. The definition can.
- **Removing a useful built-in** (Grep) to force an MCP tool. Fix the description instead.
- **Fork as a staleness fix:** forking branches the conversation, including its stale reads.
