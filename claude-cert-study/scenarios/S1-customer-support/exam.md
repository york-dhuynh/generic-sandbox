# S1 · Customer Support Resolution Agent · exam block

Answer cold: no docs, no notes, no Claude. Allow about 2 minutes per item (20 minutes for the block). Write a letter and a confidence (H/M/L) for each item, then open [answers.md](answers.md). To have Claude run the block, score it, and walk you back through each miss, use `/cca-scenario S1` instead.

## Scenario

You are building a customer support resolution agent using the Claude Agent SDK. The agent handles high-ambiguity requests like returns, billing disputes, and account issues. It has access to your backend systems through custom Model Context Protocol (MCP) tools (`get_customer`, `lookup_order`, `process_refund`, `escalate_to_human`). Your target is 80%+ first-contact resolution while knowing when to escalate.

---

### Q1

Your custom agent loop sends a request to the Messages API, then checks the response. If the response contains any text block, the loop treats the turn as complete and returns that text to the customer. In 9% of conversations, the customer receives only "Let me pull up your order details now" and nothing more. Each of those responses also contained a `tool_use` block for `lookup_order` that was never executed. What change fixes this?

A. Instruct the agent in the system prompt never to write text in the same response as a tool call.
B. Keep looping until the response text contains a closing phrase such as "Is there anything else?", up to 10 iterations.
C. Raise `max_tokens` so the agent can finish the lookup and its summary within a single response.
D. Continue while `stop_reason` is `"tool_use"`: run the tools, append their results, and call again until `"end_turn"`.

### Q2

Orders come from two backends. The legacy backend returns delivery dates as Unix epoch seconds (for example, `1729900800`). The new backend returns ISO 8601 strings. Return eligibility depends on whether delivery was within the last 30 days. Audits show the agent misjudges eligibility on 6% of legacy orders, almost always when it has to reason about the epoch values. Other teams own both backends and will not change them this quarter. What is the most reliable fix?

A. Add system prompt guidance on converting Unix timestamps to calendar dates, with two worked examples.
B. Add a `convert_timestamp` tool and instruct the agent to call it whenever a date looks numeric.
C. Add a `PostToolUse` hook on `lookup_order` that converts its dates to ISO 8601 before the agent sees them.
D. Route legacy orders to a subagent whose system prompt specializes in the legacy backend's data formats.

### Q3

When `process_refund` rejects a request, the MCP server returns `isError: true` with the text "Operation failed". Logs show two patterns:
- For refunds outside the 30-day window, the agent retries the identical call 3–5 times, then gives the customer a vague apology.
- On genuine payment-gateway timeouts, it gives up immediately and escalates.

What change best improves both behaviors?

A. Add a system prompt rule allowing one retry per failed tool call, followed by escalation.
B. Retry every failure inside the server with exponential backoff, returning "Operation failed" once retries run out.
C. Return `isError: false` with an empty result for policy rejections, and keep `isError: true` for timeouts.
D. Return error content with the failure category, whether retrying can help, and a customer-facing explanation.

### Q4

You are writing explicit escalation criteria into the system prompt. Which TWO situations should the criteria tell the agent to escalate to a human? **(Select TWO.)**

A. The customer asks to speak with a human, even though the issue is a standard return the agent could resolve.
B. The refund policy does not cover the request, so resolving it would require a policy exception.
C. The customer writes in all capitals and sounds very frustrated, although the issue is a routine replacement.
D. Two accounts match the customer's name and city, and the customer has not yet given an email or order number.
E. The agent rates its own confidence in the proposed resolution below 7 out of 10.

### Q5

Billing disputes that span several orders often run past 40 turns. To control cost, older turns are summarized once the history passes a size threshold. QA finds that after summarization, the agent sometimes quotes the wrong refund amount or asks again for an order number the customer already gave. What is the most effective fix?

A. Raise the summarization threshold so older turns are summarized later in long conversations.
B. Keep IDs, amounts, and commitments in a case-facts block outside the summary, sent with every request.
C. Instruct the summarizer to copy every order number, amount, and date verbatim into each new summary.
D. Move to a model with a larger context window and stop summarizing the older turns of each conversation.

### Q6

To launch quickly, the team connected the agent to the company's internal operations MCP server. The agent now sees 19 tools: its four support tools plus 15 operations tools such as `update_inventory`, `adjust_loyalty_points`, and `create_shipment`. Tool-selection errors have risen since launch. In one incident, the agent called `update_inventory` after a customer reported a damaged item. What should you do first?

A. Give the agent only the tools the support role needs, and route rare cross-team actions through escalation.
B. Rewrite all 19 tool descriptions so each states when to use it and how it differs from similar tools.
C. Add a classifier in front of the agent that predicts which tools each request needs and enables only those.
D. Add a `PreToolUse` hook that logs every call to a non-support tool for weekly review by the operations team.

### Q7

Human agents who receive escalations say they spend the first 4–5 minutes of every handoff re-reading the transcript or asking the customer to repeat details. The `escalate_to_human` tool takes a single free-text `reason` field, which the agent fills with entries like "customer needs help with refund". What change most directly fixes this?

A. Attach the complete conversation transcript to every escalation so the human agent has all the details.
B. Instruct the agent in the system prompt to write longer, more detailed reasons whenever it escalates.
C. Make `escalate_to_human` require structured fields: customer ID, root cause, amount, and recommended action.
D. Have the human agents' console call `get_customer` and `lookup_order` automatically whenever an escalation arrives.

---

## Official sample questions (CCAR-F exam guide v1.0, Section 9)

These three are reproduced from the official guide. They show the real exam's style. Answer them cold too, even if you've read them before. What matters is whether you can explain *why* the key wins.

### Q8

Production data shows that in 12% of cases, your agent skips `get_customer` entirely and calls `lookup_order` using only the customer's stated name, occasionally leading to misidentified accounts and incorrect refunds. What change would most effectively address this reliability issue?

A. Add a programmatic prerequisite that blocks `lookup_order` and `process_refund` calls until `get_customer` has returned a verified customer ID.
B. Enhance the system prompt to state that customer verification via `get_customer` is mandatory before any order operations.
C. Add few-shot examples showing the agent always calling `get_customer` first, even when customers volunteer order details.
D. Implement a routing classifier that analyzes each request and enables only the subset of tools appropriate for that request type.

### Q9

Production logs show the agent frequently calls `get_customer` when users ask about orders (e.g., "check my order #12345"), instead of calling `lookup_order`. Both tools have minimal descriptions ("Retrieves customer information" / "Retrieves order details") and accept similar identifier formats. What's the most effective first step to improve tool selection reliability?

A. Add few-shot examples to the system prompt demonstrating correct tool selection patterns, with 5-8 examples showing order-related queries routing to `lookup_order`.
B. Expand each tool's description to include input formats it handles, example queries, edge cases, and boundaries explaining when to use it versus similar tools.
C. Implement a routing layer that parses user input before each turn and pre-selects the appropriate tool based on detected keywords and identifier patterns.
D. Consolidate both tools into a single `lookup_entity` tool that accepts any identifier and internally determines which backend to query.

### Q10

Your agent achieves 55% first-contact resolution, well below the 80% target. Logs show it escalates straightforward cases (standard damage replacements with photo evidence) while attempting to autonomously handle complex situations requiring policy exceptions. What's the most effective way to improve escalation calibration?

A. Add explicit escalation criteria to your system prompt with few-shot examples demonstrating when to escalate versus resolve autonomously.
B. Have the agent self-report a confidence score (1-10) before each response and automatically route requests to humans when confidence falls below a threshold.
C. Deploy a separate classifier model trained on historical tickets to predict which requests need escalation before the main agent begins processing.
D. Implement sentiment analysis to detect customer frustration levels and automatically escalate when negative sentiment exceeds a threshold.
