# Making accurate practice exams: the evidence

Research done 2026-10-28 on how accurate LLM-written practice exams can be, and how to make them more so. The evidence is mostly psychometrics and medical education. Numbers marked ✔ were re-checked against the paper's abstract (Europe PMC); the rest come from the research agent's reading of abstracts and index pages. Preprints are marked.

## What "accurate" means, and where an LLM falls short

| Kind of accuracy | Achievable? | Evidence |
|---|---|---|
| **Blueprint fidelity**: domains, scenarios, format | Yes. It's bookkeeping, and `cca.py draw --mock` already does it | – |
| **Correct keys and no flaws** | Only with independent verification. Raw LLM items fail often | GPT-3.5 items written from supplied text: only 32% fully correct ✔ ([Ngo 2024](https://pubmed.ncbi.nlm.nih.gov/38162414/)). LLM quizzes: 49% had item-writing flaws and 22% had factual or conceptual errors, but 91% were a usable draft ✔ ([Camarata 2025](https://pubmed.ncbi.nlm.nih.gov/40516963/)). Faulty items appeared in all 8 studies of a systematic review ([Artsi 2024](https://doi.org/10.1186/s12909-024-05239-y)) |
| **Realistic difficulty** | Unknown, and probably too easy | GPT-4o items were easier than human items, difficulty .78 vs .69 ✔. They also discriminated less and skewed toward lower-order thinking ([Law 2025](https://pubmed.ncbi.nlm.nih.gov/39923067/)). Reviewed GPT-4o items matched human items, difficulty .67 vs .65 ✔ ([Linde 2026](https://pubmed.ncbi.nlm.nih.gov/41507355/)) |
| **A score that predicts the real exam** | No | No mapping exists from practice percent to the 720 scaled score. Even an official self-assessment explains only ~67% of score variance ([USMLE example](https://pubmed.ncbi.nlm.nih.gov/20881715/)). One 60-item mock at 72% has a 95% interval of about ±11 points; three fresh mocks narrow it to about ±6.6 |

## Findings that shape the design

**Item writing.**
- The NBME's "testwiseness" flaws inflate or distort scores ([NBME guide](https://health.uconn.edu/faculty-development/wp-content/uploads/sites/69/2017/06/constructing_written_test_questions.pdf); [Rush 2016](https://pubmed.ncbi.nlm.nih.gov/27681933/); [Harasym 1998](https://pubmed.ncbi.nlm.nih.gov/10183336/)):
  - the key is the longest or most complete option
  - the stem and the key share a word
  - absolutes ("always", "never")
  - convergence
  - "all of the above"
- **Cover-the-options rule:** a good scenario item can be answered from the stem alone.
- Four-option items rarely have three working distractors: only 13.8% did ([Tarrant 2009](https://doi.org/10.1186/1472-6920-9-40)). Keep 4 options to match the real exam, but expect the third distractor to be weak.
- Item writers favor middle key positions by up to 3–4 to 1 ([Attali & Bar-Hillel 2003](https://doi.org/10.1111/j.1745-3984.2003.tb01099.x)). The script, not the writer, should assign key letters. The kit already does this.

**Checking.**
- **Rule-based flaw detection** caught 91% of human-identified flaws, versus 79% for GPT-4 (preprint) ([Moore 2023](https://arxiv.org/abs/2307.08161)). Write the rules as code first.
- **A model grading its own work is biased:** LLMs recognize and favor their own outputs ([Panickssery 2024](https://arxiv.org/abs/2404.13076)). Have separate solver runs that don't see the key.
- **Shortcuts:** models can often pick the key from the options alone ([Balepur 2024](https://aclanthology.org/2024.acl-long.555/)), and they're biased toward certain option letters ([Zheng 2024](https://arxiv.org/abs/2309.03882)).
  - Probe each item with the options only and with the stem only.
  - Solve it under every rotation of the options.
- **Even curated human benchmarks contain errors:** about 6.5% in MMLU ([Gema 2025](https://aclanthology.org/2025.naacl-long.262/)). Human review still mattered in every study found. None showed it could be dropped.

**Difficulty.**
- Predicting difficulty from item text barely beats guessing the average. The best entry in the BEA 2024 shared task scored an RMSE of .299 against a .311 baseline ([BEA 2024](https://aclanthology.org/2024.bea-1.39/)).
- LLMs as simulated test-takers correlate weakly with humans ([BEA 2025](https://arxiv.org/abs/2506.09796)).
- With a single learner you can estimate *your* ability, with a confidence interval, but not each item's difficulty.

**Forms and reuse.**
- Retaking an identical form after studying its rationales inflates the score: practice effect d ≈ .26, larger with coaching ([Hausknecht 2007](https://pubmed.ncbi.nlm.nih.gov/17371085/)). Only unseen items should count toward readiness.

## The pipeline this points to

1. **Generate from item models.** For each task × scenario:
   - a "most effective fix" style lead-in
   - typed distractors: partial fix, right fix at the wrong layer, outdated, over-engineered
   - verbatim quotes from a dated snapshot of the official docs, supporting the key and refuting each distractor
   - the 12 official samples as style examples only
2. **Run deterministic flaw checks:**
   - each quote exists in the snapshot
   - the key isn't a length outlier
   - no word is shared by the stem and the key only
   - no absolutes, no "all/none of the above", no negative stems
   - no convergence
   - no near-duplicates of other bank items or the official samples
3. **Verify independently:**
   - Solver runs that don't see the key answer under every option rotation. Keep an item only if every run picks the key.
   - Ask whether any second option is defensible.
   - Run the options-only and stem-only probes.
   - Anything that fails goes to quarantine.
4. **Human review:** every quarantined item, plus a 10% random audit. Check the facts (do the quotes support the key and refute the distractors?), not the style.
   - The reviewer shouldn't be the learner. Otherwise review only items you've already taken.
5. **Assemble forms:**
   - 4 scenarios × 15 items, domain weights ±1
   - each key letter 12–18 times, with no run longer than 3
   - one item per enemy cluster
   - scored mocks use unseen items only
   - the 12 official items stay a one-time anchor set
6. **Analyze each mock:**
   - a binomial confidence interval on the score
   - domain tallies pooled across mocks
   - every high-confidence miss gets a key challenge
   - **readiness:** the lower 95% bound across at least 3 fresh forms is above your target

## Calibration against the official samples (2026-10-28)

The bank's difficulty probes were run on the 12 official sample items, with 2 runs each:

| Probe | Official samples |
|---|---|
| Weak model (Claude Haiku 5.5, low effort, closed book) | 24/24 right |
| Options only, stem hidden (Claude Sonnet 5.5) | 24/24 right |

Two conclusions:
1. The weak-model probe can't tell items apart, so `bank.py` records it but doesn't use it.
2. Options-only guessability is the difficulty signal. The bank's first dev items ranged from 0/2 to 2/2 on it, so some are already harder than the official samples by this measure.

Two caveats: the samples are public and may be in the models' training data, and LLM-based difficulty correlates only weakly with how hard humans find an item. The signal can flag give-away items. It can't predict your score.

## Risk that's left over

- **Shared blind spots:** the writer and every solver can misread the docs the same way. This risk is higher when they're all Claude, because the research suggests at least one solver from outside the Claude family.
- **The docs change** between snapshots.
- **Difficulty stays unvalidated,** and LLM items skew easy, so mock scores probably overstate readiness.
- **Items can drift** toward doc trivia instead of judgment.

## Couldn't verify

- Rodriguez's (2005) effect sizes (its conclusion, that 3 options are optimal, is solid).
- The size of the identical-form effect in Hausknecht.
- Any controlled study of grounded vs. ungrounded generation, or of multi-model agreement, on key accuracy.
- Direct evidence that LLM items overuse "longest option is the key".
- Any published mapping from practice scores to Claude Certified Architect scaled scores.

Most evidence on LLM items comes from small medical-education studies with older models.
