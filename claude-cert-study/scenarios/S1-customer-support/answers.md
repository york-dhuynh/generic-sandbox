# S1 · Customer Support Resolution Agent · answers and reverse engineering

Score yourself with the key, then work through every miss and every guess. A guess is a low-confidence answer, even when it was right. For each one, cover the explanation, read the clue, and try to say why the key wins before reading on.

## Answer key

| Q | Key | Objective | Rule in one line |
|---|---|---|---|
| 1 | D | 1.1 Agentic loop | Loop on `stop_reason`, never on the presence of text |
| 2 | C | 1.5 Hooks | Normalize inconsistent tool data in code at the tool boundary |
| 3 | D | 2.2 Structured errors | Errors carry category + retryability + explanation so the agent can choose the right recovery |
| 4 | A, B | 5.2 Escalation | Escalate on an explicit request or a policy gap; not on sentiment, self-confidence, or an ambiguous match |
| 5 | B | 5.1 Long interactions | Keep critical facts in a persistent block outside the summarized history |
| 6 | A | 2.3 Tool distribution | Tools outside the role get misused; remove them before tuning descriptions |
| 7 | C | 1.4 Handoff | Escalation hands off a structured summary, not a transcript or a vague reason |
| 8 | A | 1.4 Enforcement *(official)* | Rules with financial consequences need programmatic enforcement |
| 9 | B | 2.1 Tool descriptions *(official)* | Minimal descriptions cause misrouting; fix descriptions first |
| 10 | A | 5.2 Escalation *(official)* | Unclear boundaries → explicit criteria + few-shot before any infrastructure |

---

## Q1 · Key D · Objective 1.1 · Agentic loop

**Question type:** fix a defect. The stem names the symptom and the mechanism behind it.

**The clue:** "the loop treats the turn as complete" when "the response contains any text block", together with "a `tool_use` block … that was never executed". The response asked for a tool, and the loop ignored the request.

**Why D:** `stop_reason` is the API's explicit signal for what the model wants next. `"tool_use"` means "run these tools and send me the results". `"end_turn"` means the model has finished. A model can narrate ("Let me pull up your order") in the same response as a tool call, so text alone never signals completion.

**Why not the others:**
- **A** treats a control-flow bug as a prompt problem. Narration next to a tool call is normal and allowed. Even if the prompt mostly suppressed it, the loop would still be checking the wrong signal.
- **B** combines two anti-patterns the guide names: parsing natural-language "I'm done" signals, and an iteration cap as the main stop condition.
- **C** confuses this with truncation. A truncated response has `stop_reason: "max_tokens"`. Here the model stopped deliberately to request a tool.

**Work it backwards:** "An agent stops early or loops forever" points to the loop's stop condition first. Then ask which signal the loop reads. If it isn't `stop_reason`, that's the answer.

**Other ways the exam could ask this:**
- *Same rule, new setting:* a research subagent returns half-finished findings because the coordinator reads the first assistant text as its result. The answer is still `stop_reason`-driven looping.
- *Flip a condition:* if logs showed `stop_reason: "max_tokens"` with a cut-off sentence, the fix would be about output length (raise `max_tokens` or ask for shorter output), not about loop control.
- *Neighboring objective (1.4):* when the issue is the tool **order** ("skips `get_customer`") rather than loop termination, the answer is a programmatic prerequisite.

**Source:** [Handling stop reasons](https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons) · [How tool use works](https://platform.claude.com/docs/en/agents-and-tools/tool-use/how-tool-use-works)

---

## Q2 · Key C · Objective 1.5 · Agent SDK hooks

**Question type:** most reliable fix, with a constraint ("other teams own both backends").

**The clue:** "misjudges … almost always when it has to reason about the epoch values", plus the backends "will not change". The data reaching the model is inconsistent, and you can't fix it at the source.

**Why C:** A `PostToolUse` hook runs your code on every tool result before the model sees it. Converting dates there makes the inconsistency disappear on every call, deterministically. The model only ever reasons about one format. The guide uses exactly this example: normalizing Unix vs ISO 8601 timestamps.

**Why not the others:**
- **A** is probabilistic. It still asks the model to do arithmetic on epoch values, which is the step that fails.
- **B** is still probabilistic. The model has to *decide* to call the converter, and the trigger ("looks numeric") is the same judgment that's failing. It also adds a tool call to every legacy lookup.
- **D** over-engineers the problem. A specialized subagent still reasons about raw epoch values, and you've added orchestration to fix a formatting problem.

**Work it backwards:** When the model mishandles *data* (not instructions) and the data's shape is predictable, transform it in code before the model sees it. "Reliable" in the question plus "can't change the source" points to a hook at the tool boundary.

**Other ways the exam could ask this:**
- *Same rule, new setting:* status codes come back as numbers (`3`, `7`) that the agent misreads. A `PostToolUse` hook maps them to labels (`"shipped"`, `"returned"`).
- *Flip a condition:* if the problem were that `lookup_order` returns 40 fields and the agent loses track, the answer is **trimming** tool output to the relevant fields (task 5.1). That's still code at the boundary, but for context, not format.
- *Neighboring objective (1.5, pre-call side):* "refunds over $500 must go to a human". A pre-call (`PreToolUse`) hook blocks `process_refund` above the threshold and redirects to escalation.

**Current docs:** `PostToolUse` can append context (`additionalContext`) or replace the result (`updatedToolOutput`). The exam only expects you to know that it transforms results before the model sees them.

**Source:** [Agent SDK hooks](https://code.claude.com/docs/en/agent-sdk/hooks)

---

## Q3 · Key D · Objective 2.2 · Structured MCP tool errors

**Question type:** best improves *both* behaviors. The answer must fix two opposite failures at once.

**The clue:** one error message ("Operation failed") produces two wrong reactions: retrying something that can never succeed, and giving up on something that might. The agent can't tell the two failures apart.

**Why D:** Recovery depends on knowing what kind of failure happened. A business-rule rejection (outside the 30-day window) is not retryable, and the customer needs the policy explained. A transient timeout *is* retryable. MCP puts tool execution errors, including business-logic errors, in the result with `isError: true` precisely so the model can see them and react. The guide asks you to put the category, retryability, and a readable explanation in that error content.

**Why not the others:**
- **A** is one blunt rule for two different failures. It still retries the policy rejection once and still gives up on timeouts after one try, and the customer still gets no explanation.
- **B** retries business-rule failures that will never succeed, and still returns the generic message the agent can't act on.
- **C** reports a failure as success with an empty result. The guide names this anti-pattern: the agent would tell the customer nothing happened, or carry on as though the refund went through.

**Work it backwards:** If one error message causes *different* wrong behaviors, the missing ingredient is information. The fix makes the error say what kind of failure it is and what to do next.

**Other ways the exam could ask this:**
- *Same rule, new setting:* `lookup_order` returns "not found" both for a nonexistent order and when the database is unreachable. Distinguish an access failure from a valid empty result.
- *Flip a condition:* if *every* failure were a transient timeout, the right fix would be bounded retry. Ideally the server or subagent recovers locally and reports only what it couldn't resolve.
- *Neighboring objective (5.3):* in a multi-agent system, the subagent returns structured error context (type, attempted query, partial results, alternatives) to the coordinator. That's official sample Q9 in the S3 block (guide Q8).

**Watch the spec:** `isError` is a real MCP field. `errorCategory` and `isRetryable` are not spec fields; they're content you design into the error result, as the guide describes.

**Source:** [MCP tools · error handling](https://modelcontextprotocol.io/specification/2026-07-28/server/tools)

---

## Q4 · Keys A, B · Objective 5.2 · Escalation and ambiguity

**Question type:** Select TWO. Each correct option has to stand on its own.

**The clue:** the frame says "knowing when to escalate". The options mix real triggers with the guide's named poor proxies.

**Why A and B:** The guide lists the escalation triggers: the customer explicitly asks for a human (honor it immediately, even if the agent could solve it), and a policy gap or exception (the policy doesn't cover the case, so the agent shouldn't invent one). It also lists no meaningful progress as a trigger.

**Why not the others:**
- **C** uses sentiment, which isn't complexity. The guide's guidance for a frustrated but solvable case is to acknowledge the frustration, offer the resolution, and escalate only if the customer repeats the request for a human.
- **D** is an ambiguity problem, not an escalation trigger. With multiple matches, ask for more identifiers and never guess.
- **E** relies on self-reported confidence, which is poorly calibrated, as official sample Q10 says. The agent is most confidently wrong on the hard cases.

**Work it backwards:** For each option, ask whether a human is actually needed or whether the agent just needs more information or more empathy. Escalate only for the first.

**Other ways the exam could ask this:**
- *Same rule, new setting:* "Which signal should trigger escalation?" with a single answer. The answer is the explicit request for a human or the policy gap, and the distractors are sentiment and confidence scores.
- *Flip a condition:* if the frustrated customer in C asks for a manager a second time, escalation becomes correct.
- *Neighboring objective (1.4):* once you escalate, *how* do you hand off? With a structured summary (Q7).

**Source:** CCAR-F guide task 5.2 · [Customer support chat guide](https://platform.claude.com/docs/en/about-claude/use-case-guides/customer-support-chat)

---

## Q5 · Key B · Objective 5.1 · Long interactions

**Question type:** most effective fix, with a constraint ("to control cost").

**The clue:** the agent loses specific values ("wrong refund amount", re-asks for "an order number the customer already gave") after summarization. Progressive summarization is known to lose exact numbers, dates, and commitments.

**Why B:** A case-facts block holds the details that must stay exact. It lives outside the summarized history and goes with every request, so summaries can compress the rest of the conversation without losing them.

**Why not the others:**
- **A** delays the loss without preventing it. The 41st turn still gets a lossy summary.
- **C** is still probabilistic, and it keeps the facts inside the very thing being compressed. Every re-summarization is another chance to drop or alter a value. The guide keeps the case-facts block *outside* the summarized history.
- **D** breaks the cost constraint in the stem. A bigger window also doesn't guarantee attention to details buried mid-conversation (lost in the middle).

**Work it backwards:** If specific values get lost when context is compressed, pull those values out and keep them where compression can't touch them. Any option that tweaks the compression itself only treats the symptom.

**Other ways the exam could ask this:**
- *Same rule, new setting:* in a research pipeline, the synthesis agent loses which source a statistic came from after summarization. Keep structured claim-to-source mappings (task 5.6).
- *Flip a condition:* if the context fills up because each `lookup_order` result has 40+ fields, the fix is trimming tool output to the needed fields before it accumulates.
- *Neighboring objective (5.1, placement):* key facts get ignored in a long prompt. Put them first and use explicit section headers, because of lost-in-the-middle effects.

**Source:** [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) · [Manage tool context](https://platform.claude.com/docs/en/agents-and-tools/tool-use/manage-tool-context)

---

## Q6 · Key A · Objective 2.3 · Tool distribution

**Question type:** first step.

**The clue:** "19 tools: its four support tools plus 15 operations tools", and a support agent calling `update_inventory`. Most of these tools don't belong to the role at all.

**Why A:** The guide is explicit: too many tools degrade selection, and tools outside an agent's role get misused. Scope tools to the role. Rare cross-role needs go through a path built for them, here escalation. This is also least privilege: a support agent that can't call `update_inventory` can't misuse it.

**Why not the others:**
- **B** helps with confusing tools that *belong*, as in official sample Q9. Here the problem is tools that shouldn't be there, and better descriptions still leave 15 extra tools in play.
- **C** over-engineers the problem. A classifier and routing layer replace a configuration change.
- **D** is a detective control. Logging finds misuse after the damage and prevents nothing, and least privilege means removal.

**Work it backwards:** Compare this with sample Q9. Both stems show wrong tool selection, so ask whether the confused tools *belong* to the agent. If they do, improve descriptions first. If they don't, remove them first.

**Other ways the exam could ask this:**
- *Same rule, new setting:* a research synthesis agent was given every web search tool. Give it a scoped `verify_fact` tool for the common case only (official sample Q10 in the S3 block, guide Q9).
- *Flip a condition:* if all 19 tools were genuinely needed by the role, look at descriptions and naming first (2.1). The fix might also be splitting the work across specialized agents.
- *Neighboring objective (2.3, `tool_choice`):* you need the agent's *first* action to be a particular tool call. Forced tool choice (`{"type": "tool", "name": …}`) makes that call happen.

**Source:** [Define tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools) · [Writing tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents)

---

## Q7 · Key C · Objective 1.4 · Escalation handoff

**Question type:** most direct fix.

**The clue:** humans "re-read the transcript or ask the customer to repeat details", and the reason field holds "customer needs help with refund". The handoff carries no usable facts.

**Why C:** The guide defines a good handoff as a structured summary: customer ID, root cause, amounts, and recommended action. It's for people who don't have time for the transcript. Making the tool *require* those fields enforces the structure every time instead of hoping the prose is good.

**Why not the others:**
- **A** hands over what they're already wading through. The transcript is the problem, not the fix.
- **B** is probabilistic and unstructured. Longer prose doesn't guarantee the right facts.
- **D** fetches raw records but loses what only the agent knows: the diagnosed root cause, what it already tried, and what it recommends.

**Work it backwards:** Ask what the recipient needs in order to act without re-investigating. Then pick the option that guarantees exactly that, in a fixed structure.

**Other ways the exam could ask this:**
- *Same rule, new setting:* a subagent returns long reasoning to the coordinator, whose context is tight. Return structured findings instead of verbose reasoning (5.1).
- *Flip a condition:* if the human agents *did* need full history for a legal audit, attach the transcript **in addition to** the structured summary, never in place of it.
- *Neighboring objective (1.4, multi-concern):* a customer raises three issues in one message. Decompose them, investigate in parallel with shared context, and send back one combined resolution.

**Source:** CCAR-F guide task 1.4 · [Customer support chat guide](https://platform.claude.com/docs/en/about-claude/use-case-guides/customer-support-chat)

---

## Q8 · Key A · Objective 1.4 · *Official sample*

**Official rationale (condensed):** a required tool sequence for critical business logic needs programmatic enforcement. B and C rely on probabilistic compliance, which isn't enough when errors cost money. D addresses tool *availability*, not tool *order*.

**The clue:** "incorrect refunds" means financial consequences, so the rule has to hold every time.

**Work it backwards:** Ask whether the rule must hold every time. If yes, choose code (a gate or hook). If it's a judgment call, a prompt is proportionate.

**Other ways the exam could ask this:**
- *Same rule, new setting:* refunds above $500 must go to a human. A pre-call hook blocks `process_refund` and redirects to `escalate_to_human`.
- *Flip a condition:* if the rule were a tone preference ("greet returning customers by name"), prompt guidance is the proportionate fix. No financial consequence means no gate.
- *Neighboring objective (5.2):* compare Q10. Escalation calibration is judgment, so criteria + few-shot is right there. Know which side of the line each stem is on.

**Source:** CCAR-F guide §9 Q1 · [Agent SDK hooks](https://code.claude.com/docs/en/agent-sdk/hooks)

---

## Q9 · Key B · Objective 2.1 · *Official sample*

**Official rationale (condensed):** tool descriptions are the main signal the model uses to select tools. Minimal descriptions are the root cause, and expanding them is a low-effort, high-leverage fix. Few-shot (A) adds tokens without fixing the cause. A routing layer (C) is over-engineered. Consolidation (D) is valid but more effort than a first step warrants.

**The clue:** "Both tools have minimal descriptions" and "most effective first step". The stem tells you the root cause outright.

**Work it backwards:** "First step" means the least machinery that addresses the stated cause. When the stem quotes the descriptions, it's telling you to fix them.

**Other ways the exam could ask this:**
- *Same rule, new setting:* a codebase agent keeps using built-in Grep instead of a more capable MCP search tool. Write a richer MCP tool description (2.4).
- *Flip a condition:* if the descriptions were already detailed and the tools still overlapped in purpose, rename or split them so each has a distinct contract. Consolidation could then be the right next step.
- *Neighboring objective (2.3):* see Q6. When the misused tool shouldn't be there at all, remove it.

**Source:** CCAR-F guide §9 Q2 · [Define tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools)

---

## Q10 · Key A · Objective 5.2 · *Official sample*

**Official rationale (condensed):** explicit criteria + few-shot fix the root cause, unclear decision boundaries, and they're the proportionate first response. Self-reported confidence (B) is poorly calibrated. A trained classifier (C) is over-engineered before prompt work has been tried. Sentiment (D) doesn't track complexity.

**The clue:** the agent escalates easy cases and handles hard ones itself. It's miscalibrated in *both* directions, which means it doesn't know where the boundary is.

**Work it backwards:** When the agent misjudges *which cases* need X, teach the boundary with explicit criteria and examples. Reach for classifiers, confidence scores, and sentiment only after that's been tried, and in practice they're distractors on this exam.

**Other ways the exam could ask this:**
- *Same rule, new setting:* a CI review agent flags style nits as critical. Use explicit severity criteria with concrete examples (4.1).
- *Flip a condition:* if the boundary were a hard rule ("refunds over $500 always need a human"), enforce it in code (Q8's logic).
- *Neighboring objective (4.2):* few-shot examples work best when they target the *ambiguous* cases and show why one action beats the plausible alternative.

**Source:** CCAR-F guide §9 Q3 · [Customer support chat guide](https://platform.claude.com/docs/en/about-claude/use-case-guides/customer-support-chat)

---

## Scenario playbook

### What the frame tells you
| Phrase in the frame | What it puts in play |
|---|---|
| "using the Claude Agent SDK" | The agent loop (`stop_reason`), hooks, and the SDK's control points |
| "custom MCP tools" with four named tools | Tool descriptions, error design, which tools the agent gets |
| "high-ambiguity requests" | Escalation criteria, few-shot for ambiguous cases, clarifying questions |
| `process_refund` | Money moves, so rules that must hold need code, not prompts |
| "80%+ first-contact resolution **while knowing when to escalate**" | Both over-escalation and under-escalation are wrong |

### The design to hold in your head
```
customer ──► agent loop (continue on stop_reason "tool_use", stop on "end_turn")
               │
               ├─► get_customer ─► lookup_order ─► process_refund
               │       ▲ pre-call gate: verified ID, amount limit → else escalate
               │       ▼ PostToolUse: normalize formats, trim fields
               ├─► escalate_to_human (structured fields: customer ID, root cause, amount, recommended action)
               └─ context = case-facts block + trimmed history
```

### Question families
| Family | What the stem looks like | Deciding rule | Objectives |
|---|---|---|---|
| Required order or limit | "skips verification", "refund over $X processed" | Programmatic gate or pre-call hook | 1.4, 1.5 |
| Inconsistent tool data | "timestamps in two formats", "numeric status codes" | `PostToolUse` normalization | 1.5 |
| Similar tools confused | "calls `get_customer` for order questions" | Rewrite the descriptions first | 2.1 |
| Wrong or too many tools | "connected to the ops server", "19 tools" | Scope tools to the role | 2.3 |
| Tool failures | "Operation failed", blind retries, giving up | Structured error content | 2.2 |
| Escalation calibration | "FCR 55%", easy cases escalated, hard ones kept | Explicit criteria + few-shot | 5.2, 4.2 |
| Escalation triggers | "asks for a manager", "policy doesn't cover", "two matches" | Request or policy gap → escalate. Ambiguous match → ask | 5.2 |
| Handoff quality | "humans re-read transcripts" | Structured handoff summary | 1.4 |
| Long conversations | "forgets amount after 40 turns" | Case-facts block, trimmed tool output | 5.1 |
| Loop control | "stops after saying it will look something up" | `stop_reason` | 1.1 |
| Multi-concern messages | "three issues in one message, only one handled" | Decompose, investigate in parallel, one combined answer | 1.4 |

### The tension S1 is built around
**When is a prompt enough?**
- If the rule must hold every time and has money or compliance attached (verify identity, refund limits), use code.
- If it's a judgment call (is this case complex, is this a policy gap), explicit criteria + few-shot is the proportionate fix.

Official samples Q8 and Q10 sit on opposite sides of that line. Most S1 items ask which side the stem is on.

### Traps that recur in S1
- **Classifier, sentiment analysis, or a self-confidence score** as an option is almost always the distractor.
- **Description rewrite vs tool removal:** Q9 vs Q6. Ask whether the confused tool belongs.
- **Detective vs preventive:** logging or review queues don't stop a refund that shouldn't happen.
- **Empty-as-success:** hiding a failure is never the fix.
