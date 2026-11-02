# CCAR-P blueprint (Claude Certified Architect – Professional)

Condensed from the **official exam guide v1.0, effective July 2026**. The guide is the authority on scope. Objective IDs like `P3.2` are added here for progress tracking. The official guide lists the objectives as unnumbered bullets.
PDF: https://everpath-course-content.s3-accelerate.amazonaws.com/instructor%2F6nizmqk8tpzpfjvt6qmmav7rh%2Fpublic%2F1783542810%2FClaude+Certified+Architect+%E2%80%93+Professional+Exam+Guide.pdf

## Exam facts

| Item | Value |
|---|---|
| Code | CCAR-P |
| Items | 63, multiple-choice and multiple-response. **Standalone items, no scenario bank** |
| Time | 120 minutes |
| Pass | Scaled 720 on 100–1,000 |
| Fee | $175 USD |
| Prerequisites | None. Foundations is not required |
| Recommended experience | 3+ years systems architecture or platform engineering; 6+ months hands-on with Claude or similar LLM systems in production; end-to-end delivery from discovery to operations |
| Not for | Entry-level developers, casual users, prompt-only roles without system design responsibility |

The minimally qualified candidate designs, implements, and **governs** Claude solutions in production, and understands trade-offs across cost, latency, performance, safety, and maintainability.

## Domains

| # | Domain | Weight | ≈ items of 63 |
|---|---|---|---|
| 1 | Solution Design & Architecture | 17% | 11 |
| 2 | Claude Models, Prompting & Context Engineering | 13% | 8 |
| 3 | Integration | 19% | 12 |
| 4 | Evaluation, Testing & Optimization | 16% | 10 |
| 5 | Governance, Safety & Risk Management | 14% | 9 |
| 6 | Stakeholder Communication & Lifecycle Management | 14% | 9 |
| 7 | Developer Productivity & Operational Enablement | 7% | 4 |

Domains 5–7 (35%) have no Foundations equivalent. Do not skim them.

## Objectives

### P1 Solution Design & Architecture (17%)
- **P1.1** Translate business problems into Claude-based AI solutions
- **P1.2** Design end-to-end architectures (input → processing → output → feedback loops)
- **P1.3** Select architectural patterns: workflow, agentic, augmented LLM
- **P1.4** Design multi-agent systems and orchestration strategies
- **P1.5** Apply decomposition techniques for complex problems
- **P1.6** Align to business value pillars: efficiency, transformation, productivity, cost, performance SLAs

### P2 Claude Models, Prompting & Context Engineering (13%)
- **P2.1** Select Claude models based on trade-offs
- **P2.2** Design system prompts, templates, guardrails
- **P2.3** Apply zero-shot, few-shot, chain-of-thought
- **P2.4** Optimize context windows and token usage
- **P2.5** Prompt reuse: caching, modular prompts, Skills

### P3 Integration (19%)
- **P3.1** Evaluate tool/agent configuration for capability bloat
- **P3.2** Analyze authentication/authorization requirements to find security gaps
- **P3.3** Evaluate accuracy–latency trade-offs and justify configuration
- **P3.4** Analyze observability challenges and pick monitoring strategies at scale
- **P3.5** Design a RAG pipeline with appropriate chunking and indexing
- **P3.6** Match retrieval strategy to data shape and query pattern
- **P3.7** Select integration mechanism: MCP vs API/CLI vs agent-to-agent
- **P3.8** Progressive discovery vs monolithic context strategy

### P4 Evaluation, Testing & Optimization (16%)
- **P4.1** Define metrics: accuracy, latency, cost, safety, security
- **P4.2** Design eval datasets and test frameworks with mixed methods
- **P4.3** A/B testing and iterative improvement
- **P4.4** Diagnose issues: prompt failure, hallucination, model mismatch
- **P4.5** Optimize token usage, latency, cost–performance
- **P4.6** Monitor with logging and observability tools

### P5 Governance, Safety & Risk Management (14%)
- **P5.1** Implement guardrails and safety controls
- **P5.2** Identify risks, limitations, failure modes of LLM systems
- **P5.3** Human-in-the-loop validation strategies
- **P5.4** Regulatory compliance (e.g., GDPR, HIPAA, FedRAMP)
- **P5.5** Ethical AI: bias, fairness, transparency

### P6 Stakeholder Communication & Lifecycle Management (14%)
- **P6.1** Structured discovery and requirement gathering
- **P6.2** Communicate architectural decisions and trade-offs
- **P6.3** Manage feedback loops and expectation alignment, including SLAs
- **P6.4** Document architectures and give implementation guidance
- **P6.5** Support lifecycle phases: discovery, design, handoff, monitoring, iteration

### P7 Developer Productivity & Operational Enablement (7%)
- **P7.1** Configure Claude tools and environments for teams (e.g., Claude Code)
- **P7.2** Improve developer workflows with AI-assisted tooling
- **P7.3** Support debugging and operational issue resolution

## What the official samples teach

The guide has 3 sample items. Their rationales show how answers are keyed:
- **Least privilege means removal** (P3.1/P3.2). Remove tools the role never needs. Logging and confirmations are detective or compensating controls, and a bigger model doesn't change authorization scope.
- **Static-first ordering + prompt caching** (P2.5/P4.5). This cuts both latency and cost without dropping needed context. Truncation, blind downsizing, and moving content into few-shot are wrong.
- **Symptoms point to the changed component** (P4.4/P3.5). Confident-but-wrong answers right after a document refresh, with model and latency unchanged, point to retrieval/indexing first.

## Official preparation guidance
- Self-assess against every objective above.
- Read official docs for the Claude API, models, prompt engineering, MCP, and Skills.
- Build and operate at least one end-to-end Claude solution **including RAG, evaluation, and observability**.
- Practice architectural decisions: model selection, integration protocols, security trade-offs.

## Bridges from Foundations

| Professional objective | Foundations groundwork | What's new |
|---|---|---|
| P1.3, P1.4, P1.5 | 1.2, 1.6 | Choosing workflow vs agent vs augmented LLM up front, tied to business value |
| P2.4, P2.5 | 5.1 | Prompt caching and model choice are now in scope, not just "exists" |
| P3.1 | 2.3 | Capability bloat as a security and reliability risk |
| P3.2 | none (auth was out of scope) | Authn/authz gap analysis, delegated access |
| P3.5, P3.6 | none (embeddings/vector DB out of scope) | Chunking, indexing, retrieval strategy |
| P3.7, P3.8 | 2.4 | MCP vs API/CLI vs agent-to-agent; progressive discovery |
| P4.x | 4.4, 5.5 | Full evaluation practice: datasets, A/B, diagnosis, cost tuning |
| P5.3 | 5.2, 5.5 | HITL as governance, plus compliance regimes |
| P6.x | none | Discovery, decision records, SLAs, lifecycle |
| P7.x | 3.x | Team rollout and operations, not just your own setup |
