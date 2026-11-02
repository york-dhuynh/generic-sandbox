# Writing exam-style questions

Shared standard for `/cca-quiz`, `/cca-mock-exam`, and the checks in `/cca-learn`. Bad practice questions teach wrong lessons, so quality beats quantity.

## What a real item looks like

- **Foundations:** a scenario frame (one of S1–S6), then a stem describing a production situation. Stems usually include a symptom with numbers or logs ("in 12% of cases…", "logs show…", "latency +40%"), a constraint, and a question such as "most effective", "first step", "root cause", or "where should this file go".
- **Professional:** standalone items. Each stem carries its own context, often with business or governance constraints such as regulated data, SLAs, or a stakeholder objection.
- Mostly 4 options (A–D) with one key. About 10–15% are multiple-response with 5 options (A–E), stating "Select TWO".
- Options are parallel in length and style. The correct one is **not** the longest or most detailed by default.
- The cognitive level is applied judgment, not recall of trivia. "Which flag" recall is fine only when the flag is an explicit blueprint fact (e.g., `-p`, `--output-format json`, `--json-schema`).

## Authoring procedure

1. **Target.** Take the task ID (and scenario for Foundations) from `cca.py draw`. Read that task's entry in the blueprint. The item must test something listed there and nothing listed as out of scope.
2. **Key first.** Decide the correct answer and the principle it rests on (answer-heuristics.md). If the key depends on a product fact, it must be in the exam guide or confirmed in official docs. When unsure, fetch the doc page or choose a different angle. Never invent flags, fields, defaults, or numbers.
3. **Distractors.** Write 3 wrong options. Each must be plausible to someone with a specific misconception and wrong for a reason you can name in one sentence. Draw from the distractor checklist. At most one option may be "obviously silly", and ideally none are.
4. **Letter.** Place the key at the letter `cca.py draw` assigned. Models tend to put keys at A or B, and the drawn letter removes that bias.
5. **Drift check.** If the topic is in exam-vs-current-docs.md, key it per the exam guide and mention the drift in the rationale.
6. **Self-review before showing.**
   - Could a careful expert argue for a second option? If yes, sharpen the stem.
   - Is the key guessable from wording alone, such as the only option that echoes stem keywords or the longest option? If yes, rebalance.
   - Does the stem leak the answer? Answer the item yourself before showing it.
7. **Don't recycle** the 12 official Foundations samples or 3 Professional samples. The user can read those in the guide. New items may test the same principles in new situations.
   Some objectives sit close to a sample: 1.4 (F-Q1), 2.1 (F-Q2), 5.2 (F-Q3), 3.2 (F-Q4), 3.4 (F-Q5), 3.3 (F-Q6), 1.2 (F-Q7), 5.3 (F-Q8), 2.3 (F-Q9), 3.6 (F-Q10), 4.5 (F-Q11), 1.6/4.6 (F-Q12), P3.1 (P-S1), P2.5 (P-S2), P4.4 (P-S3). For these, change the angle rather than reskinning:
   - test the boundary with a neighboring objective (P3.1 capability bloat vs P3.8 tool search)
   - flip the conditions so the sample's answer becomes wrong
   - combine two findings that only one option fixes
   - ask about the second step after the sample's first step

## Feedback format (after the user answers)

```
✅ Correct / ❌ Incorrect. Key: C   (Task 1.5 · Scenario S1)

Why C: <the principle in 1–2 sentences, tied to the stem's specific evidence>
Why not A: <named misconception>
Why not B: …
Why not D: …
Rule to remember: <one line, reusable>
Official source: <one URL from official-sources.md>
[Drift note: … only if relevant]
```

Keep feedback tight. If the user was wrong with high confidence, add one sentence naming the misconception directly. Confident misses are the most valuable thing to fix.
