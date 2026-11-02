# S3 · Multi-Agent Research System · exam block

Answer cold: no docs, no notes, no Claude. Allow about 2 minutes per item (20 minutes for the block). Write a letter and a confidence (H/M/L) for each item, then open [answers.md](answers.md). To have Claude run the block, score it, and walk you back through each miss, use `/cca-scenario S3` instead.

## Scenario

You are building a multi-agent research system using the Claude Agent SDK. A coordinator agent delegates to specialized subagents: one searches the web, one analyzes documents, one synthesizes findings, and one generates reports. The system researches topics and produces comprehensive, cited reports.

---

### Q1

The coordinator delegates to the document analysis subagent with the prompt "Analyze the key papers in light of the findings so far." The analyses that come back are generic. They don't reference any of the 14 sources the web search subagent found earlier in the same run, and they cite no URLs. Each subagent produces good output when tested on its own with a complete prompt. What change fixes this?

A. Give the document analysis subagent the web search tools so it can find the earlier results again itself.
B. Raise the document analysis subagent's context window so the coordinator's full history fits inside it.
C. Put the web search findings, with their URLs and document names, into the subagent's task prompt.
D. Tell the subagent in its system prompt to read the coordinator's earlier messages before it begins.

### Q2

For a comparison across four independent subtopics, the coordinator spawns one web search subagent per subtopic. Each subagent takes about 90 seconds, and the full research phase takes over 6 minutes. Logs show the coordinator emits one Task call per response and waits for its result before emitting the next. What change most reduces research time without lowering quality?

A. Combine all four subtopics into one web search subagent's prompt so a single subagent covers them.
B. Have the coordinator emit all four Task calls in one response instead of one at a time.
C. Move the web search subagents to a smaller, faster model to shorten the time each one takes.
D. Limit each web search subagent to fewer searches so that every subtopic finishes sooner.

### Q3

A draft report states "Remote work raised productivity by 13%" without a citation. Fact-checking finds two credible sources: a 2020 study reporting a 13% gain and a 2023 survey reporting a 4% decline. The document analysis agent currently passes prose summaries to the synthesis agent. Which TWO changes best fix the report's provenance and its handling of conflicting evidence? **(Select TWO.)**

A. Tell the synthesis agent to report only the figure from the more recent of any two conflicting sources.
B. Have the analysis agent return each claim with its source URL, document, excerpt, and date.
C. Leave statistics out of the report whenever sources disagree, keeping only the qualitative findings.
D. When credible sources conflict, report both figures with attribution instead of choosing one.
E. Add a final pass where the synthesis agent rereads its report and adds the citations it remembers.

### Q4

For "regulation of autonomous vehicles in the EU, US, and China", the coordinator assigns one web search subagent per region. The final report covers the EU and the US in depth but gives China a single sentence. Logs show the China subagent returned only two sources, and the coordinator then sent the synthesis to the report subagent. What change best prevents reports like this?

A. Raise the web search subagent's result limit so that every subtopic returns at least ten sources.
B. Instruct the report subagent to expand thin sections by elaborating on the sources it does have.
C. Run the whole pipeline three times and merge the reports, keeping the most detailed section per region.
D. Have the coordinator check the synthesis for gaps and re-delegate targeted queries before reporting.

### Q5

The coordinator has two tools: Task, for delegating to subagents, and `search_cache`. The `search_cache` description is detailed and accurate: it looks up sources already retrieved earlier in this run, which saves repeat web searches. Last week a prompt edit added the line "Always search thoroughly before drawing conclusions" to the coordinator's system prompt. Since then, the coordinator calls `search_cache` 20–30 times per query, often for topics nothing has retrieved yet, and delegates to the web search subagent far less often. What should you change?

A. Expand the `search_cache` description to state even more firmly that it only covers previously retrieved sources.
B. Remove `search_cache` from the coordinator so that all lookups have to go through the web search subagent.
C. Reword the new instruction to route thorough research through the web search subagent, not "search".
D. Add a hook that blocks `search_cache` after three calls per query and returns an error to the coordinator.

### Q6

On broad topics, six document analysis subagents each return about 9,000 tokens to the coordinator. Most of each result is narrative about how the subagent read each paper and why. The coordinator forwards these results to the synthesis agent. Synthesis misses key figures that appear in the middle results. What change best addresses this?

A. Switch the synthesis agent to a model with a larger context window so all six results fit comfortably.
B. Have the coordinator condense each result into a short paragraph before forwarding it to synthesis.
C. Split synthesis into two runs of three results each, then concatenate the two partial syntheses.
D. Have analysis subagents return structured findings (claim, evidence, source, date) instead of narratives.

### Q7

A research session has spent 40 minutes gathering and analyzing sources on grid-scale battery storage. Stakeholders want two report drafts from that research, one framed for policymakers and one for investors, so they can compare synthesis approaches. They don't want the research repeated, and they don't want either draft to shape the other. What should you do?

A. Continue the same session, asking for the investor draft once the policymaker draft is complete.
B. Fork the session after the research phase once per draft, so each builds on the same research independently.
C. Start two new sessions and rerun the research in each so that the two drafts are fully independent.
D. Request both drafts in a single prompt so the agent can keep the two versions consistent with each other.

---

## Official sample questions (CCAR-F exam guide v1.0, Section 9)

These three are reproduced from the official guide. They show the real exam's style. Answer them cold too, even if you've read them before. What matters is whether you can explain *why* the key wins.

### Q8

After running the system on the topic "impact of AI on creative industries," you observe that each subagent completes successfully: the web search agent finds relevant articles, the document analysis agent summarizes papers correctly, and the synthesis agent produces coherent output. However, the final reports cover only visual arts, completely missing music, writing, and film production. When you examine the coordinator's logs, you see it decomposed the topic into three subtasks: "AI in digital art creation," "AI in graphic design," and "AI in photography." What is the most likely root cause?

A. The synthesis agent lacks instructions for identifying coverage gaps in the findings it receives from other agents.
B. The coordinator agent's task decomposition is too narrow, resulting in subagent assignments that don't cover all relevant domains of the topic.
C. The web search agent's queries are not comprehensive enough and need to be expanded to cover more creative industry sectors.
D. The document analysis agent is filtering out sources related to non-visual creative industries due to overly restrictive relevance criteria.

### Q9

The web search subagent times out while researching a complex topic. You need to design how this failure information flows back to the coordinator agent. Which error propagation approach best enables intelligent recovery?

A. Return structured error context to the coordinator including the failure type, the attempted query, any partial results, and potential alternative approaches.
B. Implement automatic retry logic with exponential backoff within the subagent, returning a generic "search unavailable" status only after all retries are exhausted.
C. Catch the timeout within the subagent and return an empty result set marked as successful.
D. Propagate the timeout exception directly to a top-level handler that terminates the entire research workflow.

### Q10

During testing, you observe that the synthesis agent frequently needs to verify specific claims while combining findings. Currently, when verification is needed, the synthesis agent returns control to the coordinator, which invokes the web search agent, then re-invokes synthesis with results. This adds 2-3 round trips per task and increases latency by 40%. Your evaluation shows that 85% of these verifications are simple fact-checks (dates, names, statistics) while 15% require deeper investigation. What's the most effective approach to reduce overhead while maintaining system reliability?

A. Give the synthesis agent a scoped `verify_fact` tool for simple lookups, while complex verifications continue delegating to the web search agent through the coordinator.
B. Have the synthesis agent accumulate all verification needs and return them as a batch to the coordinator at the end of its pass, which then sends them all to the web search agent at once.
C. Give the synthesis agent access to all web search tools so it can handle any verification need directly without round-trips through the coordinator.
D. Have the web search agent proactively cache extra context around each source during initial research, anticipating what the synthesis agent might need to verify.
