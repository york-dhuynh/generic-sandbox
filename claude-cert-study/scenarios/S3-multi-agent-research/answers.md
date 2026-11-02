# S3 · Multi-Agent Research System · answers and reverse engineering

Score yourself with the key, then work through every miss and every guess. A guess is a low-confidence answer, even when it was right. For each one, cover the explanation, read the clue, and try to say why the key wins before reading on.

## Answer key

| Q | Key | Objective | Rule in one line |
|---|---|---|---|
| 1 | C | 1.3 Context passing | Subagents see only the prompt you give them; pass complete findings with their sources |
| 2 | B | 1.3 Parallel spawning | Independent subtasks: emit several Task calls in one coordinator response |
| 3 | B, D | 5.6 Provenance | Keep claim→source records through synthesis; show conflicting credible figures with attribution and dates |
| 4 | D | 1.2 Iterative refinement | The coordinator checks synthesis for gaps and re-delegates targeted queries before reporting |
| 5 | C | 2.1 Tool interfaces | System-prompt keywords can pull the model toward a tool; fix the wording that changed |
| 6 | D | 5.1 Context between agents | Upstream agents return structured facts, not reasoning narratives |
| 7 | B | 1.7 Sessions and forking | Fork from a shared baseline to explore divergent approaches independently |
| 8 | B | 1.2 Decomposition *(official)* | Coverage gaps that trace to the coordinator's split are the coordinator's fault |
| 9 | A | 5.3 Error propagation *(official)* | Return failure type, attempted query, partial results, and alternatives |
| 10 | A | 2.3 Tool distribution *(official)* | Scoped tool for the common case; route the rare case through the coordinator |

---

## Q1 · Key C · Objective 1.3 · Subagent context passing

**Question type:** fix a defect. "Each subagent produces good output when tested on its own" tells you the subagent itself isn't broken.

**The clue:** the prompt says "in light of the findings so far", but the findings never appear in it. The output ignores the 14 sources and cites no URLs. The subagent is being asked to use information it was never given.

**Why C:** A subagent starts with fresh context. It doesn't inherit the coordinator's conversation or tool results, and the only thing that passes from parent to subagent is the task prompt. So the coordinator must put the complete prior findings in that prompt, with their metadata (URLs, document names, pages), so the analysis can build on them and keep attribution.

**Why not the others:**
- **A** duplicates work and over-provisions the subagent. It would run new searches instead of using the 14 sources already found, and analysis doesn't need search tools.
- **B** assumes the subagent could see the coordinator's history if it had room. It can't. Isolation is structural, so a bigger window changes nothing.
- **D** has the same misconception. No instruction can make the subagent read messages that were never sent to it.

**Work it backwards:** When a subagent's output ignores something "earlier in the run", ask whether that information was in its prompt. If the delegation prompt only *refers* to findings ("so far", "above", "as discussed"), that's the bug.

**Other ways the exam could ask this:**
- *Same rule, new setting:* the report subagent produces a report without citations although synthesis had them. Pass the synthesis output with its claim-to-source mappings in the report subagent's prompt.
- *Flip a condition:* if the prompt *did* include the findings but the output still lost the URLs, the fix is a structured format that separates content from metadata, so attribution survives. That's still 1.3, with a different defect.
- *Neighboring objective (1.3, coordinator prompts):* subagents duplicate each other's work or wander off scope. Give each one an objective, an output format, and clear task boundaries, stated as goals and quality criteria rather than step-by-step procedures.

**Current docs:** non-fork subagents start fresh, and only the Agent tool's prompt string passes from the parent. Claude Code now also offers *fork* subagents that copy the parent conversation. The exam's model is the fresh-context subagent, so answer that subagents don't inherit history.

**Source:** [Agent SDK subagents · What subagents inherit](https://code.claude.com/docs/en/agent-sdk/subagents) · [How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)

---

## Q2 · Key B · Objective 1.3 · Parallel spawning

**Question type:** most effective improvement, with a constraint ("without lowering quality").

**The clue:** "four independent subtopics" plus "emits one Task call per response and waits". The work is parallel by nature but runs one task at a time.

**Why B:** To run subagents in parallel, the coordinator emits several Task calls in a **single** response. Independent subtasks then finish in about the time of the slowest one instead of the sum of all four. Anthropic's research system spins up 3–5 subagents in parallel and reports large time savings on complex queries.

**Why not the others:**
- **A** removes the parallelism you want and overloads one subagent with four scopes, which risks shallow coverage of each.
- **C** speeds up each step but keeps the serial chain, and it trades away quality the stem says to protect.
- **D** buys speed by doing less research, which directly lowers quality.

**Work it backwards:** If a stem says the subtasks are independent and the log shows them happening one after another, the answer is parallel dispatch in one response. Options that make each step faster or smaller miss the structural cause.

**Other ways the exam could ask this:**
- *Same rule, new setting:* a code review coordinator runs style, security, and test-coverage subagents one after another. Dispatch all three in one response.
- *Flip a condition:* if subtopic 2 needed subtopic 1's results (dependent work), sequential delegation is correct, and parallelizing would make subtopic 2 run without its inputs.
- *Neighboring objective (1.2):* the coordinator spawns all four subagents even for a simple fact question. It should choose which subagents to run, and how many, based on the query instead of always running the full pipeline.

**Current docs:** the exam calls it the **Task** tool and says the coordinator's `allowedTools` must include `"Task"`. Current docs name it **`Agent`** in `tool_use` blocks, though it still appears as `"Task"` in the init tools list (drift row 1). Answer "Task". Claude Code subagents also run in the background by default now, but the exam's lever is still several calls in one response.

**Source:** [Agent SDK subagents](https://code.claude.com/docs/en/agent-sdk/subagents) · [How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)

---

## Q3 · Keys B, D · Objective 5.6 · Provenance and conflicting evidence

**Question type:** Select TWO. One option has to fix provenance and the other has to fix how conflicts are handled. Each must be right on its own.

**The clue:** two problems in one stem. "Without a citation" plus "passes prose summaries" means the claim-to-source link was lost in summarization. "2020 … 13% gain" vs "2023 … 4% decline" means two credible sources that disagree, possibly because of when they were measured.

**Why B and D:**
- **B:** summaries drop the mapping from each claim to its source. Structured claim records (URL, document, excerpt, date) carry it through synthesis, so the report can cite every figure.
- **D:** with conflicting credible figures, keep both with attribution and don't pick one. Dates matter here: 2020 vs 2023 may reflect a real change over time, not a contradiction, and the reader can only see that if the dates are shown.

**Why not the others:**
- **A** picks a figure by rule and hides the disagreement. The guide says not to choose arbitrarily, and "most recent" still discards credible evidence.
- **C** hides the problem by deleting useful evidence instead of presenting it honestly.
- **E** is self-review from memory after the mapping was already lost. It invites confident but wrong citations, and the guide calls self-review weak.

**Work it backwards:** For provenance problems, ask where the claim-to-source link broke. It's usually at a prose summary, so the fix is structure. For conflicts, ask whether the option shows the conflict or hides it. On this exam, showing it with attribution and dates is the answer.

**Other ways the exam could ask this:**
- *Same rule, new setting:* a financial research report merges revenue figures from two filings with different fiscal-year ends. Keep both, with dates and sources, and render financials as a table.
- *Flip a condition:* if one "source" were a blog quoting the 2020 study, the sources aren't independently credible. Trace the claim back to the primary source instead of presenting two figures.
- *Neighboring objective (5.3):* synthesis output should also carry coverage annotations, marking which findings are well supported and which areas have gaps.

**Source:** CCAR-F guide task 5.6 · [Citations](https://platform.claude.com/docs/en/build-with-claude/citations) · [How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) (the CitationAgent attributes claims to sources)

---

## Q4 · Key D · Objective 1.2 · Iterative refinement

**Question type:** prevent a recurrence. Ask which component should have caught the gap.

**The clue:** the decomposition was right (one subagent per region), but the China subagent "returned only two sources", and the coordinator "then sent the synthesis to the report subagent" with nothing in between. The pipeline has no step where anyone checks coverage.

**Why D:** In hub-and-spoke orchestration, the coordinator owns quality. It evaluates the synthesis for gaps, re-delegates targeted queries (here, China-specific regulation sources), and synthesizes again before reporting. Anthropic's lead researcher does this: it synthesizes results and decides whether more research is needed.

**Why not the others:**
- **A** is an arbitrary quota. Ten weak sources don't guarantee coverage, and the system still never checks for gaps.
- **B** papers over the gap by padding thin sections, which risks unsupported claims in a cited report.
- **C** is brute force at three times the cost. If the China sources are hard to find, all three runs may come back thin.

**Work it backwards:** This is the flip of official sample Q8. There, the decomposition was wrong, so the fix was the decomposition. Here the decomposition was right and one branch came back thin, so the fix is the review-and-re-delegate loop. Read the logs to see which step failed.

**Other ways the exam could ask this:**
- *Same rule, new setting:* a codebase-exploration coordinator gets a summary that skips one service. It notices the gap and sends a targeted follow-up before writing the overview.
- *Flip a condition:* if the coordinator's logs showed it never assigned China at all, the root cause is narrow decomposition (sample Q8), not a missing review loop.
- *Neighboring objective (1.2, effort scaling):* simple fact questions run all four subagents. The coordinator should pick subagents and effort per query, for example one agent for a simple fact and several for a broad comparison.

**Source:** [How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) · CCAR-F guide task 1.2

---

## Q5 · Key C · Objective 2.1 · Tool interfaces

**Question type:** what to change. A behavior regression with a dated cause.

**The clue:** "Last week a prompt edit added … 'Always search thoroughly'", plus "Since then". The tool description was already "detailed and accurate". Something changed, and it wasn't the tool.

**Why C:** The guide notes that keywords in the system prompt can create unintended tool associations that override good descriptions. "Search" pulls the coordinator toward the tool named `search_cache`, even for topics nothing has retrieved. Rewording the instruction to say what it actually means (do thorough research through the web search subagent) removes the association without losing the tool.

**Why not the others:**
- **A** reinforces a description that was never the problem. The stem says it's already accurate, and the prompt keyword still outweighs it.
- **B** throws away a useful capability (avoiding repeat searches) to fix a wording problem the team introduced.
- **D** treats the symptom with an arbitrary cap. Errors after three calls don't restore delegation, and they waste turns.

**Work it backwards:** When a regression starts right after a change, look at the changed component first. Then ask whether the prompt's wording now competes with a tool's name or description.

**Other ways the exam could ask this:**
- *Same rule, new setting:* after a prompt says "analyze every source carefully", the synthesis agent starts calling an `analyze_document` tool on sources it already has.
- *Flip a condition:* if nothing in the prompt had changed and the description were one vague line ("Searches stuff"), the fix is rewriting the description (official sample Q9 in S1).
- *Neighboring objective (2.1, overlapping tools):* two tools named `analyze_content` and `analyze_document` with near-identical descriptions get mixed up. Rename and rewrite them so each has a distinct purpose and contract (for example, `extract_web_results`).

**Source:** CCAR-F guide task 2.1 · [Define tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools) · [Writing tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents)

---

## Q6 · Key D · Objective 5.1 · Context between agents

**Question type:** best fix. Locate where the context is bloated.

**The clue:** "about 9,000 tokens" each, "mostly narrative about how the subagent read each paper and why", and synthesis that "misses key figures that appear in the middle results". The volume is upstream reasoning the downstream agent doesn't need, and attention suffers.

**Why D:** When downstream context is tight, upstream agents should return structured facts rather than verbose reasoning. Records of claim, evidence, source, and date are compact, keep the numbers and sources, and are easy for synthesis to combine. Anthropic's system goes further, storing outputs externally and passing lightweight references to avoid a "game of telephone".

**Why not the others:**
- **A** is the bigger-context-window reflex. Everything fits, but the figures in the middle still get missed (lost in the middle), and the narrative noise stays.
- **B** adds a lossy summarization hop at the coordinator. Short paragraphs drop exactly the figures and sources synthesis needs.
- **C** fragments synthesis. Cross-cutting conclusions across all six results are lost, and concatenation isn't synthesis.

**Work it backwards:** When a downstream agent drowns in input, fix the *shape* of what upstream sends before you change the receiver. If the upstream output is narrative, make it structured.

**Other ways the exam could ask this:**
- *Same rule, new setting:* in S1, a 40-field `lookup_order` result floods the support agent's context. Trim the tool output to the fields the agent needs.
- *Flip a condition:* if each result were already concise structured facts but there were 60 of them, you'd look at splitting the synthesis work or at a dedicated aggregation step.
- *Neighboring objective (5.1, placement):* key findings get overlooked in a long synthesis prompt. Put them first and use explicit section headers.

**Source:** [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) · [How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)

---

## Q7 · Key B · Objective 1.7 · Sessions and forking

**Question type:** which approach. Three stated constraints must all hold.

**The clue:** "40 minutes" of research to reuse, "two … drafts … compare", "don't want the research repeated", and "don't want either draft to shape the other". That's a shared baseline with two independent branches.

**Why B:** Forking creates a new session that starts with a copy of the original's history and then diverges. The original stays unchanged. Forking once per draft from the end of the research phase gives each draft the full research and none of the other draft's reasoning. In the SDK, this is resuming with `fork_session=True` (Python) or `forkSession: true` (TypeScript).

**Why not the others:**
- **A** breaks independence. The investor draft is written in a context that contains the policymaker draft.
- **C** breaks "don't repeat the research" and costs another 40 minutes per draft.
- **D** breaks independence on purpose. "Keep them consistent" is the opposite of comparing approaches.

**Work it backwards:** Match each constraint to a mechanism. "Reuse what's done" points to resume or fork. "Independent alternatives" rules out plain resume. Both together point to fork.

**Other ways the exam could ask this:**
- *Same rule, new setting:* in a developer tool (S4), an agent has mapped a legacy codebase and you want to compare two refactoring strategies. Fork from the mapped baseline.
- *Flip a condition:* if the sources had been updated since the session (tool results now stale), don't fork or resume. Start fresh with an injected structured summary of what's still valid.
- *Neighboring objective (1.7, resume):* the same research continues tomorrow after a crash. Resume the named session, and tell the agent which inputs changed so it re-checks only those.

**Watch the scope:** forking branches the *conversation*, not files on disk. That doesn't affect this stem, but it's a plausible distractor elsewhere.

**Source:** [Agent SDK sessions · Fork to explore alternatives](https://code.claude.com/docs/en/agent-sdk/sessions)

---

## Q8 · Key B · Objective 1.2 · *Official sample*

**Official rationale (condensed):** the coordinator's logs show the root cause directly. It decomposed "creative industries" into visual-arts subtasks only. The subagents did their assigned jobs correctly, and A, C, and D wrongly blame downstream agents.

**The clue:** "each subagent completes successfully", plus the three listed subtasks, which are all visual arts. The stem hands you the coordinator's log, so read it.

**Work it backwards:** Follow the defect upstream to the first component whose *output* was wrong. Here every subagent output was right for its input, so the fault is the input the coordinator wrote.

**Other ways the exam could ask this:**
- *Same rule, new setting:* a test-generation pipeline covers only the API layer because the coordinator split "add tests to the app" into three API modules.
- *Flip a condition:* if the decomposition covered all sectors but the search agent returned nothing for "music", look at that subagent's queries or at the coordinator's review loop (Q4).
- *Neighboring objective (1.2, partitioning):* two subagents return near-identical findings. Partition their scopes so they don't overlap.

**Source:** CCAR-F guide §9 Q7 · [How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)

---

## Q9 · Key A · Objective 5.3 · *Official sample*

**Official rationale (condensed):** structured error context lets the coordinator choose a recovery: retry with a modified query, try an alternative, or proceed with partial results. B hides context behind a generic status. C suppresses the error as success. D needlessly kills the whole workflow.

**The clue:** "best enables intelligent recovery". The coordinator is the one recovering, so it needs information it can act on.

**Work it backwards:** Ask who makes the recovery decision and what they need to know to make it. Then pick the option that sends exactly that information, and reject any option that hides or exaggerates the failure.

**Other ways the exam could ask this:**
- *Same rule, new setting:* in S1, `process_refund` returns "Operation failed" for both policy rejections and timeouts. Put the category and retryability in the error content.
- *Flip a condition:* for a brief transient blip, the subagent should first retry locally. It reports up only what it couldn't resolve, with partial results and what it attempted.
- *Neighboring objective (5.6, coverage):* the final report should flag where research is thin because a source failed, not present partial coverage as complete.

**Source:** CCAR-F guide §9 Q8 · [MCP tools · error handling](https://modelcontextprotocol.io/specification/2026-07-28/server/tools)

---

## Q10 · Key A · Objective 2.3 · *Official sample*

**Official rationale (condensed):** a scoped `verify_fact` tool covers the 85% common case with least privilege and keeps the coordinator pattern for the complex 15%. B creates blocking dependencies. C over-provisions the synthesis agent and breaks separation of concerns. D is speculative caching.

**The clue:** "85% … simple fact-checks" vs "15% require deeper investigation". The numbers tell you to split the solution between the common case and the rare one.

**Work it backwards:** When a stem splits the workload by percentage, look for the option that handles each part differently: a narrow capability for the common case and the existing path for the rare one. Options that give the agent everything ignore the split.

**Other ways the exam could ask this:**
- *Same rule, new setting:* a report agent often needs a source's publication date. Give it a scoped `get_source_metadata` tool rather than full document-analysis tools.
- *Flip a condition:* if 85% of verifications needed deep investigation, the round trip through the coordinator is the right path, and you'd look at parallelizing those verifications instead.
- *Neighboring objective (2.3, too many tools):* a subagent given 18 tools misuses the ones outside its role. Scope its tools to that role.

**Source:** CCAR-F guide §9 Q9 · [Agent SDK subagents · Tool restrictions](https://code.claude.com/docs/en/agent-sdk/subagents)

---

## Scenario playbook

### What the frame tells you
| Phrase in the frame | What it puts in play |
|---|---|
| "using the Claude Agent SDK" | Task tool (exam wording), `AgentDefinition`, `allowedTools`, sessions and forking |
| "A coordinator agent delegates" | Hub-and-spoke: the coordinator owns decomposition, routing, error handling, and quality checks |
| "specialized subagents" with four named roles | Isolated context, tools scoped per role, delegation prompts that carry everything needed |
| "researches topics" | Decomposition breadth, effort scaled to the query, parallel dispatch |
| "comprehensive" | Coverage gaps, from narrow decomposition or thin branches the coordinator didn't catch |
| "cited reports" | Claim-to-source mappings that survive synthesis, conflicting evidence shown with dates |

### The design to hold in your head
```
topic ──► coordinator: decompose (cover every facet, non-overlapping scopes)
            │
            ├─► several Task calls in ONE response (parallel)
            │     each prompt = goal + quality criteria + complete prior findings (URLs, docs, pages)
            ▼
   web search      document analysis      (fresh context, scoped tools)
            │             │   return structured findings: claim · evidence · source · date
            │             │   on failure: error type · attempted query · partial results · alternatives
            ▼             ▼
   coordinator ──► synthesis (scoped verify_fact for simple checks; deep checks back via coordinator)
            │
            ├─► review synthesis for gaps ─► re-delegate targeted queries ─► re-synthesize
            ▼
   report (every claim cited; conflicting figures shown with attribution + dates)
```

### Question families
| Family | What the stem looks like | Deciding rule | Objectives |
|---|---|---|---|
| Narrow coverage | "report covers only X", decomposition visible in logs | Fix the coordinator's decomposition | 1.2 |
| Thin branch | correct split, one subtopic came back thin | Coordinator reviews for gaps, re-delegates | 1.2 |
| Subagent ignores prior work | "in light of findings so far", generic output | Pass complete findings with metadata in the prompt | 1.3 |
| Slow research | independent subtasks run one at a time | Several Task calls in one response | 1.3 |
| Duplicate or off-scope work | two subagents return the same thing | Objective, output format, boundaries; goals not procedures | 1.2, 1.3 |
| Subagent failure | timeout, empty results, whole run aborted | Structured error context to the coordinator | 5.3, 2.2 |
| Synthesis needs lookups | round trips, % split of simple vs deep | Scoped tool for the common case | 2.3 |
| Tool misuse | after a prompt edit, or confusable names | Fix the wording that changed; rename or rewrite tools | 2.1 |
| Context bloat between agents | huge narrative results, missed figures | Structured facts upstream, key findings first | 5.1 |
| Lost or conflicting citations | uncited figure, two sources disagree | Claim-source records; show both with dates | 5.6 |
| Alternatives from shared research | "compare two approaches without redoing work" | Fork the session | 1.7 |
| Over-running simple queries | full pipeline for a one-line fact | Coordinator picks subagents and effort per query | 1.2 |

### The tension S3 is built around
**Which component owns the problem?**
- The coordinator owns *what* gets done: decomposition, the content of each delegation prompt, recovery decisions, and whether coverage is good enough.
- Subagents own *doing* their scoped task well and reporting back in a usable shape.

Most S3 stems describe a symptom at the end of the pipeline and give you logs that point upstream. Official sample Q8 and Q4 here are a pair: same symptom (thin coverage), different failing step.

A second tension runs through the scenario: **isolation is a feature with a cost.** Clean subagent context is why the design works, and it's also why the coordinator must pass everything explicitly.

### Traps that recur in S3
- **Blaming the downstream agent that did its job correctly.** Read the logs the stem gives you.
- **Assuming a subagent can see the coordinator's conversation.** It sees only its prompt.
- **Giving a subagent every tool to avoid a round trip.** Prefer a scoped tool for the common case.
- **A bigger context window or model** for a context-shape problem.
- **Summarizing in a way that drops numbers or sources:** a prose hop between agents.
- **Picking one of two conflicting credible figures** instead of showing both with dates.
- **Empty-as-success, or killing the whole run** on one subagent failure.
- **"Task" vs "Agent":** answer "Task" on the exam (drift row 1).
