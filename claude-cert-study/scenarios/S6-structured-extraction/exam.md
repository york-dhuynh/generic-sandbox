# S6 · Structured Data Extraction · exam block

Answer cold: no docs, no notes, no Claude. Allow about 2 minutes per item (20 minutes for the block). Write a letter and a confidence (H/M/L) for each item, then open [answers.md](answers.md). To have Claude run the block, score it, and walk you back through each miss, use `/cca-scenario S6` instead.

The exam guide publishes no sample questions for this scenario, so all ten items here were written for this kit to the same standard.

## Scenario

You are building a structured data extraction system using Claude. The system extracts information from unstructured documents, validates the output using JavaScript Object Notation (JSON) schemas, and maintains high accuracy. It must handle edge cases gracefully and integrate with downstream systems.

---

### Q1

Your invoice extraction tool's schema marks `purchase_order_number` as a required string. About 30% of invoices from small vendors don't print a PO number at all. Audits of those invoices find two kinds of output: plausible-looking PO numbers that don't exist in the ERP, and the invoice number copied into the PO field. What change best addresses the root cause?

A. Add a system prompt rule that PO numbers must be copied exactly as printed and never inferred.
B. Make `purchase_order_number` nullable, and state that null means the document shows none.
C. Add a regex `pattern` to the field so only strings in the company's PO number format are accepted.
D. Check each PO number against the ERP and retry the extraction with the lookup error when it fails.

### Q2

Downstream validation checks that extracted line items sum to the extracted invoice total. About 4% of extractions fail this check. On failure, the pipeline resends the identical request, and the second attempt passes only 10% of the time. Spot checks show the source documents do contain the correct values. What change should you make to the retry?

A. Retry up to five times and keep the first extraction that passes the sum check.
B. Switch to strict tool use so the schema itself guarantees line items match the total.
C. Drop the extracted total and compute the invoice total downstream from the extracted line items.
D. Resend the document with the failed extraction and the specific mismatch the validator found.

### Q3

Invoices, receipts, and purchase orders arrive in one mixed queue, and the document type isn't known in advance. You define three extraction tools, one per document type, and call the API with `tool_choice` set to `"auto"`. In 7% of requests the model replies with prose such as "This appears to be a receipt from…" and calls no tool, which breaks the downstream parser. What is the most reliable fix?

A. Set `tool_choice` to `"any"`, so the model must call one of the tools but chooses which.
B. Force `tool_choice` to the invoice tool, because invoices are the most common type in the queue.
C. Add a system prompt rule that every response must be a call to one of the extraction tools.
D. Add a fallback parser that maps the prose replies onto the downstream fields when no tool is called.

### Q4

Your extraction agent has an `extract_metadata` tool (document type, issuer, date, currency) and three enrichment tools: `lookup_vendor`, `convert_currency`, and `classify_expense`. The enrichment tools need the metadata as input. In 15% of runs, the model calls `lookup_vendor` first with a vendor name it guessed from the filename, and the enrichment results are wrong. Which change guarantees that metadata extraction happens first?

A. Force `extract_metadata` via `tool_choice` on the first request, then enrich in later turns.
B. Set `tool_choice` to `"any"` on the first request so the model must open with a tool call.
C. List `extract_metadata` first in the tools array so the model sees it before the enrichment tools.
D. State in the system prompt that `extract_metadata` must always be the first tool the agent calls.

### Q5

A nightly Message Batches job extracts key terms from 12,000 contracts. Last night 11,640 requests succeeded and 360 errored. Nearly all of the errored requests were contracts with long exhibits that exceeded the model's context window. What should you do next?

A. Resubmit all 12,000 contracts with a higher `max_tokens` so long contracts have room to finish.
B. Resubmit the 360 failed requests unchanged, because batch errors are usually transient.
C. Resubmit the 360 in a batch that gives the model a tool for loading long contracts section by section.
D. Resubmit only the 360 failed `custom_id`s, with each oversized contract split into chunks that fit.

### Q6

On a labeled validation set of 2,000 documents, overall field-level accuracy is 97%. Leadership proposes ending human review for every extraction whose model-reported confidence is 0.9 or higher. Which TWO steps should you take before reducing human review? **(Select TWO.)**

A. Expand the validation set to 10,000 documents so the 97% aggregate figure is more precise.
B. Add a second pass in which the model re-checks each high-confidence extraction before release.
C. Break accuracy down by document type and by field to find segments the aggregate is hiding.
D. Calibrate the 0.9 threshold on the labeled set so that confidence actually predicts accuracy.
E. Raise the threshold to 0.99 so that only the most certain extractions skip human review.

### Q7

You extract citation metadata from research papers. The instructions describe every field in detail. Papers with a numbered bibliography extract well. Papers that use inline author-year citations or footnote references return an empty `references` array, or DOIs that don't exist, in about 20% of cases. What is the most effective next step?

A. Expand the prose instructions to describe each citation style the system may encounter in detail.
B. Add a few examples of correct extraction from inline, footnote, and bibliography-style papers.
C. Require at least one item in `references` so that empty arrays fail schema validation and retry.
D. Route papers without a numbered bibliography to a separate pipeline that runs a larger model.

### Q8

Accounting rejects about 3% of extracted invoices because the line items don't add up to the total. Investigation shows half are extraction errors (a missed line item). The other half are invoices where the vendor's printed total is itself wrong. Accounting wants vendor errors flagged for follow-up, not silently corrected. Which schema change best supports this?

A. Have the model compute the total from the line items and output only that computed value.
B. Instruct the model to adjust line items so they always sum to the printed invoice total.
C. Extract both `stated_total` and `calculated_total`, plus a `conflict_detected` flag.
D. Use strict tool use so schema validation flags any extraction whose line items don't add up.

### Q9

Three months ago, after validating accuracy by document type and field, you stopped human review of extractions with calibrated confidence of 0.9 or higher. Reviewers now see only the low-confidence queue. Last week a large supplier switched to a new invoice layout. How should you keep measuring the error rate of auto-approved extractions, and catch new error patterns like this one?

A. Treat the error rate found in the low-confidence review queue as the error rate for the whole system.
B. Rely on downstream teams to report incorrect records, and investigate whenever complaints spike.
C. Send a stratified random sample of auto-approved extractions to human review on a regular schedule.
D. Have the model re-score its confidence on auto-approved extractions weekly and review any that drop.

### Q10

The schema's `document_category` field is an enum: `invoice`, `receipt`, `purchase_order`, `credit_note`. New document types keep arriving, such as pro forma invoices and account statements. Some documents are genuinely ambiguous, such as a paid invoice titled "Receipt". Downstream reports are corrupted because every document is forced into the closest category. Which TWO schema changes address this? **(Select TWO.)**

A. Replace the enum with a free-text string so the model can describe any document in its own words.
B. Add an `other` value paired with a `category_detail` string that describes what the document is.
C. Keep the enum as it is and add a system prompt rule telling the model to always pick the closest match.
D. Add every document type seen in the past year to the enum so that the list covers all known cases.
E. Add an `unclear` value for documents that fit more than one category, so they can be reviewed.
