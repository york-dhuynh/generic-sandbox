# S4 · Developer Productivity with Claude · exam block

Answer cold: no docs, no notes, no Claude. Allow about 2 minutes per item (20 minutes for the block). Write a letter and a confidence (H/M/L) for each item, then open [answers.md](answers.md). To have Claude run the block, score it, and walk you back through each miss, use `/cca-scenario S4` instead.

The official exam guide publishes **no sample questions for this scenario**, so all 10 items here are practice items written to the guide's task statements.

## Scenario

You are building developer productivity tools using the Claude Agent SDK. The agent helps engineers explore unfamiliar codebases, understand legacy systems, generate boilerplate code, and automate repetitive tasks. It uses the built-in tools (Read, Write, Bash, Grep, Glob) and integrates with Model Context Protocol (MCP) servers.

---

### Q1

In a 2,400-file monorepo, an engineer asks the agent: "Where is the retry policy for outbound payment calls configured, and which services use it?" Logs show the agent first uses Glob to list every file under `src/`, then calls Read on the files in alphabetical order. After 70 Read calls it has filled most of its context and still hasn't reached the payments code. How should the agent's exploration strategy change?

A. Grep for terms like `retryPolicy` to find entry points, then Read those files and follow their imports.
B. Glob for every `*.ts` file first, then Read each match in turn until the retry configuration turns up.
C. Read every file under `src/config/` and `src/services/` in full first, so the agent has complete context.
D. Raise the agent's context budget so it can keep every file it has read in view while it continues scanning.

### Q2

The agent uses a community GitHub MCP server. Every engineer who clones the tools repository should get the same server configuration, and each engineer has their own GitHub token. One engineer also wants to try an experimental, unreviewed MCP server for a personal side project without affecting teammates. Which TWO configuration choices are correct? **(Select TWO.)**

A. Define the GitHub server in `.mcp.json` at the repository root and commit it to version control.
B. Put a shared service-account GitHub token in the committed `.mcp.json` so every setup works immediately.
C. Add the experimental server to the committed `.mcp.json` under a name marking it as personal and optional.
D. Have each engineer add the GitHub server to their own user-level configuration, following a setup wiki page.
E. Reference the token in `.mcp.json` as `${GITHUB_TOKEN}`, so each engineer's own environment supplies it.

### Q3

Engineers use the agent for multi-hour investigations of a legacy billing system. Late in long sessions its answers drift. It describes "a typical repository pattern" for data access instead of naming the `LedgerGateway` class it identified an hour earlier, and it gives different answers to the same question. Context-usage logs show the conversation is dominated by raw Grep output and full file reads from early exploration. What is the most effective change?

A. Move to a model with a larger context window so early findings stay in view for the whole investigation.
B. Add a system prompt rule telling the agent to always refer back to the specific classes it found earlier.
C. Run verbose searches in subagents that return summaries, and keep key findings in a scratchpad file.
D. Cap each investigation at 30 minutes, then have the engineer start a new session with no prior context.

### Q4

An engineer asks the agent to "add meaningful test coverage to the legacy order-processing service". The service has 310 files and about 4% coverage. The first version of the agent started at the alphabetically first file and wrote tests file by file. After two days, most new tests covered trivial getters, while the pricing and refund modules were still untested. How should the agent approach this task?

A. Run a fixed pipeline that generates tests for every file in directory order and runs the suite at the end.
B. Have the engineer list every function that needs tests before the agent writes any test code at all.
C. Map the structure, rank areas by business impact, then work a prioritized plan that adapts.
D. Write tests only for files changed in the last 90 days, since recent changes are most likely to have bugs.

### Q5

The main agent delegates "explain how this legacy module works" requests to a subagent named `explorer`. The explorer's system prompt says "You are read-only: never modify files." In two incidents, `explorer` ran `sed -i` through Bash to fix a typo it noticed while reading. Its `AgentDefinition` currently omits the `tools` field. What is the most reliable fix?

A. Set the explorer's `tools` to `["Read", "Grep", "Glob"]`, so Write, Edit, and Bash are unavailable.
B. Strengthen the explorer's prompt with a warning that any file it modifies will be rejected in code review.
C. Add few-shot examples to the explorer's prompt that show it reporting typos instead of fixing them.
D. Have the main agent check the explorer's transcript after each run and revert any files that it changed.

### Q6

An engineer asks the agent to prepare for removing a deprecated helper, `formatLegacyDate`. The work includes finding every call site and listing the project's test files, which live next to the code they test throughout the tree. Which TWO tool choices are appropriate? **(Select TWO.)**

A. Use Glob with the pattern `formatLegacyDate` to find every file in the repository that calls the helper.
B. Use Grep to search file contents for `formatLegacyDate` to find every call site in the codebase.
C. Use Glob with the pattern `**/*.test.ts` to list the test files, wherever they live in the tree.
D. Use Read on every file under `src/` first, so that no call site can be missed by a search.
E. Use Grep with the pattern `*.test.ts` to list every test file that exists in the repository.

### Q7

Yesterday an engineer ran a long session in which the agent analyzed the `inventory` package, read twelve of its files, and identified three refactoring candidates. Overnight, a teammate merged a PR that rewrote two of those twelve files. Today the engineer resumes the session by ID and asks the agent to start the refactor. What should the engineer do to get a reliable result?

A. Resume as is, because the agent detects changed files on disk and refreshes its earlier analysis by itself.
B. Fork the session with `fork_session`, so the original analysis is preserved while the refactor goes ahead.
C. Start a new session with no prior context and repeat the full analysis of all twelve files from scratch.
D. Resume, tell the agent which two files changed, and have it re-read and re-check them before acting.

### Q8

The team added an internal MCP server that exposes `search_code_index`. The tool queries a semantic index over all 40 company repositories and returns symbol definitions with their call graphs. Logs show the agent still uses Grep for 85% of cross-repository questions, which produces slow, incomplete answers. The MCP tool's description reads "Searches code." What is the most effective first step?

A. Remove Grep from the agent's tools so that it has to use `search_code_index` for every search it runs.
B. Expand the MCP tool's description: what it indexes, what it returns, and when to prefer it over Grep.
C. Add a `PreToolUse` hook that blocks Grep and redirects every search request to `search_code_index`.
D. Add few-shot examples to the system prompt that show cross-repository questions routed to the MCP tool.

### Q9

The first version of the tool hard-codes a decision tree for every question: run Glob on the directory the question names, Read the first five matches, then answer. It works for questions like "what's in `src/auth`?" It fails on questions like "why does checkout time out under load?", where the relevant code is somewhere other than the question suggests. What design change best fits these open-ended questions?

A. Extend the decision tree with more branches that map common question keywords to likely directories.
B. Increase the number of files read in the fixed sequence from five to twenty-five for each question.
C. Add a classifier that sorts questions into categories and runs a predefined tool sequence for each.
D. Run an agentic loop where the model picks each next tool call from what earlier results showed.

### Q10

Engineers use the tool to generate boilerplate for new internal services. A developer asks it to "scaffold a new event-consumer service following our conventions" on a messaging platform the developer has never used. The first two attempts both looked plausible but missed requirements the developer recognized only after reading the code: dead-letter handling, idempotency keys, and the team's retry policy. What should the developer do next?

A. Write a longer, more emphatic prompt that tells the agent to be thorough and to follow every convention.
B. Have the agent interview the developer about requirements and edge cases before it writes any code.
C. Let the agent keep regenerating the service until one version passes the developer's manual review.
D. Split the request into three separate prompts, one for each of the requirements the attempts missed.
