# S6 · Structured Data Extraction · answers and reverse engineering

Score yourself with the key, then work through every miss and every guess. A guess is a low-confidence answer, even when it was right. For each one, cover the explanation, read the clue, and try to say why the key wins before reading on.

The guide has no official samples for S6, so every item here is a practice item. The keys rest on the guide's task statements 4.2–4.5, 2.3, and 5.5, and on the linked docs.

## Answer key

| Q | Key | Objective | Rule in one line |
|---|---|---|---|
| 1 | B | 4.3 Schema design | A required field the source may lack invites fabrication; make it nullable |
| 2 | D | 4.4 Retry with feedback | Retry with the document, the failed output, and the specific error, never blind |
| 3 | A | 4.3 `tool_choice` | Several schemas and an unknown type → `"any"` guarantees a tool call |
| 4 | A | 2.3 Forced tool | A step that must run first → force that named tool, then continue in later turns |
| 5 | D | 4.5 Batch failures | Resubmit only the failed `custom_id`s, fixed for the cause of failure |
| 6 | C, D | 5.5 Human review | Before automating: accuracy by segment, and thresholds calibrated on labeled data |
| 7 | B | 4.2 Few-shot | Instructions read inconsistently across layouts → examples of each layout |
| 8 | C | 4.4 Self-check fields | Extract stated and calculated values side by side and flag the conflict |
| 9 | C | 5.5 Ongoing sampling | After automating, keep measuring with a stratified random sample of auto-approved output |
| 10 | B, E | 4.3 Enum design | Extensible categories get `other` + detail; ambiguous ones get `unclear` |

---

## Q1 · Key B · Objective 4.3 · Schema design

**Question type:** root cause. The stem asks you to fix why the bad values appear, not to catch them afterwards.

**The clue:** "marks `purchase_order_number` as a **required** string" together with "don't print a PO number **at all**". The schema demands a value the document can't supply, so the model has to put *something* there.

**Why B:** The guide says to design fields as optional or nullable when source documents may not contain the information. That prevents the model from fabricating values to satisfy required fields. A nullable field with a clear meaning for null ("the document shows none") gives the model an honest answer to give. This is the schema version of the docs' advice to let Claude say "I don't know".

**Why not the others:**
- **A** fights the schema with a prompt. The field is still required, so the model must still produce a string. The prompt rule and the schema pull in opposite directions, and the schema shapes the output.
- **C** checks format, not truth. A plausible-looking fabricated PO number matches the format, and so might a copied invoice number. Valid shape isn't a real value.
- **D** retries for information that doesn't exist. The guide states that retries don't work when the required information is simply absent from the source document. The ERP check is a fine safety net, but it doesn't remove the cause.

**Work it backwards:** When an extraction invents values, first ask whether the source contains them. If it often doesn't, look at what the schema forces. A required field with no source value is a fabrication generator.

**Other ways the exam could ask this:**
- *Same rule, new setting:* contracts sometimes lack a termination date, and the extraction fills in the effective date. Make `termination_date` nullable.
- *Flip a condition:* if every invoice *did* print a PO number and the model sometimes skipped it, the field should stay required. The fix then is about extraction quality: few-shot examples for the layouts where it's missed, or retry with the validation error.
- *Neighboring objective (4.4):* "validation fails and retries keep failing for one field". Check whether the information is absent from the source before you tune retries.

**Source:** CCAR-F guide task 4.3 · [Structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) · [Reduce hallucinations](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations)

---

## Q2 · Key D · Objective 4.4 · Retry with error feedback

**Question type:** design fix for an existing loop. The stem tells you the retry exists and isn't working.

**The clue:** "resends the **identical** request" passes 10% of the time, while "the source documents **do** contain the correct values". The information is there; the model just isn't told what went wrong.

**Why D:** The guide's retry pattern is a follow-up request with the original document, the failed extraction, and the specific validation errors. Telling the model *which* line items and *how far* the sum is off turns a re-roll into a correction. That works here because the problem is fixable from the source.

**Why not the others:**
- **A** is a blind re-roll with a higher budget. It spends up to five times the cost for slightly better odds, and the model still doesn't know what to fix.
- **B** confuses syntax with semantics. Tool use and strict schemas guarantee valid structure and types. They don't guarantee that numbers add up, and JSON Schema can't express "these items sum to that total".
- **C** hides the symptom and loses data. If the model missed a line item, a computed total still agrees with the (incomplete) line items, so the error passes silently. You also lose the ability to spot vendors whose printed totals are wrong (Q8).

**Work it backwards:** A retry is only as good as the feedback it carries. If the retry is identical to the first attempt, add the specific error. Then check whether the information exists in the source: if it does, feedback helps; if it doesn't, nothing will.

**Other ways the exam could ask this:**
- *Same rule, new setting:* a date comes back as "next Friday" and fails ISO 8601 validation. Retry with the error ("`due_date` must be YYYY-MM-DD; got 'next Friday'"), and add format-normalization rules to the prompt.
- *Flip a condition:* if the failing invoices *didn't* contain the missing values (for example, line items are in an attachment you didn't send), no retry fixes it. Make the field nullable, or route the document to a human.
- *Neighboring objective (4.3):* "which errors does tool use with a schema eliminate?" Syntax errors such as malformed JSON and wrong types. Not semantic errors such as wrong sums or values in the wrong field.

**Current docs:** strict tool use and JSON outputs guarantee schema compliance (drift row 6). The guide's point stands: compliance with the schema isn't correctness.

**Source:** CCAR-F guide task 4.4 · [Structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)

---

## Q3 · Key A · Objective 4.3 · `tool_choice` with several schemas

**Question type:** most reliable fix. "Reliable" means you want a guarantee, not a likelihood.

**The clue:** "three extraction tools", "type isn't known in advance", `"auto"`, and "calls no tool". With `"auto"`, the model may answer in text instead of calling a tool, and it did.

**Why A:** `tool_choice: "any"` means the model must call one of the provided tools but can choose which one. That's exactly the guide's skill: set `"any"` to guarantee structured output when several extraction schemas exist and the document type is unknown. The docs add that with `any` or a forced tool, the model doesn't emit natural-language text before the `tool_use` block.

**Why not the others:**
- **B** guarantees a tool call, but the wrong one for a third or more of the queue. Receipts and purchase orders would be squeezed into the invoice schema.
- **C** is probabilistic. A prompt rule lowers the 7% but doesn't guarantee it, and the API has a setting for this exact guarantee.
- **D** handles the symptom downstream. It builds a fragile second parser for prose instead of preventing prose.

**Work it backwards:** Learn the three settings as guarantees:
- `"auto"`: maybe a tool, maybe text.
- `"any"`: certainly a tool, the model's choice of which.
- Forced (`{"type": "tool", "name": …}`): certainly *that* tool.

Then match the guarantee to what the stem needs. Here the need is "some tool, but the right one for the type", so `"any"`.

**Other ways the exam could ask this:**
- *Same rule, new setting:* a single-schema pipeline where the model sometimes chats instead of extracting. With one tool, `"any"` or forcing that tool both guarantee the call.
- *Flip a condition:* if the document type *were* known before the call (for example, routed by upload folder), force the matching tool by name. There's no reason to let the model choose.
- *Neighboring objective (2.3):* a particular tool must run *first* (Q4). `"any"` isn't enough there; you need the forced named tool.

**Current docs (drift row 18):** the define-tools page now says forced tool use (`"any"` and a named `tool`) returns a 400 error on Claude Opus 5.5, Sonnet 5.5, Fable 5.1, and Mythos 5.1, and isn't supported with manual extended thinking. On those models the docs recommend `"auto"` with strict tool use, or structured outputs (JSON outputs). **On the exam, answer per the guide: `"any"`.**

**Source:** CCAR-F guide tasks 4.3 and 2.3 · [Define tools · Forcing tool use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools)

---

## Q4 · Key A · Objective 2.3 · Forced tool selection

**Question type:** a guarantee ("guarantees that metadata extraction happens first"). That rules out anything probabilistic.

**The clue:** "enrichment tools need the metadata as input" and the model "calls `lookup_vendor` first with a vendor name it guessed". There's an ordering dependency, and the model sometimes skips it.

**Why A:** Forced selection, `tool_choice: {"type": "tool", "name": "extract_metadata"}`, guarantees that *that* tool is called. The guide's own example is forcing `extract_metadata` before enrichment tools, then handling later steps in follow-up turns where the model can choose freely.

**Why not the others:**
- **B** guarantees *a* tool call but not *which* one. The model could still open with `lookup_vendor`.
- **C** relies on an ordering effect the docs don't promise. The order of tool definitions isn't a control mechanism.
- **D** is probabilistic. Prompts lower the failure rate but can't guarantee the order. Here the step is wrong 15% of the time and corrupts every downstream enrichment.

**Work it backwards:** "Guarantees" plus "first" points to forcing the named tool on the first call. If the stem said "some tool" instead of "this tool", the answer would be `"any"`.

**Other ways the exam could ask this:**
- *Same rule, new setting:* a classification step (`classify_document`) must run before the type-specific extraction. Force it on the first call, then call the matching extractor.
- *Flip a condition:* if the requirement were only "never answer in prose" rather than "this tool first", `"any"` is enough (Q3).
- *Neighboring objective (1.4 / 1.5, S1):* in an Agent SDK agent where a tool order has financial consequences, the guide's answer is a programmatic prerequisite or hook that blocks the later tool until the earlier one has run. Forced `tool_choice` controls only the next call; a gate controls the whole session.

**Current docs (drift row 18):** as in Q3, forced `tool_choice` returns a 400 error on the newest models (Opus 5.5, Sonnet 5.5, Fable 5.1, Mythos 5.1). On those models the docs recommend `auto` with strict tool use, or structured outputs. For example, get the metadata with structured outputs in a first request, then pass it into the enrichment request. **On the exam, answer per the guide: force the named tool.**

**Source:** CCAR-F guide task 2.3 · [Define tools · Forcing tool use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools)

---

## Q5 · Key D · Objective 4.5 · Batch failure handling

**Question type:** next step after a partial failure.

**The clue:** "11,640 succeeded and 360 errored", and the cause is that they "exceeded the model's context window". It's a known, specific, deterministic cause affecting a small, identifiable subset.

**Why D:** The guide's batch-failure skill is to resubmit only the failed documents, identified by `custom_id`, with a change that addresses the failure, such as chunking documents that were too long. `custom_id` exists so you can match results to requests. The docs stress that because results can come back in any order.

**Why not the others:**
- **A** misreads the limit and wastes money. `max_tokens` caps the *output*, not the input, and re-running 11,640 successful requests pays for them twice.
- **B** assumes a transient error. Oversized input fails the same way every time, so an unchanged resubmission errors again.
- **C** needs a mid-request loop with your own (client) tool, which a batch request can't run, because nothing can send back a `tool_result` (guide task 4.5; drift row 20). A "load sections on demand" loop needs the synchronous API, or splitting up front.

**Work it backwards:** For a partial batch failure, ask two questions. Which requests failed? (Use `custom_id`; resubmit only those.) Why did they fail? (Fix that cause before resubmitting.) Any option that reruns successes, or resubmits without a change for a deterministic failure, is a distractor.

**Other ways the exam could ask this:**
- *Same rule, new setting:* a batch of 5,000 receipts has 40 failures caused by an invalid parameter in a request template. Fix the template and resubmit those 40 `custom_id`s.
- *Flip a condition:* if the 360 were `expired` (the batch hit its 24-hour limit under heavy load) rather than errored for size, resubmitting them unchanged is reasonable. The cause is capacity, not the requests.
- *Neighboring objective (4.5, SLA math):* clients need results within 30 hours of a document arriving, and a batch can take up to 24 hours. Worst case is the wait before submission plus 24 hours, so submit at least every 6 hours. The guide's example uses 4-hour windows to leave margin. Every 12 or 24 hours breaks the SLA.

**Current docs:** most batches finish within an hour, but only completion within 24 hours is guaranteed, and requests that don't finish expire (drift row 9). Plan around 24 hours. The docs also list tool use and multi-turn conversations as batchable: server tools (web search, code execution, MCP connector) run in a loop inside the request (drift row 20). A client tool that you execute still can't return its result mid-request.

**Source:** CCAR-F guide task 4.5 · [Batch processing](https://platform.claude.com/docs/en/build-with-claude/batch-processing)

---

## Q6 · Keys C, D · Objective 5.5 · Human review and confidence calibration

**Question type:** Select TWO, "before reducing". You're looking for the checks that must pass first.

**The clue:** "**overall** … 97%" and "**model-reported** confidence is 0.9 or higher". These are two unvalidated assumptions: that the aggregate is uniform, and that the confidence number means something.

**Why C and D:**
- **C:** The guide warns that aggregate accuracy (its example is 97%) can hide poor performance on specific document types or fields, and it asks you to validate by segment before automating. A rare document type at 70% vanishes inside a 97% average.
- **D:** Field-level confidence is only useful after it has been calibrated against a labeled validation set. Only then can a threshold mean "at or above 0.9, accuracy is X%". Uncalibrated self-reported confidence is the poor proxy that official sample Q3 warns about.

**Why not the others:**
- **A** gives a more precise estimate of the wrong metric. More documents tighten the aggregate without breaking it down.
- **B** is self-review. The same model rechecking its own output keeps its own reasoning and blind spots, and it doesn't measure anything.
- **E** moves an uncalibrated number. Without calibration, 0.99 doesn't mean more reliable than 0.9; it only means fewer documents skip review.

**Work it backwards:** "Can we stop human review?" has two prerequisites. Is accuracy good *everywhere*, not just on average? Does the confidence score *mean* what the threshold assumes? Any option that doesn't test one of those is a distractor.

**Other ways the exam could ask this:**
- *Same rule, new setting:* a contract extractor scores 96% overall, but `indemnification_cap` is right only 78% of the time. Keep human review on that field even after automating the others.
- *Flip a condition:* if segment accuracy and calibration had already been checked, the next question is ongoing monitoring after automation. That's stratified random sampling of auto-approved output (Q9).
- *Neighboring objective (4.4):* low-confidence or contradictory documents go to humans. A `conflict_detected` flag (Q8) is one of the cleanest routing signals.

**Source:** CCAR-F guide task 5.5 (primary) · background: [Develop tests](https://platform.claude.com/docs/en/test-and-evaluate/develop-tests)

---

## Q7 · Key B · Objective 4.2 · Few-shot for varied document structures

**Question type:** most effective next step.

**The clue:** "the instructions describe every field **in detail**", yet results split by **layout**: numbered bibliographies work, inline and footnote styles return empty arrays or invented DOIs. Detailed instructions are being read inconsistently across structures.

**Why B:** The guide calls few-shot examples the most effective fix when detailed instructions alone give inconsistent results. It names both of these cases: handling varied document structures (inline citations vs bibliographies), and fixing empty or null extraction of required fields. Examples show the model what correct extraction looks like for each layout, which prose struggles to convey.

**Why not the others:**
- **A** adds more of what's already failing. The instructions are already detailed, and the gap is in applying them across layouts, not in coverage.
- **C** forces fabrication. Requiring at least one reference when the model can't find any produces invented entries, worse than empty ones (see Q1).
- **D** is a bigger model plus a second pipeline for a demonstration problem. It's more machinery and cost before the cheap, targeted fix has been tried.

**Work it backwards:** If the stem says instructions are already detailed and quality varies by input *shape*, the answer is examples covering those shapes. If instead the stem says the instructions are vague, the answer is clearer criteria first (4.1).

**Other ways the exam could ask this:**
- *Same rule, new setting:* recipe extraction handles "2 cups" but fabricates values for "a pinch" and "to taste". Add examples of informal measurements, including ones mapped to null or "unspecified".
- *Flip a condition:* if output were inconsistent because it was *malformed* (broken JSON, missing keys), the fix is tool use with a schema, not examples.
- *Neighboring objective (4.3):* the model returns an empty array where the paper truly has no references. That's correct, and the schema should allow it: an empty array or null is the honest answer.

**Current docs:** the guide says 2–4 targeted examples; the prompting guide says 3–5 (drift row 11). Don't let the count decide an item.

**Source:** CCAR-F guide task 4.2 · [Prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)

---

## Q8 · Key C · Objective 4.4 · Self-check fields

**Question type:** schema design to support a downstream requirement ("flagged, not silently corrected").

**The clue:** two different causes produce the same symptom (extraction misses *and* wrong printed totals), plus "flagged for follow-up, not silently corrected". You need to *see* the disagreement, not erase it.

**Why C:** The guide's self-correction pattern is to extract `calculated_total` next to `stated_total` so discrepancies are flagged, and to add a `conflict_detected` boolean for inconsistent source data. That gives downstream code a clean signal:
- On a conflict, retry with the specific mismatch (Q2) to catch extraction misses.
- If the conflict survives the retry, it's probably the vendor's error, so route it to accounting.

Both causes stay visible and separable.

**Why not the others:**
- **A** silently corrects. Wrong vendor totals disappear, and a missed line item yields a self-consistent but wrong total.
- **B** instructs fabrication. It tells the model to falsify line items to match a possibly wrong total.
- **D** asks a schema to check arithmetic. Schemas check structure and types, not whether values sum; the guide's key point is that schemas don't prevent semantic errors. Even if it could, a validation failure can't tell a missed line item from a vendor's wrong total, so it wouldn't single out vendor errors for follow-up.

**Work it backwards:** When the *source* can be wrong, don't let the extraction choose between conflicting values. Capture both and flag the difference, so the decision happens downstream where it can be audited.

**Other ways the exam could ask this:**
- *Same rule, new setting:* a contract's summary page says 24 months, but clause 7 says 36. Extract both with their locations and set `conflict_detected`, so a human resolves it.
- *Flip a condition:* if accounting only wanted extraction errors fixed and trusted vendor totals completely, the retry-with-feedback loop alone (Q2) would be enough.
- *Neighboring objective (5.5):* the `conflict_detected` flag is a routing signal. Contradictory source documents go to human review, ahead of the general low-confidence queue.

**Source:** CCAR-F guide task 4.4

---

## Q9 · Key C · Objective 5.5 · Ongoing error measurement

**Question type:** monitoring design after automation.

**The clue:** "reviewers now see **only** the low-confidence queue" plus "a new invoice layout". No human is looking at the auto-approved output, and a change could make high-confidence extractions wrong without anyone noticing.

**Why C:** The guide's skill is stratified random sampling of high-confidence extractions to measure error rates and detect new error patterns. Random means the sample represents the auto-approved population. Stratified (by document type, supplier, or field) means small segments, such as one supplier's new layout, still get sampled.

**Why not the others:**
- **A** measures the wrong population. The low-confidence queue is selected *because* it's uncertain, so its error rate says nothing about the auto-approved set.
- **B** is reactive and biased. You find errors only when someone downstream notices and complains, often long after bad data has spread.
- **D** relies on the model's self-assessment again. A layout the model misreads confidently stays confident, and confidence doesn't check itself.

**Work it backwards:** To know the error rate of a set nobody reviews, a human has to review a random sample of that set. Stratify it so rare segments aren't missed. Every other option either measures a different set or relies on the model judging itself.

**Other ways the exam could ask this:**
- *Same rule, new setting:* an auto-approved claims classifier. Sample a fixed percentage of auto-approved claims per claim type for weekly audit.
- *Flip a condition:* if you hadn't yet automated anything, the question becomes "what must be true before automating" (Q6): segment accuracy and calibration.
- *Neighboring objective (4.4, `detected_pattern`):* in a review system where humans dismiss findings, add a `detected_pattern` field so you can analyze which patterns produce false positives. It's the same idea: structure the output so humans can measure it systematically.

**Source:** CCAR-F guide task 5.5 (primary) · background: [Develop tests](https://platform.claude.com/docs/en/test-and-evaluate/develop-tests)

---

## Q10 · Keys B, E · Objective 4.3 · Enum design for edge cases

**Question type:** Select TWO. Each key handles a different half of the stem.

**The clue:** two separate problems. "New document types **keep arriving**" is an *extensibility* problem. "Genuinely **ambiguous**" is an *uncertainty* problem. Both get "forced into the closest category".

**Why B and E:**
- **B:** the guide's pattern for extensible categories is an `"other"` enum value plus a detail string. New types land in `other` with a description, and downstream code still gets a stable value. The detail strings show which types deserve their own enum value later.
- **E:** the guide's pattern for ambiguous cases is an `"unclear"` value. It lets the model say "I can't tell" instead of guessing, and gives you a routing signal for review.

**Why not the others:**
- **A** throws away the contract with downstream systems. Free text breaks reporting and integration, which the frame says the system must support.
- **C** is the status quo with a prompt attached. Forcing the closest match is the current behavior and the cause of the corruption.
- **D** freezes the list at what you've already seen. It does nothing for next month's new type and nothing for ambiguous documents.

**Work it backwards:** Ask what an *honest* answer looks like when the model hits each edge case. For "a kind I haven't been given" it's `other` plus what it is. For "I can't tell which" it's `unclear`. The schema must make both answers possible, or the model will be forced to lie in a valid format.

**Other ways the exam could ask this:**
- *Same rule, new setting:* expense categories (`travel`, `meals`, `software`). Add `other` + `category_detail` for new spend types, and `unclear` for mixed receipts.
- *Flip a condition:* if the category list were truly closed and complete (for example, the four document types a regulated form allows), keep the strict enum. An `other` value would only invite drift.
- *Neighboring objective (4.3, normalization):* sources write the same value differently ("USD", "US$", "$"). Keep the strict enum *and* add format-normalization rules to the prompt so the model maps variants to the canonical value.

**Source:** CCAR-F guide task 4.3 · [Structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)

---

## Scenario playbook

### What the frame tells you
| Phrase in the frame | What it puts in play |
|---|---|
| "extracts information from **unstructured documents**" | Varied layouts, so few-shot examples across structures. Missing information, so nullable fields |
| "validates the output using **JSON schemas**" | Tool use + schema, `tool_choice`, the line between syntax and semantics, validation-retry loops |
| "maintains **high accuracy**" | Measuring by segment, calibrated confidence, human review routing, stratified sampling |
| "handle **edge cases** gracefully" | Null over fabrication, `unclear` / `other` + detail, `conflict_detected`, routing to humans |
| "integrate with **downstream systems**" | Guaranteed structured output, stable enums, flags downstream can act on, batches for volume |

### The pipeline to hold in your head
```
documents ──► extraction call
                tool_choice "any"  (several schemas, type unknown)
                forced tool        (extract_metadata must run first)
                schema: required vs nullable · enum + "unclear" / "other"+detail
                        stated_total + calculated_total + conflict_detected
                prompt: field rules · format normalization · few-shot per layout
          ──► validate in code (the schema guarantees shape, not truth)
                ├─ fails, info IS in source  → retry: document + failed output + specific errors
                ├─ fails, info NOT in source → null, or route to human (retry can't help)
                └─ passes ─► field confidence (calibrated on labeled set)
                               ├─ ≥ threshold → downstream
                               └─ low / conflict_detected → human review
volume:     Message Batches · custom_id · resubmit failed only, fixed · window + 24h ≤ SLA
monitoring: accuracy by document type and field · stratified random sample of auto-approved
```

### Question families
| Family | What the stem looks like | Deciding rule | Objectives |
|---|---|---|---|
| Fabricated values | "invents PO numbers", "fills dates that aren't there" | Make the field nullable or optional | 4.3 |
| Prose instead of output | "replies with a summary, no tool call" | `tool_choice: "any"` (or force the one tool) | 4.3 |
| Step must run first | "enrichment ran before metadata" | Force the named tool, then continue in later turns | 2.3, 4.3 |
| Values don't reconcile | "line items don't sum", "value in the wrong field" | Semantic checks in code; schemas don't catch these | 4.3, 4.4 |
| Retry isn't working | "identical retry", "retries never succeed" | Add the specific error; check whether the info exists at all | 4.4 |
| Source contradicts itself | "vendor's total is wrong", "two dates disagree" | Extract both, set `conflict_detected`, route | 4.4, 5.5 |
| Categories that don't fit | "new types arrive", "ambiguous documents" | `other` + detail, `unclear` | 4.3 |
| Inconsistent source formats | "USD / US$ / $", "dates in three formats" | Normalization rules in the prompt alongside the strict schema | 4.3 |
| Layout-dependent failures | "works on format X, fails on format Y" | Few-shot examples covering each structure | 4.2 |
| Volume and cost | "overnight", "12,000 documents", "50% cheaper" | Batches; `custom_id`; resubmit failed only; refine on a sample first | 4.5 |
| Latency commitments | "results within 30 hours", "blocking step" | Window + 24h ≤ SLA; never batch a blocking path | 4.5 |
| "Can we stop reviewing?" | "97% overall", "confidence ≥ 0.9" | Segment accuracy plus calibrated thresholds | 5.5 |
| Monitoring after automation | "reviewers only see low-confidence" | Stratified random sample of auto-approved output | 5.5 |

### The tension S6 is built around
**What does the schema guarantee, and what do you have to check yourself?**
- Tool use with a JSON schema (and today, strict tool use and JSON outputs) guarantees **shape**: valid JSON, correct types, required keys present, enum values from the list.
- It does **not** guarantee **truth**: sums that reconcile, values in the right field, values that actually appear in the source.
- A required field can even *cause* false values, by forcing an answer the document doesn't contain.

Most S6 items ask which side of that line the problem is on:
- **Shape problems:** fix with the schema and `tool_choice`.
- **Truth problems:** fix with semantic validation, retry with specific feedback, nullable fields, conflict flags, and human review.

### Traps that recur in S6
- **"Strict mode will catch it"** for a semantic error such as a wrong sum or a misplaced value.
- **"Make it required"** when the source may not contain the value. That manufactures fabrication.
- **Blind retries**, or retries when the information isn't in the source.
- **Silent correction:** computing or adjusting values so they reconcile instead of flagging the conflict.
- **97% overall** offered as proof. Look for the segment it hides.
- **Self-reported confidence or self-review** used without calibration against labeled data.
- **Bigger model or separate pipeline** for a layout problem that examples would fix.
- **Batch misuse:** a tool loop inside one batch request, resubmitting the whole batch, a blocking step on the batch path, or planning around the typical 1-hour turnaround instead of the 24-hour limit.
