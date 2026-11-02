# Official sources

All links were checked live on 2026-10-27. Docs move, so when a link breaks, find the current page in the llms.txt indexes below rather than guessing a URL.

## Source hierarchy

Use this order whenever sources disagree:

1. **Official exam guide.** It defines what is tested and how answers are keyed. Links are in the two blueprint files.
2. **Official product docs.** These cover how things work today: Claude Code + Agent SDK, the Claude API, and the MCP spec.
3. **Other first-party material.** Anthropic engineering articles, Anthropic Academy courses, and the `anthropics` GitHub repos.
4. **Third-party prep** (claudecertificationguide.com, Udemy, blogs). Use these for extra practice only. They are never an authority. When they conflict with tiers 1–2, tiers 1–2 win.

If the exam guide and current docs disagree, answer **exam questions** per the guide and build **real systems** per the docs. Log the conflict in exam-vs-current-docs.md.

## Indexes for finding current pages

| Index | URL |
|---|---|
| Claude Code + Agent SDK docs | https://code.claude.com/docs/llms.txt |
| Claude API (platform) docs | https://platform.claude.com/llms.txt |
| MCP docs and spec | https://modelcontextprotocol.io/llms.txt |

Any docs page can be fetched as Markdown by appending `.md`, for example `https://code.claude.com/docs/en/skills.md`. Note that platform.claude.com returns HTTP 200 even for pages that don't exist. Confirm a platform URL by finding it in its llms.txt, not by status code.

## Certification program (official)

- Certifications hub: https://anthropic-partners.skilljar.com/page/partner-certifications
- CCAR-F prep courses (Partner Academy): https://anthropic-partners.skilljar.com/page/claude-certified-architect-foundations-prep-courses
- CCAR-P learning path (Partner Academy): https://anthropic-partners.skilljar.com/path/claude-certified-architect-professional
- Public Anthropic Academy: https://anthropic.skilljar.com/
  - Building with the Claude API: https://anthropic.skilljar.com/claude-with-the-anthropic-api
  - Claude Code in Action: https://anthropic.skilljar.com/claude-code-in-action
  - Introduction to Model Context Protocol: https://anthropic.skilljar.com/introduction-to-model-context-protocol
  - Model Context Protocol: Advanced Topics: https://anthropic.skilljar.com/model-context-protocol-advanced-topics
  - Introduction to agent skills: https://anthropic.skilljar.com/introduction-to-agent-skills
  - Introduction to subagents: https://anthropic.skilljar.com/introduction-to-subagents
- Anthropic courses repo (prompting, tool use, evals notebooks): https://github.com/anthropics/courses
- Claude cookbooks: https://github.com/anthropics/claude-cookbooks

## Anthropic engineering articles (first-party, high exam value)

| Article | Best for |
|---|---|
| https://www.anthropic.com/engineering/building-effective-agents | Workflows vs agents, prompt chaining, orchestrator-workers, "start simple" (F1.2, F1.6, P1.3) |
| https://www.anthropic.com/engineering/multi-agent-research-system | Coordinator/subagent research systems, parallelism, eval of agents (F1.2–1.3, F5.3, F5.6, P1.4) |
| https://www.anthropic.com/engineering/writing-tools-for-agents | Tool naming, descriptions, consolidation, token-efficient responses (F2.1–2.3, P3.1) |
| https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents | Context as a finite budget, compaction, note-taking, sub-agents (F5.1, F5.4, P2.4) |
| https://www.anthropic.com/engineering/claude-code-best-practices | CLAUDE.md, plan-first, TDD loop, multi-Claude review (F3.x, F4.6) |
| https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk | Agent SDK loop: gather context, act, verify (F1.1, F1.5) |
| https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills | Skills and progressive disclosure (F3.2, P2.5, P3.8) |
| https://www.anthropic.com/engineering/code-execution-with-mcp | Progressive tool discovery vs loading every tool definition (P3.8, P3.1) |
| https://www.anthropic.com/engineering/advanced-tool-use | Tool search, programmatic tool calling, tool examples (F2.3, P3.8) |
| https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents | Agent eval design, graders, datasets (P4.1–4.3) |
| https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents | State persistence across context windows (F5.4) |
| https://www.anthropic.com/engineering/contextual-retrieval | Chunking + contextual embeddings + BM25 + reranking (P3.5, P3.6) |

## Foundations: docs by task statement

Labels: CC = Claude Code docs · SDK = Agent SDK docs · API = Claude API docs · MCP = MCP specification (2026-07-28).

| Task | Official pages |
|---|---|
| 1.1 Agentic loop | API [how-tool-use-works](https://platform.claude.com/docs/en/agents-and-tools/tool-use/how-tool-use-works), [handle-tool-calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls), [handling-stop-reasons](https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons), [build-a-tool-using-agent](https://platform.claude.com/docs/en/agents-and-tools/tool-use/build-a-tool-using-agent); SDK [agent-loop](https://code.claude.com/docs/en/agent-sdk/agent-loop) |
| 1.2 Coordinator–subagent | SDK [subagents](https://code.claude.com/docs/en/agent-sdk/subagents); CC [sub-agents](https://code.claude.com/docs/en/sub-agents); engineering [multi-agent-research-system](https://www.anthropic.com/engineering/multi-agent-research-system) |
| 1.3 Spawning + context passing | SDK [subagents](https://code.claude.com/docs/en/agent-sdk/subagents) (Agent/Task tool, `agents` param, parallel calls), SDK [sessions](https://code.claude.com/docs/en/agent-sdk/sessions) (fork) |
| 1.4 Enforcement + handoff | SDK [hooks](https://code.claude.com/docs/en/agent-sdk/hooks), SDK [permissions](https://code.claude.com/docs/en/agent-sdk/permissions); API [customer-support-chat](https://platform.claude.com/docs/en/about-claude/use-case-guides/customer-support-chat) |
| 1.5 Hooks | SDK [hooks](https://code.claude.com/docs/en/agent-sdk/hooks); CC [hooks](https://code.claude.com/docs/en/hooks), CC [hooks-guide](https://code.claude.com/docs/en/hooks-guide) |
| 1.6 Decomposition | engineering [building-effective-agents](https://www.anthropic.com/engineering/building-effective-agents); CC [common-workflows](https://code.claude.com/docs/en/common-workflows) |
| 1.7 Sessions | SDK [sessions](https://code.claude.com/docs/en/agent-sdk/sessions); CC [sessions](https://code.claude.com/docs/en/sessions); CC [cli-reference](https://code.claude.com/docs/en/cli-reference) (`--resume`, `--name`, `--fork-session`) |
| 2.1 Tool descriptions | API [define-tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools); engineering [writing-tools-for-agents](https://www.anthropic.com/engineering/writing-tools-for-agents) |
| 2.2 Tool errors | MCP [tools](https://modelcontextprotocol.io/specification/2026-07-28/server/tools) (`isError`); API [handle-tool-calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls) (`is_error`) |
| 2.3 Tool scoping, tool_choice | API [define-tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools), [tool-search-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool) (define-tools covers forcing tool use); SDK [subagents](https://code.claude.com/docs/en/agent-sdk/subagents) (per-agent tools) |
| 2.4 MCP in Claude Code | CC [mcp](https://code.claude.com/docs/en/mcp) (scopes, `${VAR}` expansion, `.mcp.json`); SDK [mcp](https://code.claude.com/docs/en/agent-sdk/mcp); MCP [resources](https://modelcontextprotocol.io/specification/2026-07-28/server/resources) |
| 2.5 Built-in tools | CC [tools-reference](https://code.claude.com/docs/en/tools-reference); CC [best-practices](https://code.claude.com/docs/en/best-practices) |
| 3.1 CLAUDE.md hierarchy | CC [memory](https://code.claude.com/docs/en/memory) (hierarchy, `@import`, `.claude/rules/`); CC [commands](https://code.claude.com/docs/en/commands) (`/memory`) |
| 3.2 Commands + skills | CC [skills](https://code.claude.com/docs/en/skills) (frontmatter, `context: fork`, commands merged into skills); CC [sub-agents](https://code.claude.com/docs/en/sub-agents) |
| 3.3 Path-specific rules | CC [memory](https://code.claude.com/docs/en/memory) (section "Path-specific rules") |
| 3.4 Plan mode | CC [common-workflows](https://code.claude.com/docs/en/common-workflows); CC [permission-modes](https://code.claude.com/docs/en/permission-modes); CC [sub-agents](https://code.claude.com/docs/en/sub-agents) (Explore) |
| 3.5 Iterative refinement | CC [best-practices](https://code.claude.com/docs/en/best-practices); engineering [claude-code-best-practices](https://www.anthropic.com/engineering/claude-code-best-practices) |
| 3.6 CI/CD | CC [headless](https://code.claude.com/docs/en/headless); CC [cli-reference](https://code.claude.com/docs/en/cli-reference) (`-p`, `--output-format`, `--json-schema`); CC [github-actions](https://code.claude.com/docs/en/github-actions); CC [gitlab-ci-cd](https://code.claude.com/docs/en/gitlab-ci-cd) |
| 4.1 Explicit criteria | API [claude-prompting-best-practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) |
| 4.2 Few-shot | API [claude-prompting-best-practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices); API [increase-consistency](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/increase-consistency) |
| 4.3 Structured output | API [structured-outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs), [strict-tool-use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/strict-tool-use), [define-tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools); SDK [structured-outputs](https://code.claude.com/docs/en/agent-sdk/structured-outputs) |
| 4.4 Validation + retry | API [structured-outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs); API [reduce-hallucinations](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations) |
| 4.5 Batches | API [batch-processing](https://platform.claude.com/docs/en/build-with-claude/batch-processing) |
| 4.6 Multi-pass review | CC [best-practices](https://code.claude.com/docs/en/best-practices) (writer/reviewer sessions); CC [code-review](https://code.claude.com/docs/en/code-review) |
| 5.1 Long context | API [context-windows](https://platform.claude.com/docs/en/build-with-claude/context-windows), [context-editing](https://platform.claude.com/docs/en/build-with-claude/context-editing), [compaction](https://platform.claude.com/docs/en/build-with-claude/compaction), [manage-tool-context](https://platform.claude.com/docs/en/agents-and-tools/tool-use/manage-tool-context); engineering [effective-context-engineering-for-ai-agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) |
| 5.2 Escalation | API [customer-support-chat](https://platform.claude.com/docs/en/about-claude/use-case-guides/customer-support-chat); API prompting best practices |
| 5.3 Error propagation | engineering [multi-agent-research-system](https://www.anthropic.com/engineering/multi-agent-research-system); MCP [tools](https://modelcontextprotocol.io/specification/2026-07-28/server/tools) |
| 5.4 Codebase exploration | CC [context-window](https://code.claude.com/docs/en/context-window), CC [large-codebases](https://code.claude.com/docs/en/large-codebases), CC [sub-agents](https://code.claude.com/docs/en/sub-agents), CC [commands](https://code.claude.com/docs/en/commands) (`/compact`) |
| 5.5 Human review + calibration | API [develop-tests](https://platform.claude.com/docs/en/test-and-evaluate/develop-tests) |
| 5.6 Provenance | API [citations](https://platform.claude.com/docs/en/build-with-claude/citations), [search-results](https://platform.claude.com/docs/en/build-with-claude/search-results); engineering [multi-agent-research-system](https://www.anthropic.com/engineering/multi-agent-research-system) |

## Professional: docs by objective

| Objective | Official pages |
|---|---|
| P1.1–P1.6 Design | engineering [building-effective-agents](https://www.anthropic.com/engineering/building-effective-agents), [multi-agent-research-system](https://www.anthropic.com/engineering/multi-agent-research-system); API [overview](https://platform.claude.com/docs/en/about-claude/use-case-guides/overview); API [overview](https://platform.claude.com/docs/en/managed-agents/overview) |
| P2.1 Model selection | API [overview](https://platform.claude.com/docs/en/models/overview), [choosing-a-model](https://platform.claude.com/docs/en/about-claude/models/choosing-a-model), [optimizing-for-cost-and-intelligence](https://platform.claude.com/docs/en/about-claude/models/optimizing-for-cost-and-intelligence) |
| P2.2–P2.3 Prompts + guardrails | API [overview](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/overview), [claude-prompting-best-practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) |
| P2.4 Context + tokens | API [context-windows](https://platform.claude.com/docs/en/build-with-claude/context-windows), [token-counting](https://platform.claude.com/docs/en/build-with-claude/token-counting), [compaction](https://platform.claude.com/docs/en/build-with-claude/compaction); engineering [effective-context-engineering-for-ai-agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) |
| P2.5 Reuse | API [prompt-caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching), [overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview), [best-practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices), [skills-guide](https://platform.claude.com/docs/en/build-with-claude/skills-guide) |
| P3.1 Capability bloat | engineering [writing-tools-for-agents](https://www.anthropic.com/engineering/writing-tools-for-agents), [code-execution-with-mcp](https://www.anthropic.com/engineering/code-execution-with-mcp); SDK [permissions](https://code.claude.com/docs/en/agent-sdk/permissions) |
| P3.2 AuthN/AuthZ | MCP [authorization](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization); https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices ; SDK [secure-deployment](https://code.claude.com/docs/en/agent-sdk/secure-deployment) |
| P3.3 Accuracy vs latency | API [reduce-latency](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-latency), [choosing-a-model](https://platform.claude.com/docs/en/about-claude/models/choosing-a-model) |
| P3.4, P4.6 Observability | API [opentelemetry](https://platform.claude.com/docs/en/manage-claude/opentelemetry); SDK [observability](https://code.claude.com/docs/en/agent-sdk/observability); CC [monitoring-usage](https://code.claude.com/docs/en/monitoring-usage) |
| P3.5–P3.6 RAG | engineering [contextual-retrieval](https://www.anthropic.com/engineering/contextual-retrieval); API [embeddings](https://platform.claude.com/docs/en/build-with-claude/embeddings), [search-results](https://platform.claude.com/docs/en/build-with-claude/search-results), [citations](https://platform.claude.com/docs/en/build-with-claude/citations) |
| P3.7 Integration mechanism | API [how-tool-use-works](https://platform.claude.com/docs/en/agents-and-tools/tool-use/how-tool-use-works) (client tools vs server tools vs MCP), [define-tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools); MCP [transports](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports); https://modelcontextprotocol.io/docs/learn/architecture ; API [mcp-connector](https://platform.claude.com/docs/en/agents-and-tools/mcp-connector), [remote-mcp-servers](https://platform.claude.com/docs/en/agents-and-tools/remote-mcp-servers) |
| P3.8 Progressive discovery | API [tool-search-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool); engineering [code-execution-with-mcp](https://www.anthropic.com/engineering/code-execution-with-mcp), [equipping-agents-for-the-real-world-with-agent-skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) |
| P4.1–P4.3 Evals + A/B | API [develop-tests](https://platform.claude.com/docs/en/test-and-evaluate/develop-tests); engineering [demystifying-evals-for-ai-agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) |
| P4.4 Diagnosis | API [reduce-hallucinations](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations), [increase-consistency](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/increase-consistency), [troubleshooting-tool-use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/troubleshooting-tool-use) |
| P4.5 Cost + latency | API [prompt-caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching), [batch-processing](https://platform.claude.com/docs/en/build-with-claude/batch-processing), [reduce-latency](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-latency) |
| P5.1–P5.2 Guardrails + risks | API [mitigate-jailbreaks](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/mitigate-jailbreaks), [reduce-prompt-leak](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-prompt-leak), [reduce-hallucinations](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations); CC [security](https://code.claude.com/docs/en/security), CC [sandboxing](https://code.claude.com/docs/en/sandboxing) |
| P5.3 Human-in-the-loop | CC [permissions](https://code.claude.com/docs/en/permissions), CC [permission-modes](https://code.claude.com/docs/en/permission-modes); SDK [permissions](https://code.claude.com/docs/en/agent-sdk/permissions), SDK [user-input](https://code.claude.com/docs/en/agent-sdk/user-input) |
| P5.4 Compliance | API [mcp-connector](https://platform.claude.com/docs/en/agents-and-tools/mcp-connector) (not covered by ZDR, per its data-retention section); API [api-and-data-retention](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention); CC [zero-data-retention](https://code.claude.com/docs/en/zero-data-retention), CC [hipaa-setup](https://code.claude.com/docs/en/hipaa-setup), CC [legal-and-compliance](https://code.claude.com/docs/en/legal-and-compliance) |
| P5.5 Ethics | No dedicated doc page. Use first principles + https://www.anthropic.com/transparency if needed |
| P6.1–P6.5 Stakeholders + lifecycle | Little official doc coverage, so practice it through labs P3 and P6. API [develop-tests](https://platform.claude.com/docs/en/test-and-evaluate/develop-tests) (success criteria as the contract with stakeholders) |
| P7.1 Team config | CC [admin-setup](https://code.claude.com/docs/en/admin-setup), CC [managed-settings](https://code.claude.com/docs/en/managed-settings), CC [settings](https://code.claude.com/docs/en/settings), CC [permissions](https://code.claude.com/docs/en/permissions), CC [skills](https://code.claude.com/docs/en/skills), CC [overview](https://code.claude.com/docs/en/plugins/overview) |
| P7.2–P7.3 Workflows + ops | CC [best-practices](https://code.claude.com/docs/en/best-practices), CC [analytics](https://code.claude.com/docs/en/analytics), CC [troubleshooting](https://code.claude.com/docs/en/troubleshooting), CC [debug-your-config](https://code.claude.com/docs/en/debug-your-config) |

Agent-to-agent integration (named in P3.7) has no dedicated Anthropic doc page as of 2026-10-27. Write items about it from the trade-offs (another autonomous agent with its own reasoning, owner, latency, and failure modes) rather than from protocol specifics.

## Third-party (practice only)

- claudecertificationguide.com: free diagnostic (/diagnostic), free lessons (/learn, /ccar-p/learn), quick references (/quick-reference). Mocks are paid. It states it is independent and not affiliated with Anthropic. Its "Exam Guide or Current Docs" post documents the Task→Agent rename.
