---
name: cca-learn
description: Teach one Claude Certified Architect exam objective from official Anthropic documentation, framed the way the exam tests it, then check understanding with a few exam-style questions. Accepts a task statement (1.5, P3.8), a scenario, or a topic like tool_choice, path-scoped rules, fork_session, Message Batches, prompt caching, RAG chunking, or human-in-the-loop. Use whenever the user wants to learn, review, or understand a CCAR-F or CCAR-P topic, asks "explain X for the exam", or is confused about something they missed.
argument-hint: "<task id or topic> [socratic] [professional]"
allowed-tools:
  - Read
  - Bash(python3 ${CLAUDE_SKILL_DIR}/../../../scripts/cca.py *)
  - WebFetch(domain:code.claude.com)
  - WebFetch(domain:platform.claude.com)
  - WebFetch(domain:modelcontextprotocol.io)
  - WebFetch(domain:www.anthropic.com)
---

# Learn one exam objective

Study root: `${CLAUDE_SKILL_DIR}/../../..` (ROOT). Request: `$ARGUMENTS`

The goal is exam-ready understanding: the user can recognize the situation in a stem, pick the keyed answer, and say why the distractors fail. Official Anthropic sources are the authority (see the hierarchy in `ROOT/reference/official-sources.md`).

## 1. Pin down the objective

Map the request to one or two objective IDs using `ROOT/reference/foundations-blueprint.md` or `ROOT/reference/professional-blueprint.md`. If a topic spans several, teach the one carrying the most exam weight first and name the others. If the request is empty, ask what they want to learn, or run `python3 ${CLAUDE_SKILL_DIR}/../../../scripts/cca.py stats --exam F` and offer the weakest objective.

## 2. Gather sources

- The objective's entry in the blueprint. This is **what is tested**.
- Its rows in `ROOT/reference/official-sources.md`. Fetch the 1–3 most relevant official pages with WebFetch, using a focused prompt such as "Extract exactly how X works, defaults, and caveats". This is **how it works today**.
- `ROOT/reference/exam-vs-current-docs.md`, for any conflict on this topic.
- `ROOT/reference/answer-heuristics.md`, for the principles that decide items in this area.
- `ROOT/CLAUDE.local.md`, if present, for the learner's background.

Do not lean on third-party prep sites for facts. If a fetched doc contradicts the exam guide, teach both and say which to use on the exam. Then add the conflict to the drift log with its source.

## 3. Teach

Aim for 400–700 words unless the user asks for more. Use this shape:

1. **What the exam tests:** 1–2 sentences quoting or paraphrasing the blueprint objective.
2. **The core idea and why it's true.** Explain the mechanism, not just the rule. Rules without reasons don't transfer to new stems.
3. **A concrete example:** a minimal config, code, or prompt snippet from the official docs. Label it with the doc URL.
4. **Decision rules:** "When a stem shows X, prefer Y, because Z." Two to four of them.
5. **Traps:** the distractors this objective attracts, from the heuristics checklist.
6. **Exam vs today:** include only if there's drift.
7. **Your work:** one connection to the learner's real work, only if it genuinely fits. Skip it rather than force it.
8. **Sources:** the official URLs you actually used.

**Socratic mode** (if `socratic` is in the request): open with 2–3 probing questions, let the user reason, then fill gaps using the same structure.

## 4. Check understanding

Ask 2–3 exam-style questions on this objective, written to `ROOT/reference/question-writing.md`. Get key letters from:
```
python3 ${CLAUDE_SKILL_DIR}/../../../scripts/cca.py draw --exam F --quiz 3 --task 1.5
```
Use `--exam P` for Professional objectives, and leave out `--scenario` when logging them. Ask the items one at a time, give feedback in the standard format, and log each:
```
python3 ${CLAUDE_SKILL_DIR}/../../../scripts/cca.py log --exam F --source learn --task 1.5 --result correct --confidence medium
```
Include `--lesson "<rule>"` and `--doc <url>` on every miss.

## 5. Close

Give one line on how the check went and one next step. Pick a lab when hands-on practice would make the concept stick (`/cca-lab`), a review quiz if they missed, or the next objective in the plan.
