# Lab catalog

F1–F4 follow the four official preparation exercises in the CCAR-F guide (Section 8). F5 is added here because Scenario S5 (CI) has no official exercise. P1–P6 are built from the CCAR-P guide's advice to "build and operate at least one end-to-end Claude solution, including RAG, evaluation, and observability" and to "practice architectural decision-making".

Every lab has acceptance checks the learner can observe. A lab is done when every check passes and the learner can explain each one in exam terms.

**Cost note:** use a small current model for iteration (see https://platform.claude.com/docs/en/models/overview), keep batches small, and read `ANTHROPIC_API_KEY` from the environment. Never commit keys.

---

## F1 · Multi-tool support agent with escalation  (official exercise 1)
**Objectives:** 1.1, 1.4, 1.5, 2.1, 2.2, 5.2 · **Scenario:** S1
**Docs:** API [how-tool-use-works](https://platform.claude.com/docs/en/agents-and-tools/tool-use/how-tool-use-works), [handle-tool-calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls); SDK [agent-loop](https://code.claude.com/docs/en/agent-sdk/agent-loop), [hooks](https://code.claude.com/docs/en/agent-sdk/hooks), [custom-tools](https://code.claude.com/docs/en/agent-sdk/custom-tools); MCP [tools](https://modelcontextprotocol.io/specification/2026-07-28/server/tools)

Steps:
1. **Part A, raw loop.** Write the loop yourself with the Messages API: call, check `stop_reason`, run tools, append `tool_result`, repeat until `end_turn`. Mock the backends as in-memory dicts.
2. Define 4 tools: `get_customer`, `lookup_order`, `process_refund`, `escalate_to_human`. Make two of them confusable on purpose, for example both accepting an ID string with one-line descriptions.
3. Write 10 ambiguous test prompts ("check order #12345 for jane@x.com") and record routing accuracy. Then rewrite the descriptions with input formats, examples, and when-not-to-use guidance, and measure again.
4. Return structured errors: `isError: true` plus `errorCategory` (transient/validation/business/permission), `isRetryable`, and a message. Inject a timeout and a policy violation.
5. **Part B, Agent SDK.** Port the tools to the SDK as custom tools. Add a pre-tool hook that blocks `process_refund` above $500 and blocks any refund before `get_customer` returned a verified ID. Blocked calls redirect to `escalate_to_human`.
6. Add a post-tool hook that normalizes mixed timestamp formats (Unix vs ISO 8601) and numeric status codes.
7. Test multi-concern messages ("refund order A, and why was I double-billed on B?").

Acceptance checks:
- [ ] Loop ends only on `end_turn`. Any safety cap exists only as a logged anomaly, not the stop condition.
- [ ] Routing accuracy on the 10 prompts improved after the description rewrite (record before/after).
- [ ] Transient errors are retried and business errors are explained to the customer without retry.
- [ ] Refund > $500 is blocked by code, not prompt text, and the handoff contains customer ID, root cause, amount, and recommended action.
- [ ] A refund attempt before identity verification is blocked deterministically.
- [ ] The multi-concern message gets one unified reply covering both issues.
- [ ] "I want a human" escalates immediately, without investigation first.

## F2 · Claude Code team configuration  (official exercise 2)
**Objectives:** 3.1, 3.2, 3.3, 3.4, 2.4 · **Scenarios:** S2, S4
**Docs:** CC [memory](https://code.claude.com/docs/en/memory), [skills](https://code.claude.com/docs/en/skills), [mcp](https://code.claude.com/docs/en/mcp), [common-workflows](https://code.claude.com/docs/en/common-workflows), [sub-agents](https://code.claude.com/docs/en/sub-agents)

Use any repo, or a copy of this study directory.
1. Write a project CLAUDE.md with coding standards and testing conventions. Use `@import` for one standards file.
2. Add `.claude/rules/` files with `paths:` globs: one for `src/api/**/*`, one for `**/*.test.*`. Confirm a rule loads only when Claude touches a matching file (ask Claude which rules are active, or check `/context`).
3. Create a project skill with `context: fork`. Try `allowed-tools`, then `disallowed-tools`, and write down how current behavior differs from the exam guide's wording (drift row 3).
4. Add a shared MCP server in `.mcp.json` using `${VAR}` for a credential. Add a personal server with `claude mcp add --scope user`. Confirm both appear together in `claude mcp list`.
5. Run three tasks: a one-file bug fix (direct), a multi-file rename or migration (plan mode), and a feature with two valid designs (plan mode). Note where plan mode paid off.
6. Put an instruction only in `~/.claude/CLAUDE.md` and show that a teammate (or a fresh user scope) wouldn't get it. Use `/memory` to see what's loaded.

Acceptance checks:
- [ ] Path-scoped rule demonstrably loads only for matching files.
- [ ] Forked skill output stays out of the main conversation.
- [ ] No secret is committed. `.mcp.json` uses `${VAR}`.
- [ ] Both MCP servers are available at once.
- [ ] Written plan-mode vs direct notes for all three tasks.
- [ ] Can explain project vs user vs local scope for memory, skills, and MCP.

## F3 · Structured extraction pipeline  (official exercise 3)
**Objectives:** 4.2, 4.3, 4.4, 4.5, 5.5 · **Scenario:** S6
**Docs:** API [structured-outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs), [define-tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools), [batch-processing](https://platform.claude.com/docs/en/build-with-claude/batch-processing)

1. Make about 30 synthetic documents in 3 formats, such as invoices as tables, as prose, and as emails. It's fine to have Claude generate them. Some must be missing fields, and some must have totals that don't add up.
2. Define an extraction tool schema with required, optional, and nullable fields, an enum with `"unclear"`, and `"other"` + detail. Force it with `tool_choice`.
3. Validate with Pydantic or JSON Schema plus semantic checks (`calculated_total` vs `stated_total`, `conflict_detected`).
4. Retry with the document, the failed output, and the specific errors. Log which failures were fixable (format) and which weren't (info absent).
5. Add 2–4 few-shot examples covering format variety and measure the change.
6. Send the set through the Message Batches API with `custom_id`s. Resubmit only failures. Write down the SLA math for a 30-hour guarantee.
7. Add field-level confidence and route low-confidence or conflicting docs to a human queue. Report accuracy by document type and field, not just overall.

Acceptance checks:
- [ ] Missing info comes back `null`, never invented.
- [ ] The retry log separates resolvable from unresolvable failures.
- [ ] Batch failures are resubmitted by `custom_id` only.
- [ ] Accuracy is reported per doc type and per field.
- [ ] You can explain why tool use removes syntax errors but not semantic ones.

## F4 · Multi-agent research pipeline  (official exercise 4)
**Objectives:** 1.2, 1.3, 2.3, 5.3, 5.6 · **Scenario:** S3
**Docs:** SDK [subagents](https://code.claude.com/docs/en/agent-sdk/subagents), [sessions](https://code.claude.com/docs/en/agent-sdk/sessions); engineering [multi-agent-research-system](https://www.anthropic.com/engineering/multi-agent-research-system)

1. Build an Agent SDK coordinator with at least 2 subagents defined via `agents` (search, analysis; optionally synthesis). The coordinator's allowed tools include the subagent tool. That is `Agent` in current docs and `Task` in the exam guide.
2. Pass findings explicitly in each subagent prompt and confirm nothing is inherited.
3. Spawn subagents in parallel (several calls in one response) and measure latency against sequential.
4. Subagent output schema: claim, evidence excerpt, source URL/doc, publication date.
5. Simulate a search timeout. The coordinator receives failure type, attempted query, partial results, and alternatives, continues, and annotates coverage gaps.
6. Feed two credible sources with conflicting statistics and check that both survive with attribution.
7. Stretch: fork a session (`fork_session`) to compare two synthesis strategies from the same research baseline.

Acceptance checks:
- [ ] Measured parallel vs sequential latency.
- [ ] Every claim in the report maps to a source and date.
- [ ] Timeout leads to a partial report with explicit gaps, not a crash or a silent omission.
- [ ] Conflicts are shown, not resolved arbitrarily.
- [ ] Each subagent has only the tools its role needs.

## F5 · Claude Code in CI  (added; covers Scenario S5)
**Objectives:** 3.6, 4.1, 4.2, 4.4, 4.6 · **Scenario:** S5
**Docs:** CC [headless](https://code.claude.com/docs/en/headless), [cli-reference](https://code.claude.com/docs/en/cli-reference), [github-actions](https://code.claude.com/docs/en/github-actions), [best-practices](https://code.claude.com/docs/en/best-practices)

1. Pick a repo with a few recent diffs. Write a review script that runs `claude -p` with `--output-format json` and `--json-schema` (fields: file, line, severity, category, detected_pattern, message, suggested_fix).
2. Write explicit report/skip criteria and severity definitions with code examples. Compare against a vague "only report high-confidence issues" prompt on the same diffs.
3. Run review in a separate invocation from generation and compare it with self-review in the generating session.
4. Re-run after a new commit, passing prior findings, and report only new or unresolved ones.
5. Optional: wire it into GitHub Actions or GitLab CI per the docs.

Acceptance checks:
- [ ] Runs unattended, with no interactive hang.
- [ ] Output parses against the schema every run.
- [ ] Measured false positives: explicit criteria vs vague prompt.
- [ ] Re-review produces no duplicate comments.

---

## P1 · RAG with evaluation and observability
**Objectives:** P3.4, P3.5, P3.6, P4.1, P4.2, P4.4, P4.6 · **Docs:** engineering [contextual-retrieval](https://www.anthropic.com/engineering/contextual-retrieval); API [embeddings](https://platform.claude.com/docs/en/build-with-claude/embeddings), [citations](https://platform.claude.com/docs/en/build-with-claude/citations), [search-results](https://platform.claude.com/docs/en/build-with-claude/search-results), [opentelemetry](https://platform.claude.com/docs/en/manage-claude/opentelemetry)

1. Corpus: the official docs pages listed in `reference/official-sources.md`, fetched as `.md`. This doubles as a study tool.
2. Build two chunkers (fixed-size vs heading-aware) and add contextual chunk headers. Use embeddings and/or BM25 with a hybrid merge.
3. Answer with citations to chunks.
4. Eval set: 30 questions with gold source pages. Metrics: retrieval recall@k, answer correctness (LLM grader checked by hand on 10), latency p50/p95, cost per query.
5. Instrument traces (OpenTelemetry or structured logs) with retrieval scores per request.
6. "Refresh" the corpus with a deliberately broken re-index and diagnose it from the traces and metrics alone (the official sample P-S3 pattern).

Acceptance checks:
- [ ] Chunking comparison table on the same eval set.
- [ ] Dashboard or log query that would have caught the broken re-index.
- [ ] Written choice of retrieval strategy, justified by data shape and query pattern.

## P2 · Least-privilege and auth review
**Objectives:** P3.1, P3.2, P5.1, P5.2, P5.3 · **Docs:** MCP [authorization](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization); https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices ; SDK [permissions](https://code.claude.com/docs/en/agent-sdk/permissions), [secure-deployment](https://code.claude.com/docs/en/agent-sdk/secure-deployment); CC [permissions](https://code.claude.com/docs/en/permissions)

1. Choose a target: the F1 agent, or an MCP server or agent design from your real work.
2. Inventory every tool and scope against the roles that use it. Flag capability bloat.
3. Trace the auth path end to end. Look for over-scoped tokens, token passthrough, confused deputy risks, shared service credentials, and missing per-user delegation.
4. For each destructive action, decide between removing it, a deterministic gate, or human-in-the-loop, and justify the choice.
5. Write a findings table: risk, evidence, severity, fix, control type (preventive/detective/compensating).

Acceptance checks:
- [ ] Every fix is labeled preventive, detective, or compensating, and least-privilege fixes are preventive (removal).
- [ ] At least one auth gap traced to a specific spec requirement.

## P3 · Integration decision record
**Objectives:** P3.3, P3.7, P3.8, P6.2, P6.4 · **Docs:** MCP [transports](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports); API [mcp-connector](https://platform.claude.com/docs/en/agents-and-tools/mcp-connector), [tool-search-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool); engineering [code-execution-with-mcp](https://www.anthropic.com/engineering/code-execution-with-mcp), [writing-tools-for-agents](https://www.anthropic.com/engineering/writing-tools-for-agents)

1. Pick a real integration: a system your agents must reach, such as a ticketing system or a database.
2. Write an ADR that compares MCP, direct API/CLI, and agent-to-agent, and compares progressive discovery against loading every tool up front. Cover accuracy, latency, cost, security, operability, and team skills.
3. Claude then role-plays a skeptical CTO and a security lead reviewing it. Defend the decision, then revise.

Acceptance checks:
- [ ] The ADR states context, options, decision, consequences, and the reversal trigger (what evidence would change the decision).
- [ ] Both reviewer personas' strongest objections are answered in the final version.

## P4 · Eval-driven optimization (A/B)
**Objectives:** P2.1, P2.5, P4.1, P4.3, P4.5 · **Docs:** API [develop-tests](https://platform.claude.com/docs/en/test-and-evaluate/develop-tests), [prompt-caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching), [choosing-a-model](https://platform.claude.com/docs/en/about-claude/models/choosing-a-model)

1. Take a task from F3 or P1 with an eval set.
2. A/B two prompt variants, then two model tiers, holding everything else fixed. Use enough items to see a real difference, and report the spread.
3. Reorder the prompt so static content comes first, enable prompt caching, and measure latency and cost.
4. Write a one-page decision memo with a recommendation and its trade-offs.

Acceptance checks:
- [ ] Metrics cover accuracy, latency, and cost for every arm.
- [ ] Measured caching effect.
- [ ] The memo states what result would reverse the decision.

## P5 · Team enablement plan
**Objectives:** P7.1, P7.2, P7.3, P6.5 · **Docs:** CC [admin-setup](https://code.claude.com/docs/en/admin-setup), [managed-settings](https://code.claude.com/docs/en/managed-settings), [permissions](https://code.claude.com/docs/en/permissions), [skills](https://code.claude.com/docs/en/skills), [overview](https://code.claude.com/docs/en/plugins/overview), [analytics](https://code.claude.com/docs/en/analytics), [troubleshooting](https://code.claude.com/docs/en/troubleshooting)

Design a Claude Code rollout for a 20-person team:
1. Managed vs project vs user settings and permission policy.
2. Shared skills, rules, and MCP servers, and how they are distributed (repo vs plugin).
3. An onboarding guide and a troubleshooting runbook for the top 5 likely failures.
4. Usage and outcome metrics.

Acceptance checks:
- [ ] Every setting is placed at the right scope, with a reason.
- [ ] The runbook has symptom → diagnosis → fix for each failure.

## P6 · Stakeholder discovery role-play
**Objectives:** P1.1, P1.6, P5.4, P5.5, P6.1, P6.3, P6.5

Claude plays three stakeholders for a regulated use case, for example claims triage at an insurer handling health data:
- a business owner focused on ROI and a deadline
- a compliance officer concerned with HIPAA/GDPR, retention, and auditability
- a support lead worried about customer experience

1. Run structured discovery. Claude answers in character and reveals constraints only when asked well.
2. Write the requirements, success metrics, SLA proposal, risk register (including bias and fairness), and lifecycle plan (discovery → design → handoff → monitoring → iteration).
3. Claude grades it against a rubric: missed constraints, unmeasurable goals, SLA realism, and compliance gaps.

Acceptance checks:
- [ ] Every stakeholder's hidden constraint was surfaced.
- [ ] Each success metric is measurable and owned.
- [ ] Compliance controls map to specific requirements.
