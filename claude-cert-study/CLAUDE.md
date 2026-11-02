# Claude Certified Architect study workspace

This folder is a study kit for **Claude Certified Architect – Foundations (CCAR-F)**, then **Professional (CCAR-P)**. Sessions here are study sessions: teach, quiz, coach, and review labs.

## Source policy

Official Anthropic material outranks everything else. The full hierarchy and verified links are in `reference/official-sources.md`. Read it when you need a source. It is deliberately not imported, so it doesn't load into every session. In short:

1. **The official exam guides** decide what is tested and how answers are keyed. They are condensed in `reference/foundations-blueprint.md` and `reference/professional-blueprint.md`.
2. **Official docs** decide how things work today: code.claude.com, platform.claude.com, modelcontextprotocol.io.
3. Anthropic engineering articles, Anthropic Academy, and the `anthropics` GitHub repos.
4. Third-party prep sites, such as claudecertificationguide.com, are for extra practice only and never count as evidence.

When the exam guide and current docs disagree, teach both. Answer exam items per the guide, and record the conflict in `reference/exam-vs-current-docs.md` with an official source.

Never invent product facts: flags, fields, defaults, limits, or tool names. If you're unsure, fetch the official page or use `/cca-verify`. A wrong "fact" in a study session is worse than "let me check".

## Skills

| Command | Use |
|---|---|
| `/cca-test [S#] [n] \| retake [S#\|session] \| results …` | Browser practice test from the verified bank, or a retake of one already taken. The page copies a `/cca-test results` line back for grading and debrief |
| `/cca-day [minutes] [plan\|questions]` | The daily rotation: time-boxed deep dive, spoiler-free overview of the next scenario, interleaved quick review; tracks open questions |
| `/cca-scenario [S1–S6\|next\|status] [fresh]` | Depth-first scenario study from `scenarios/`: exam block, score, reverse-engineer misses, transfer check |
| `/cca-coach` | Dashboard, study plan, readiness, outside scores, switching to Professional |
| `/cca-learn <objective or topic>` | Teach one objective from official docs, then check it |
| `/cca-quiz [mode] [n]` | Exam-style items with rationale; adaptive, diagnostic, review, or filtered |
| `/cca-mock-exam [foundations\|professional]` | Full timed mock with a report (manual trigger only) |
| `/cca-lab [id] [start\|hint\|review]` | Hands-on labs F1–F5 and P1–P6 |
| `/cca-verify <claim>` | Fact-check a claim against official docs in an isolated subagent |

## Conventions
- Log every answered practice item through `scripts/cca.py log`, so the dashboard and adaptive draws stay accurate.
- Never read `progress/bank/keys.json` or run `scripts/bank.py inspect` on an unseen item. The user will take those questions. `bank.py show` and `review` (after grading) are the safe ways in.
- End every study sitting with a journal entry (`scripts/cca.py journal add --kind session --minutes N --text "…"`), then refresh the dashboard (`scripts/cca.py dashboard`).
- Keep study replies tight. One question at a time. Give feedback with reasons, not just verdicts.
- Learner context, if any, is in `CLAUDE.local.md`. It is personal and not committed.
