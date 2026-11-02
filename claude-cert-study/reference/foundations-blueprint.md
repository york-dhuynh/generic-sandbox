# CCAR-F blueprint (Claude Certified Architect – Foundations)

Condensed from the **official exam guide v1.0, effective July 2026**. The guide is the authority on what is tested and how answers are keyed. Re-check the PDF before booking, because Anthropic says the guide "is subject to change without notice".
PDF: https://everpath-course-content.s3-accelerate.amazonaws.com/instructor%2F6nizmqk8tpzpfjvt6qmmav7rh%2Fpublic%2F1783542750%2FClaude+Certified+Architect+%E2%80%93+Foundations+Exam+Guide.pdf

Contents: Exam facts · Domains · Scenarios · Task statements (D1–D5) · In/out of scope · Official exercises

## Exam facts

| Item | Value |
|---|---|
| Code | CCAR-F |
| Items | 60, multiple-choice and multiple-response (each item says how many to select) |
| Structure | 4 scenarios drawn at random from a bank of 6 |
| Time | 120 minutes |
| Pass | Scaled 720 on 100–1,000. No published raw-to-scaled conversion |
| Fee | $125 USD |
| Validity | 12 months; free non-proctored renewal assessment if renewed on time |
| Retakes | Wait 14 / 30 / 90 days after 1st / 2nd / 3rd fail; max 4 attempts per rolling 12 months |
| Audience | Solution architects with ~6+ months building with Claude API, Agent SDK, Claude Code, MCP |

## Domains

| # | Domain | Weight | ≈ items of 60 |
|---|---|---|---|
| 1 | Agentic Architecture & Orchestration | 27% | 16 |
| 2 | Tool Design & MCP Integration | 18% | 11 |
| 3 | Claude Code Configuration & Workflows | 20% | 12 |
| 4 | Prompt Engineering & Structured Output | 20% | 12 |
| 5 | Context Management & Reliability | 15% | 9 |

## Scenarios (4 of these 6 appear)

| ID | Scenario | Setup | Primary domains |
|---|---|---|---|
| S1 | Customer Support Resolution Agent | Agent SDK agent for returns, billing disputes, account issues. Custom MCP tools `get_customer`, `lookup_order`, `process_refund`, `escalate_to_human`. Target 80%+ first-contact resolution while knowing when to escalate. | 1, 2, 5 |
| S2 | Code Generation with Claude Code | Team uses Claude Code for generation, refactoring, debugging, docs. Custom slash commands, CLAUDE.md, plan mode vs direct execution. | 3, 5 |
| S3 | Multi-Agent Research System | Agent SDK coordinator delegating to web-search, document-analysis, synthesis, and report subagents. Produces cited reports. | 1, 2, 5 |
| S4 | Developer Productivity with Claude | Agent SDK tool for exploring unfamiliar/legacy codebases, boilerplate, automation. Built-in tools (Read, Write, Bash, Grep, Glob) plus MCP servers. | 2, 3, 1 |
| S5 | Claude Code for Continuous Integration | Claude Code in CI/CD: automated review, test generation, PR feedback. Prompts must give actionable feedback and minimize false positives. | 3, 4 |
| S6 | Structured Data Extraction | Extract from unstructured documents, validate with JSON schemas, high accuracy, graceful edge cases, downstream integration. | 4, 5 |

## Task statements

Each line condenses the guide's "Knowledge of" and "Skills in" bullets. IDs match the official guide.

### Domain 1 — Agentic Architecture & Orchestration (27%)

**1.1 Agentic loops**
- Loop: send request → inspect `stop_reason` → if `"tool_use"` run tools and append `tool_result` to history → repeat; stop on `"end_turn"`.
- Model-driven tool choice vs pre-configured decision trees.
- Anti-patterns: parsing natural-language "I'm done" signals, arbitrary iteration caps as the *primary* stop, treating presence of assistant text as completion.

**1.2 Coordinator–subagent orchestration**
- Hub-and-spoke: coordinator owns all inter-subagent communication, error handling, routing (observability, consistency).
- Subagents have isolated context and do not inherit the coordinator's history.
- Coordinator decomposes, delegates, aggregates, and picks which subagents to run based on the query, not always the full pipeline.
- Risk: overly narrow decomposition → incomplete coverage. Partition scope to minimize duplication. Iterative refinement: evaluate synthesis for gaps → re-delegate targeted queries → re-synthesize.

**1.3 Subagent invocation, context passing, spawning**
- Exam wording: the **Task** tool spawns subagents and the coordinator's `allowedTools` must include `"Task"` (current docs call it `Agent`; see exam-vs-current-docs.md).
- Context must be passed explicitly in the subagent prompt; no shared memory between invocations.
- `AgentDefinition`: description, system prompt, tool restrictions per subagent type.
- Pass complete prior findings; use structured formats separating content from metadata (URLs, doc names, pages) to keep attribution.
- Parallelism: emit multiple Task calls in **one** coordinator response.
- Coordinator prompts state goals and quality criteria, not step-by-step procedures.
- Fork-based sessions to explore divergent approaches from a shared baseline.
- Current docs add fork subagents that copy the conversation, and run subagents in the background by default. See drift rows 15 and 16.

**1.4 Multi-step workflows: enforcement and handoff**
- Programmatic enforcement (hooks, prerequisite gates) vs prompt guidance. Prompts alone have a non-zero failure rate, so deterministic compliance needs code (e.g., identity verification before financial operations).
- Block `process_refund` until `get_customer` returned a verified ID.
- Decompose multi-concern requests, investigate in parallel with shared context, synthesize one resolution.
- Escalation handoff = structured summary (customer ID, root cause, amount, recommended action) for humans who lack the transcript.

**1.5 Agent SDK hooks**
- `PostToolUse` hooks transform tool results before the model sees them (normalize Unix vs ISO 8601 timestamps, numeric status codes).
- Pre-call interception hooks block policy violations (e.g., refunds > $500) and redirect to escalation.
- Hooks = deterministic guarantees; prompts = probabilistic compliance. Choose hooks when rules must hold.

**1.6 Task decomposition**
- Fixed sequential pipelines (prompt chaining) for predictable multi-aspect work vs dynamic adaptive decomposition for open-ended investigation.
- Large code review: per-file local passes + a separate cross-file integration pass (avoids attention dilution).
- Open-ended tasks ("add tests to legacy code"): map structure → find high-impact areas → prioritized plan that adapts.

**1.7 Session state, resumption, forking**
- `--resume <session-name>` continues a named session. `fork_session` branches from a shared baseline.
- When resuming after code changes, tell the agent which files changed for targeted re-analysis.
- If prior tool results are stale, start fresh with an injected structured summary instead of resuming.

### Domain 2 — Tool Design & MCP Integration (18%)

**2.1 Tool interfaces**
- Descriptions are the primary selection signal. Minimal or overlapping descriptions cause misrouting.
- Include input formats, example queries, edge cases, boundaries, and when to use it vs similar tools.
- Fix overlap by renaming and rewriting (e.g., `analyze_content` → `extract_web_results`), or split generic tools into purpose-specific ones with defined contracts.
- System-prompt keywords can create unintended tool associations that override good descriptions.

**2.2 Structured MCP tool errors**
- MCP `isError` flag reports tool failures to the agent.
- Categories: transient (timeouts, unavailable), validation (bad input), business (policy violation), permission.
- Generic "Operation failed" prevents recovery. Return `errorCategory`, `isRetryable`, and a human-readable description. Business violations get `retriable: false` plus a customer-friendly explanation.
- Subagents recover locally from transient failures and propagate only unresolved errors, with partial results and what was attempted.
- Access failure ≠ valid empty result.

**2.3 Tool distribution and tool_choice**
- Too many tools (18 vs 4–5) degrades selection. Tools outside an agent's role get misused.
- Scope tools per role. Allow limited cross-role tools for high-frequency needs (e.g., `verify_fact` for synthesis), route complex cases via coordinator.
- Replace generic tools with constrained ones (`fetch_url` → `load_document` that validates URLs).
- `tool_choice`: `"auto"` (may answer in text), `"any"` (must call some tool), forced `{"type":"tool","name":"..."}` (must call that tool, e.g., `extract_metadata` first).

**2.4 MCP servers in Claude Code and agents**
- Project scope `.mcp.json` (shared, version-controlled) vs user scope `~/.claude.json` (personal/experimental).
- `${VAR}` expansion in `.mcp.json` keeps secrets out of the repo.
- Tools from all configured servers are discovered at connection and available together.
- MCP **resources** expose content catalogs (issue summaries, doc hierarchies, DB schemas) to cut exploratory tool calls.
- Rich MCP tool descriptions stop the agent preferring built-ins (Grep) over a more capable MCP tool.
- Prefer existing community servers (e.g., Jira) over custom; build custom only for team-specific workflows.

**2.5 Built-in tools**
- Grep = search file contents. Glob = match file paths (`**/*.test.tsx`). Read/Write = whole files. Edit = targeted change by unique text match.
- If Edit fails on a non-unique match, fall back to Read + Write.
- Build understanding incrementally: Grep for entry points → Read to follow imports. Do not read everything upfront.
- Trace usage through wrapper modules: list exported names, then search each.
- Current Claude Code differs on Grep/Glob defaults and on the Edit fallback. See drift rows 12 and 13. Answer per the guide.

### Domain 3 — Claude Code Configuration & Workflows (20%)

**3.1 CLAUDE.md hierarchy**
- User `~/.claude/CLAUDE.md` (only you, not shared) → project `CLAUDE.md` or `.claude/CLAUDE.md` → subdirectory `CLAUDE.md`.
- Classic bug: a teammate misses instructions that live in someone's user-level file.
- `@import` pulls in specific standards files per package. `.claude/rules/` splits a monolith into topic files (testing.md, api-conventions.md).
- `/memory` shows which memory files are loaded, which helps diagnose inconsistent behavior. In current docs, `/context` shows what loaded and `/memory` lists locations (drift row 10).

**3.2 Slash commands and skills**
- Project commands `.claude/commands/` (shared via VCS) vs user `~/.claude/commands/`.
- Skills `.claude/skills/<name>/SKILL.md` with frontmatter: `context: fork` (isolated subagent so verbose output does not pollute the main session), `allowed-tools` (exam framing: restrict tools during the skill), `argument-hint` (prompt for required args).
- Personal variants go in `~/.claude/skills/` under a different name so teammates are unaffected.
- Skills = on-demand, task-specific. CLAUDE.md = always-loaded universal standards.

**3.3 Path-specific rules**
- `.claude/rules/*.md` with YAML `paths:` globs load only when editing matching files, which saves context.
- Beats subdirectory CLAUDE.md when a convention spans directories (`**/*.test.tsx`, `terraform/**/*`).

**3.4 Plan mode vs direct execution**
- Plan mode: large-scale, multi-file, multiple valid approaches, architectural decisions (microservice split, 45+ file migration).
- Direct: well-scoped, clear changes (single-file fix with stack trace, one validation check).
- Combine: plan the migration, then execute directly. Explore subagent isolates verbose discovery and returns a summary.

**3.5 Iterative refinement**
- 2–3 concrete input/output examples beat prose when prose is read inconsistently.
- Test-driven iteration: write tests first, share failures.
- Interview pattern: have Claude ask questions first in unfamiliar domains.
- Interacting issues → one detailed message. Independent issues → fix sequentially.

**3.6 CI/CD**
- `-p` / `--print` for non-interactive runs, which prevents hangs on input.
- `--output-format json` + `--json-schema` for machine-parseable findings that become inline PR comments.
- CLAUDE.md supplies testing standards, fixtures, review criteria to CI runs.
- An independent review instance beats the session that wrote the code.
- On re-review, include prior findings and report only new or unaddressed issues. Provide existing tests to avoid duplicate test suggestions.
- Current headless docs recommend `--bare` for CI, which skips CLAUDE.md. See drift row 19. Answer per the guide.

### Domain 4 — Prompt Engineering & Structured Output (20%)

**4.1 Explicit criteria**
- Specific categorical criteria ("flag comments only when claimed behavior contradicts code") beat "be conservative" or "only high-confidence".
- High false-positive categories destroy trust in accurate ones. Temporarily disable them while fixing.
- Define severity levels with concrete code examples.

**4.2 Few-shot**
- Most effective fix when instructions alone give inconsistent format or quality.
- 2–4 targeted examples of ambiguous cases, showing why one action beats plausible alternatives. Current docs say 3–5 (drift row 11).
- Examples generalize judgment, show output format (location, issue, severity, fix), separate acceptable patterns from real issues, and reduce extraction hallucination across varied document structures.

**4.3 Structured output via tool use + JSON schema**
- Tool use with a JSON schema is the most reliable route to schema-compliant output and eliminates syntax errors, but **not semantic errors** (totals that don't sum, values in wrong fields).
- `tool_choice "any"` when several extraction schemas exist and the doc type is unknown. Forced tool to run a specific extraction first.
- Make fields optional/nullable when sources may lack them, so the model doesn't fabricate. Use enums with `"unclear"`, and `"other"` + detail string.
- Add format-normalization rules alongside strict schemas.
- Forced `tool_choice` (`any` / named tool) returns 400 on the newest models. See drift row 18. Answer per the guide.

**4.4 Validation, retry, feedback loops**
- Retry with error feedback: resend document + failed extraction + specific validation errors.
- Retries fail when the info is absent from the source (vs format/structure errors, which retries fix).
- Add `detected_pattern` to findings to analyze dismissals. Self-check fields: `calculated_total` vs `stated_total`, `conflict_detected`.

**4.5 Batch processing**
- Message Batches API: 50% cheaper, up to 24h, no latency SLA, **no multi-turn tool calling inside a request**, `custom_id` correlates request/response.
- Batch for overnight or weekly work. Synchronous for blocking pre-merge checks.
- SLA math, e.g., submit every 4h to guarantee 30h with 24h processing.
- Resubmit only failed `custom_id`s with fixes (e.g., chunk oversized docs). Refine prompts on a sample before bulk runs.
- Server tools now run inside batch requests. See drift row 20.

**4.6 Multi-instance and multi-pass review**
- Self-review is weak because the model keeps its generation reasoning. An independent instance beats self-review instructions or extended thinking.
- Per-file passes + integration pass. Self-reported confidence per finding for routing.

### Domain 5 — Context Management & Reliability (15%)

**5.1 Long interactions**
- Progressive summarization loses numbers, dates, customer expectations. Keep a persistent "case facts" block outside summarized history.
- Lost-in-the-middle: put key findings first and use explicit section headers.
- Trim verbose tool output to relevant fields (40+ fields → 5) before it accumulates.
- Send full conversation history each request. Upstream agents return structured facts, not verbose reasoning, when downstream context is tight.

**5.2 Escalation and ambiguity**
- Triggers: customer asks for a human (honor immediately), policy exception/gap (policy silent on the case), no meaningful progress.
- Not reliable proxies: sentiment, self-reported confidence.
- Frustrated but solvable: acknowledge, offer resolution, escalate if they repeat the request.
- Multiple customer matches → ask for more identifiers, never guess.
- Fix calibration with explicit criteria + few-shot examples in the system prompt.

**5.3 Error propagation in multi-agent systems**
- Return failure type, attempted query, partial results, alternatives.
- Anti-patterns: generic "search unavailable", silently returning empty-as-success, killing the whole workflow on one failure.
- Synthesis output carries coverage annotations (well-supported vs gaps).

**5.4 Large codebase exploration**
- Degradation signs: inconsistent answers, "typical patterns" instead of specific classes found earlier.
- Scratchpad files persist findings. Subagents isolate verbose exploration. Summarize a phase before spawning the next.
- Crash recovery: each agent exports state; coordinator loads a manifest on resume. `/compact` when discovery output fills context.
- Current docs downplay the context window as a constraint (1M tokens, automatic compaction). See drift row 14. Answer per the guide.

**5.5 Human review and confidence calibration**
- Aggregate accuracy (97%) can hide weak document types or fields. Validate by segment before automating.
- Stratified random sampling of high-confidence outputs to measure error rate and catch novel errors.
- Field-level confidence calibrated on labeled validation sets. Route low-confidence or contradictory docs to humans.

**5.6 Provenance and uncertainty**
- Summaries lose claim→source mapping. Require structured claim-source mappings (URL, doc, excerpt) preserved through synthesis.
- Conflicting credible stats: keep both with attribution. Do not pick one arbitrarily. Let the coordinator reconcile.
- Require publication/collection dates so time differences aren't read as contradictions.
- Separate well-established from contested findings. Render by content type (tables for financials, prose for news).

## In scope / out of scope

**Out of scope (will not appear):** fine-tuning; API auth, billing, account management; language/framework specifics; deploying or hosting MCP servers; Claude internals or training; Constitutional AI/RLHF; embedding models and vector DB details; computer use; vision; streaming/SSE; rate limits, quotas, pricing math; OAuth and key rotation; cloud-provider config; benchmarking; prompt caching details beyond knowing it exists; tokenization.

Several of these (RAG and retrieval, auth gaps, prompt caching, model selection) **are** tested on Professional. See professional-blueprint.md.

## Official preparation exercises (summary)

1. **Multi-tool agent with escalation** (D1, D2, D5): 3–4 MCP tools incl. two confusable ones; stop_reason loop; structured errors (errorCategory, isRetryable); threshold-blocking hook → escalation; multi-concern messages.
2. **Claude Code team workflow** (D3, D2): project CLAUDE.md; `.claude/rules/` with `paths:` globs; project skill with `context: fork` + `allowed-tools`; `.mcp.json` with `${VAR}` + personal server in `~/.claude.json`; compare plan mode vs direct on three task sizes.
3. **Structured extraction pipeline** (D4, D5): schema with required/optional/nullable + enum "other"+detail; validation-retry loop; few-shot for varied formats; batch of 100 via Message Batches with `custom_id` failure handling and SLA math; field-level confidence routing.
4. **Multi-agent research pipeline** (D1, D2, D5): coordinator + ≥2 subagents with explicit context; parallel spawning in one response; claim/evidence/source/date outputs; simulated timeout with structured error; conflicting sources preserved.

The guide's Section 9 has 12 official sample questions with rationales. Do them early because they calibrate the item style. answer-heuristics.md distills their principles.
