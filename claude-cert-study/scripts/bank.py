#!/usr/bin/env python3
"""Question bank for CCAR-F practice: generate verified items with Claude, then build, give, and grade forms.

Standard library only. Claude runs through the Claude Code CLI in headless mode (`claude -p`) on your normal
login, in an empty temp folder with every tool turned off. Generation never prints item text, so unseen
items stay unseen. The method and its evidence are in reference/practice-exam-research.md.

  bank.py snapshot [--tasks 1.4,1.5 | --scenario S1]     save the official doc pages items must quote
  bank.py generate --scenario S1 --n 10 [--difficulty hard|standard] [--workers 3] [--harden] [--dev]
  bank.py status
  bank.py repair                                          retry quarantined items flagged only as ambiguous
  bank.py form --block S1 [--n 15] | --mock               a form of verified items you haven't seen
  bank.py show SESSION N                                  one item, no key
  bank.py answer SESSION N LETTERS [--conf high|medium|low] [--flag]
  bank.py grade SESSION                                   score + interval, log it, mark items seen
  bank.py review SESSION [--n N]                          after grading: keys, reasons, doc quotes
  bank.py review --quarantine                             items the checkers disagreed on (never scored)
  bank.py dispute ID --note "..."  /  bank.py resolve ID keep|retire [--note "..."]
  bank.py history                                         every graded form with its 95% interval
  bank.py inspect ID                                      full item with key (dev items only, or after use)

Pipeline per item: plan (objective, key letter) → write (Opus, quotes from the doc snapshot) → rule checks
(quote exists, no length or wording cues, no near-duplicates; one rewrite allowed) → blind solving (Opus
and Sonnet, open-book, every option rotation; all runs must pick the key) → options-only probe under every
rotation (difficulty signal; the official samples all score easy) → with --harden, one rewrite when easy, kept
only if it passes everything again → verified or quarantined.

Files in progress/bank/: items.json (stems, options, status), keys.json (answers), forms/<session>.json,
docs/ (snapshot + manifest.json), runs.jsonl (one line per Claude call with its cost). Set CLAUDE_BIN if
the claude binary isn't on PATH.
"""
import argparse
import concurrent.futures as cf
import datetime as dt
import glob
import html
import json
import math
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cca  # noqa: E402

ROOT = cca.ROOT
BANK = ROOT / "progress" / "bank"
ITEMS = BANK / "items.json"
KEYS = BANK / "keys.json"
FORMS = BANK / "forms"
DOCS = BANK / "docs"
RUNS = BANK / "runs.jsonl"
REF = ROOT / "reference"

WRITER = ("claude-opus-5-5", "high")
SOLVERS = [("claude-opus-5-5", "medium"), ("claude-sonnet-5-5", "medium")]
PROBE = ("claude-sonnet-5-5", "low")          # options-only probe
WEAK = ("claude-haiku-5-5", "low")            # closed-book weak examinee
DOC_BUDGET = 400_000                          # characters of docs per task, whole pages only
LOCK = threading.Lock()


def die(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(2)


def load_json(path, default):
    return json.loads(path.read_text()) if path.exists() else default


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")
    tmp.replace(path)


def stamp():
    return dt.datetime.now().strftime("%Y%m%d-%H%M")


def wilson(c, n, z=1.96):
    if not n:
        return 0.0, 0.0
    p = c / n
    d = 1 + z * z / n
    mid = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, mid - half), min(1.0, mid + half)


# ---------------------------------------------------------------- reference material

def scenario_frame(s):
    lines = (ROOT / "scenarios" / cca.FOLDERS[s] / "exam.md").read_text().splitlines()
    k = lines.index("## Scenario") + 1
    out = []
    for line in lines[k:]:
        if line.strip() == "---":
            break
        out.append(line)
    return "\n".join(out).strip()


def task_title(task):
    m = re.search(rf"^\*\*{re.escape(task)} ([^*]+)\*\*", (REF / "foundations-blueprint.md").read_text(), re.M)
    return m.group(1).strip() if m else ""


def official_samples():
    out = []
    for f in sorted((ROOT / "scenarios").glob("S*/exam.md")):
        text = f.read_text()
        if "## Official sample questions" in text:
            part = text.split("## Official sample questions", 1)[1]
            part = part.split("\n", 1)[1]  # drop the heading's remainder line
            out.append(f"Scenario {f.parent.name[:2]}:\n{part.strip()}")
    return "\n\n".join(out)


def task_urls(task):
    for line in (REF / "official-sources.md").read_text().splitlines():
        if line.startswith(f"| {task} "):
            return re.findall(r"\((https?://[^)\s]+)\)", line)
    return []


def slug(url):
    return re.sub(r"[^a-z0-9]+", "_", re.sub(r"^https?://", "", url).lower()).strip("_")


def strip_html(text):
    text = re.sub(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    return re.sub(r"[ \t]+", " ", html.unescape(text))


def fetch(url):
    md = any(h in url for h in ("code.claude.com/", "platform.claude.com/", "modelcontextprotocol.io/"))
    target = url if url.endswith(".md") or not md else url + ".md"
    req = urllib.request.Request(target, headers={"User-Agent": "cca-study-kit/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        text = r.read().decode("utf-8", "replace")
    if text.lstrip().lower().startswith(("<!doctype", "<html")):
        text = strip_html(text)
    if "page not found" in text[:800].lower():
        raise ValueError("page not found")
    return text


def cmd_snapshot(a):
    tasks = (a.tasks.split(",") if a.tasks else
             [t for t, s in cca.F_AFFINITY.items() if not a.scenario or a.scenario in s])
    manifest = load_json(DOCS / "manifest.json", {})
    urls = sorted({u for t in tasks for u in task_urls(t)})
    ok = fail = 0
    for u in urls:
        try:
            text = fetch(u)
        except Exception as e:  # network or missing page: report and continue
            print(f"  failed {u}: {e}")
            fail += 1
            continue
        DOCS.mkdir(parents=True, exist_ok=True)
        (DOCS / f"{slug(u)}.md").write_text(text)
        manifest[slug(u)] = {"url": u, "fetched": dt.date.today().isoformat(), "chars": len(text)}
        ok += 1
    save_json(DOCS / "manifest.json", manifest)
    print(f"snapshot: {ok} pages saved, {fail} failed, for {len(tasks)} objectives → {DOCS}")


def task_docs(task):
    """(name, text) pairs for a task: the exam guide, the drift table, then its official pages within budget."""
    out = [("exam-guide", (REF / "foundations-blueprint.md").read_text()),
           ("drift-table", (REF / "exam-vs-current-docs.md").read_text())]
    used = 0
    for u in task_urls(task):
        f = DOCS / f"{slug(u)}.md"
        if not f.exists():
            continue
        text = f.read_text()
        if used and used + len(text) > DOC_BUDGET:
            continue
        out.append((slug(u), text))
        used += len(text)
    return out


# ---------------------------------------------------------------- calling Claude

def claude_bin():
    found = os.environ.get("CLAUDE_BIN") or shutil.which("claude")
    if found:
        return found
    cands = sorted(glob.glob(os.path.expanduser(
        "~/.vscode/extensions/anthropic.claude-code-*/resources/native-binary/claude")))
    if cands:
        return cands[-1]
    die("claude CLI not found; set CLAUDE_BIN to its path")


def call_claude(purpose, item_id, model, effort, prompt, schema, system_file=None, system_text=None, timeout=900):
    cmd = [claude_bin(), "-p", "--model", model, "--effort", effort, "--tools", "", "--no-session-persistence",
           "--output-format", "json", "--json-schema", json.dumps(schema)]
    cmd += ["--system-prompt-file", str(system_file)] if system_file else ["--system-prompt", system_text or ""]
    cmd.append(prompt)
    t0 = time.time()
    out, cost, ok, err = None, 0.0, False, None
    with tempfile.TemporaryDirectory() as cwd:
        for attempt in range(3):
            if attempt:
                time.sleep((20, 60)[attempt - 1])  # back off: failures here are usually rate or usage limits
            try:
                p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
                d = json.loads(p.stdout)
                cost += d.get("total_cost_usd") or 0.0
                if not d.get("is_error") and isinstance(d.get("structured_output"), dict):
                    out, ok, err = d["structured_output"], True, None
                    break
                err = f"{d.get('subtype')} {d.get('api_error_status') or ''} {str(d.get('result') or '')[:160]}".strip()
            except subprocess.TimeoutExpired:
                err = "timeout"
            except json.JSONDecodeError:
                err = ((p.stdout or "") + (p.stderr or "")).strip()[:200] or "no output"
    with LOCK:
        RUNS.parent.mkdir(parents=True, exist_ok=True)
        with RUNS.open("a") as f:
            f.write(json.dumps({"ts": cca.now(), "purpose": purpose, "item": item_id, "model": model,
                                "effort": effort, "ok": ok, "cost_usd": round(cost, 5),
                                "seconds": round(time.time() - t0, 1), **({"error": err} if err else {})}) + "\n")
    return out, cost


# ---------------------------------------------------------------- writing

HARD = """Write it hard. The exam rewards judgment between options that all sound reasonable.
- Every distractor is a fix a competent engineer might really propose: a real mechanism that works in another
  situation, fixes a different symptom, fixes the right thing at the wrong layer, is out of date per the exam
  guide, or over-engineers. At most one distractor may be weak, and none may be silly.
- Put one decisive detail in the stem (a number, a log line, a constraint) that rules out the most tempting
  distractor. Without that detail, two options would be defensible.
- Make the candidate combine two facts: the scenario's constraint and the stem's evidence.
- Test judgment, not recall. Ask for a root cause from evidence, the most effective fix under a constraint, the
  second step after an obvious first step, or the right place for something.
- Beat the slogans. A candidate who only knows the guide's one-liners ("hooks beat prompts", "the coordinator owns
  errors", "fix the descriptions first") should be pulled toward a distractor that fits the slogan but misses this
  situation's detail.
- Bury the decisive detail mid-stem among other realistic facts, and add one red herring that makes a distractor
  look right. Never put the decisive detail in the last sentence, and never quote the faulty config or prompt in
  a way that names the bug.
- Paraphrase the guide. No option may restate a guide sentence nearly word for word.
"""
STANDARD = "Write it at the level of the official samples: one clear principle decides it.\n"

RULES = """Rules every item follows:
- The stem is answerable before the options are read: a closed, focused lead-in at the end.
- Options are parallel in grammar and length. The correct option is not the longest or most detailed.
- No word from the stem appears only in the correct option.
- No "all of the above", "none of the above", negative stems (NOT, EXCEPT), or absolutes (always, never).
- Key every item per the exam guide. Where the guide and current docs differ (drift table), the guide wins;
  say so in the explanation.
- Evidence: quote verbatim, character for character, from the documents provided, naming the document by its
  name attribute. At least one quote must support the correct answer. Add quotes that rule out distractors
  where the documents allow. Quote prose, not code blocks, 25–300 characters each.
- Don't reuse the official samples; test their principles in new situations if at all.
"""

ITEM_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["stem", "options", "key", "question_type", "rule", "why", "evidence", "hardness_note"],
    "properties": {
        "stem": {"type": "string"},
        "options": {"type": "object", "additionalProperties": False, "required": ["A", "B", "C", "D"],
                    "properties": {k: {"type": "string"} for k in "ABCDE"}},
        "key": {"type": "array", "items": {"type": "string", "enum": list("ABCDE")}},
        "question_type": {"type": "string", "enum": ["root cause", "first step", "most effective", "most reliable",
                                                      "where it goes", "which design", "select two"]},
        "rule": {"type": "string"},
        "why": {"type": "object", "additionalProperties": False, "required": ["A", "B", "C", "D"],
                "properties": {k: {"type": "string"} for k in "ABCDE"}},
        "evidence": {"type": "array", "items": {
            "type": "object", "additionalProperties": False, "required": ["option", "role", "doc", "quote"],
            "properties": {"option": {"type": "string", "enum": list("ABCDE")},
                           "role": {"type": "string", "enum": ["supports key", "rules out distractor"]},
                           "doc": {"type": "string"}, "quote": {"type": "string"}}}},
        "hardness_note": {"type": "string"},
    },
}

SOLVE_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["answer", "confidence", "also_defensible"],
    "properties": {
        "answer": {"type": "array", "items": {"type": "string", "enum": list("ABCDE")}},
        "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
        "also_defensible": {"type": "string", "enum": list("ABCDE") + ["none"]},
    },
}


def docs_block(docs):
    return "\n".join(f'<doc name="{n}">\n{t}\n</doc>' for n, t in docs)


def system_files(task, difficulty, tmp):
    docs = task_docs(task)
    common = f"<documents>\n{docs_block(docs)}\n</documents>\n"
    writer = tmp / f"writer-{task}-{difficulty}.txt"
    writer.write_text(
        "You write practice items for the Claude Certified Architect – Foundations exam (CCAR-F). Items must be "
        "accurate to the exam guide and Anthropic's official docs, and must read like the real exam.\n\n"
        f"<item_writing_standard>\n{(REF / 'question-writing.md').read_text()}\n</item_writing_standard>\n"
        f"<keying_principles>\n{(REF / 'answer-heuristics.md').read_text()}\n</keying_principles>\n"
        f"<official_samples_for_style_only>\n{official_samples()}\n</official_samples_for_style_only>\n"
        f"<difficulty>\n{HARD if difficulty == 'hard' else STANDARD}</difficulty>\n<rules>\n{RULES}</rules>\n"
        + common)
    return writer, {n: t for n, t in docs}


SOLVER_INTRO = ("You are an expert checking a practice item for the Claude Certified Architect – Foundations exam. "
                "Answer it as the exam would key it: per the exam guide, using the official docs provided. Choose "
                "the single best option (two if the stem says Select TWO). Then say whether any other option is "
                "also defensible as correct; answer none unless an expert could seriously argue for it.\n\n")


def solver_file(item, docs, tmp, iid):
    """Open-book context for blind solvers: the exam guide, the drift table, and the whole pages the item cites."""
    names = ["exam-guide", "drift-table"] + sorted({e["doc"] for e in item["evidence"]} - {"exam-guide", "drift-table"})
    f = tmp / f"solver-{iid}.txt"
    f.write_text(SOLVER_INTRO + f"<documents>\n{docs_block([(n, docs[n]) for n in names if n in docs])}\n</documents>\n")
    return f


def norm(s):
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
    for a, b in (("’", "'"), ("‘", "'"), ("“", '"'), ("”", '"'), ("–", "-"), ("—", "-"), (" ", " ")):
        s = s.replace(a, b)
    s = re.sub(r"[`*_>#|]", "", s)
    return re.sub(r"\s+", " ", s).strip().lower()


def quote_found(quote, doc_text):
    parts = [p for p in re.split(r"\.\.\.|…", norm(quote)) if p.strip()]
    hay = norm(doc_text)
    pos = 0
    for p in parts:
        i = hay.find(p.strip(), pos)
        if i < 0:
            return False
        pos = i + len(p.strip())
    return bool(parts)


STOP = set("about after again against their there these those which while would could should other another "
           "being where every using within without before because through during agent agents claude model "
           "tool tools option options".split())


def words(s):
    return {w for w in re.findall(r"[a-z][a-z_]{4,}", s.lower()) if w not in STOP}


def grams(s, n=3):
    w = re.findall(r"[a-z0-9_]+", s.lower())
    return {tuple(w[i:i + n]) for i in range(len(w) - n + 1)}


def jaccard(a, b):
    return len(a & b) / len(a | b) if a and b else 0.0


def rule_checks(item, plan, docs, others):
    """Return (failures, warnings) for a written item."""
    fail, warn = [], []
    letters = list("ABCDE") if plan["type"] == "multi" else list("ABCD")
    opts = {k: v for k, v in item["options"].items() if v and v.strip()}
    if sorted(opts) != letters:
        fail.append(f"needs options {''.join(letters)} exactly")
    if sorted(item["key"]) != sorted(plan["key"]):
        fail.append(f"key must be {'+'.join(plan['key'])}")
    if plan["type"] == "multi" and "select two" not in item["stem"].lower():
        fail.append('a multi item must say "Select TWO"')
    sup = [e for e in item["evidence"] if e["role"] == "supports key" and e["option"] in plan["key"]]
    bad = [e for e in item["evidence"] if e["doc"] not in docs or len(e["quote"]) < 25
           or not quote_found(e["quote"], docs[e["doc"]])]
    if not sup or any(e in bad for e in sup):
        fail.append("needs a verbatim quote (25+ chars) from a provided document supporting the key")
    if bad:
        fail.append(f"{len(bad)} quote(s) not found verbatim in the named document")
    text = " ".join(opts.values()).lower()
    if re.search(r"\b(all|none) of the above\b", text):
        fail.append('no "all/none of the above"')
    if re.search(r"\b(NOT|EXCEPT|LEAST)\b", item["stem"]):
        fail.append("no negative stems")
    if re.search(r"\b(always|never)\b", text):
        warn.append("absolute term in an option")
    keys = [k for k in plan["key"] if k in opts]
    lens = {k: len(v) for k, v in opts.items()}
    dist = [lens[k] for k in opts if k not in keys]
    if keys and dist:
        if plan["type"] == "single":
            k = keys[0]
            if lens[k] > max(dist) and lens[k] > 1.15 * (sum(dist) / len(dist)):
                fail.append("the key is the longest option by a clear margin")
        elif sorted(lens, key=lens.get)[-2:] == sorted(keys, key=lens.get):
            fail.append("the two keys are the two longest options")
        stem_w = words(item["stem"])
        dist_w = set().union(*(words(opts[k]) for k in opts if k not in keys))
        echo = (stem_w & set().union(*(words(opts[k]) for k in keys))) - dist_w
        if len(echo) >= 2:
            fail.append(f"stem words appear only in the key: {', '.join(sorted(echo)[:4])}")
    g = grams(item["stem"])
    if any(jaccard(g, o) >= 0.5 for o in others):
        fail.append("near-duplicate of an existing bank item or official sample")
    return fail, warn


# ---------------------------------------------------------------- verifying

def rotated(item, rot, letters):
    """Options re-lettered by a cyclic rotation; returns (text, map shown->original)."""
    n = len(letters)
    back = {letters[i]: letters[(i + rot) % n] for i in range(n)}
    lines = [f"{s}. {item['options'][back[s]]}" for s in letters]
    return "\n".join(lines), back


def verify(item, plan, sfile, pool):
    letters = list("ABCDE") if plan["type"] == "multi" else list("ABCD")
    frame = scenario_frame(plan["scenario"])
    key = sorted(plan["key"])
    jobs = []
    for rot_range in (range(1), range(1, len(letters))):  # rotation 0 first, so the rest read a warm cache
        batch = []
        for model, effort in SOLVERS:
            for rot in rot_range:
                opts, back = rotated(item, rot, letters)
                prompt = f"Scenario:\n{frame}\n\nQuestion:\n{item['stem']}\n\n{opts}"
                batch.append(("solve", model, back, pool.submit(call_claude, "solve", plan["id"], model, effort,
                                                                prompt, SOLVE_SCHEMA, system_file=sfile)))
        if rot_range.start == 0:
            cf.wait([b[3] for b in batch])
        jobs += batch
    for rot in range(len(letters)):
        opts, back = rotated(item, rot, letters)
        jobs.append(("options-only", PROBE[0], back, pool.submit(
            call_claude, "options-only", plan["id"], *PROBE,
            "The question stem is hidden. From the options alone, which is most likely the correct answer to a "
            f"Claude Certified Architect exam item?\n\n{opts}", SOLVE_SCHEMA,
            system_text="You are taking a multiple-choice test. Answer even when unsure.")))
    for rot in range(2):
        opts, back = rotated(item, rot * 2 + 1, letters)
        jobs.append(("weak", WEAK[0], back, pool.submit(
            call_claude, "weak", plan["id"], *WEAK, f"Scenario:\n{frame}\n\nQuestion:\n{item['stem']}\n\n{opts}",
            SOLVE_SCHEMA, system_text="You are a candidate taking the Claude Certified Architect – Foundations "
                                      "exam. Pick the best answer (two if the stem says Select TWO).")))
    res = {"solve": [], "options-only": [], "weak": []}
    cost = 0.0
    picks, second = Counter(), Counter()
    for kind, model, back, fut in jobs:
        out, c = fut.result()
        cost += c
        if not out:
            res[kind].append(None)
            continue
        ans = sorted(back.get(x, x) for x in out["answer"])
        res[kind].append(ans == key)
        if kind == "solve":
            if ans != key:
                picks["+".join(ans)] += 1
            if out["also_defensible"] != "none":
                second[back.get(out["also_defensible"], out["also_defensible"])] += 1
    solved = [r for r in res["solve"] if r is not None]
    summary = {"runs": len(res["solve"]), "agree": sum(bool(r) for r in solved), "failed_calls":
               res["solve"].count(None), "other_picks": dict(picks), "second_defensible": dict(second),
               "options_only": f"{sum(bool(r) for r in res['options-only'])}/{len(res['options-only'])}",
               "weak": f"{sum(bool(r) for r in res['weak'])}/{len(res['weak'])}"}
    contested = [k for k, v in second.items() if v >= 2 and k not in key]
    ok = solved and len(solved) == summary["runs"] and all(solved) and not contested
    # Difficulty signal = how often the key is picked from the options alone (stem hidden), across every
    # rotation. The 12 official samples score 100% here; the weak model solved them all too, so it's recorded
    # but not used. "medium"/"hard" therefore mean harder than the official samples on this one measure.
    oo = [bool(r) for r in res["options-only"] if r is not None]
    share = sum(oo) / len(oo) if oo else 1.0
    signal = "easy" if share >= 0.75 else "medium" if share > 0 else "hard"
    reason = None if ok else ("solver disagreement" if picks else
                              f"second option defensible: {', '.join(contested)}" if contested else "solver calls failed")
    return ok, reason, summary, signal, cost


# ---------------------------------------------------------------- generate

def plan_items(scenario, n, rng):
    rows = cca.load("F")
    pool = [t for t, s in cca.F_AFFINITY.items() if scenario in s]
    ms = cca.mastery(rows, "F")
    weights = []
    for t in pool:
        c, k = ms[t]
        weights.append(cca.EXAMS["F"]["domains"][cca.domain_of(t)][1] * ((1 - (c + 1) / (k + 2)) + 0.15))
    tasks = []
    while len(tasks) < n:
        tasks += cca.weighted_pick(rng, pool, weights, n - len(tasks))
    singles = (list("ABCD") * (n // 4 + 1))
    rng.shuffle(singles)
    plans = []
    for t in tasks:
        if rng.random() < cca.MULTI_RATE:
            plans.append({"task": t, "type": "multi", "key": sorted(rng.sample("ABCDE", 2))})
        else:
            plans.append({"task": t, "type": "single", "key": [singles.pop()]})
    for p in plans:
        p["scenario"] = scenario
    return plans


def write_item(plan, writer_file, docs, others, difficulty, existing_stems):
    fmt = ("5 options, A–E, exactly two correct; the stem ends with \"Select TWO.\"" if plan["type"] == "multi"
           else "4 options, A–D, exactly one correct")
    keytxt = " and ".join(plan["key"])
    base = (f"Write one exam item.\n\nTask statement {plan['task']}: {task_title(plan['task'])} (see its entry in "
            f"the exam guide).\nScenario {plan['scenario']}:\n{scenario_frame(plan['scenario'])}\n\n"
            f"Format: {fmt}.\nThe correct answer must be option{'s' if len(plan['key']) > 1 else ''} {keytxt}; "
            f"write the others as distractors.\nDifficulty: {difficulty}.\nThe stem must not repeat the scenario "
            "text; the scenario is shown above it on the exam.\n")
    if existing_stems:
        base += "\nDon't overlap these existing items for this task and scenario:\n" + \
                "\n".join(f"- {s}" for s in existing_stems[:12]) + "\n"
    cost, item, fails, warns = 0.0, None, [], []
    prompt = base
    for attempt in range(2):
        item, c = call_claude("write", plan["id"], *WRITER, prompt, ITEM_SCHEMA, system_file=writer_file)
        cost += c
        if not item:
            fails = ["writer call failed"]
            continue
        fails, warns = rule_checks(item, plan, docs, others)
        if not fails:
            break
        prompt = base + "\nYour previous draft failed these checks; write a new item that passes them:\n" + \
            "\n".join(f"- {f}" for f in fails) + "\n"
    return item, fails, warns, cost, attempt + 1


def harden(item, plan, writer_file, docs, others, summary, tmp, pool):
    """One rewrite aimed at difficulty. Returns ((item, (summary, signal)) or None, cost, note)."""
    prompt = (
        "This verified practice item gives itself away: a model that saw only the options, with the stem hidden, "
        f"picked the key in {summary['options_only']} runs. Make the options stop revealing the key: every "
        "distractor should sound like a principled best practice, and the key must not be the only option that "
        "matches a well-known guideline."
        "\nRewrite it to be harder while keeping the same task statement, scenario, format, correct answer letter"
        f"{'s' if len(plan['key']) > 1 else ''} ({' and '.join(plan['key'])}), and the same underlying rule. Apply the "
        "difficulty guidance: beat the slogans, bury the decisive detail mid-stem with a red herring, paraphrase "
        "the guide. It must stay unambiguous: one expert answer, supported by verbatim quotes.\n\n"
        f"Current item:\n{json.dumps({k: item[k] for k in ('stem', 'options', 'key')}, ensure_ascii=False)}\n")
    new, cost = call_claude("harden", plan["id"], *WRITER, prompt, ITEM_SCHEMA, system_file=writer_file)
    if not new:
        return None, cost, "rewrite call failed; kept the original"
    fails, _ = rule_checks(new, plan, docs, others)
    if fails:
        return None, cost, f"rewrite failed rule checks ({'; '.join(fails)[:140]}); kept the original"
    ok, reason, summary2, signal, vcost = verify(new, plan, solver_file(new, docs, tmp, plan["id"] + "h"), pool)
    cost += vcost
    if not ok:
        return None, cost, f"rewrite failed verification ({reason}); kept the original"
    if share(summary2) >= share(summary):
        return None, cost, f"rewrite was no less guessable ({summary2['options_only']}); kept the original"
    return (new, (summary2, signal)), cost, f"rewritten harder: options-only {summary['options_only']} → " \
                                            f"{summary2['options_only']}, signal now {signal}"


def share(summary):
    c, n = summary["options_only"].split("/")
    return int(c) / int(n) if int(n) else 1.0


def repair(item, plan, writer_file, docs, others, summary, tmp, pool):
    """Every solver run chose the key but some called another option defensible: sharpen, then re-verify."""
    votes = ", ".join(f"option {k} in {v} of {summary['runs']} runs" for k, v in summary["second_defensible"].items())
    prompt = (
        f"Independent experts all chose the correct answer of this item, but they also called {votes} defensible. "
        "Revise the item so each of those options is clearly wrong: add or sharpen a stem detail that rules it out, "
        "or reword the option so it fails for a reason you can name. Don't make the correct option longer or more "
        "obvious, and keep the same task statement, scenario, format, correct answer letter"
        f"{'s' if len(plan['key']) > 1 else ''} ({' and '.join(plan['key'])}), and rule. Return the full item with "
        "verbatim quotes.\n\n"
        f"Current item:\n{json.dumps({k: item[k] for k in ('stem', 'options', 'key', 'why')}, ensure_ascii=False)}\n")
    new, cost = call_claude("repair", plan["id"], *WRITER, prompt, ITEM_SCHEMA, system_file=writer_file)
    if not new:
        return None, cost, "repair call failed"
    fails, _ = rule_checks(new, plan, docs, others)
    if fails:
        return None, cost, f"repair failed rule checks ({'; '.join(fails)[:140]})"
    ok, reason, summary2, signal, vcost = verify(new, plan, solver_file(new, docs, tmp, plan["id"] + "r"), pool)
    cost += vcost
    if not ok:
        return None, cost, f"repair failed verification ({reason})"
    return (new, (summary2, signal)), cost, "repaired: no second option defensible"


def cmd_generate(a):
    if a.scenario not in cca.FOLDERS:
        die(f"unknown scenario {a.scenario}")
    rng = random.Random()
    items = load_json(ITEMS, [])
    keys = load_json(KEYS, {})
    missing = [t for t in cca.F_AFFINITY if a.scenario in cca.F_AFFINITY[t]
               and not any((DOCS / f"{slug(u)}.md").exists() for u in task_urls(t))]
    if missing:
        print(f"No doc snapshot yet for {', '.join(missing)}; fetching…")
        cmd_snapshot(argparse.Namespace(tasks=None, scenario=a.scenario))
    plans = plan_items(a.scenario, a.n, rng)
    start = 1 + max((int(i["id"][1:]) for i in items), default=0)
    for i, p in enumerate(plans):
        p["id"] = f"F{start + i:04d}"
    sample_grams = [grams(b) for f in sorted((ROOT / "scenarios").glob("S*/exam.md"))
                    for b in re.split(r"\n### Q\d+\n", f.read_text()) if b.strip()]  # guide blocks + samples
    tmp = Path(tempfile.mkdtemp(prefix="cca-bank-"))
    sys_cache = {}
    t0 = time.time()
    print(f"Generating {a.n} {a.difficulty} item(s) for {a.scenario} with {a.workers} at a time. "
          "Item text is never printed.")

    def one(plan):
        with LOCK:
            if plan["task"] not in sys_cache:
                sys_cache[plan["task"]] = system_files(plan["task"], a.difficulty, tmp)
            writer_file, docs = sys_cache[plan["task"]]
            same = [i for i in items if i["task"] == plan["task"] and i["scenario"] == plan["scenario"]]
            others = [grams(i["stem"]) for i in items] + sample_grams
        stems = [" ".join(i["stem"].split()[:14]) + "…" for i in same]
        item, fails, warns, cost, tries = write_item(plan, writer_file, docs, others, a.difficulty, stems)
        rec = {"id": plan["id"], "task": plan["task"], "domain": cca.domain_of(plan["task"]),
               "scenario": plan["scenario"], "type": plan["type"], "difficulty_target": a.difficulty,
               "created": cca.today().isoformat(), "seen": [], "writes": tries,
               "stem": item["stem"] if item else "", "options": item["options"] if item else {},
               "checks": {"fail": fails, "warn": warns}}
        if item and plan["type"] == "single":
            rec["options"] = {k: v for k, v in item["options"].items() if k in "ABCD"}
        if fails:
            rec.update(status="rejected", reason="; ".join(fails), verify=None, difficulty_signal=None)
        else:
            ok, reason, summary, signal, vcost = verify(item, plan, solver_file(item, docs, tmp, plan["id"]),
                                                        call_pool)
            cost += vcost
            rec.update(status="verified" if ok else "quarantined", reason=reason, verify=summary,
                       difficulty_signal=signal)
            if not ok and (reason or "").startswith("second option defensible"):
                fixed, rcost, note = repair(item, plan, writer_file, docs, others, summary, tmp, call_pool)
                cost += rcost
                rec["repair"] = note
                if fixed:
                    item, (summary, signal) = fixed
                    ok = True
                    rec.update(status="verified", reason=None, verify=summary, difficulty_signal=signal,
                               stem=item["stem"], options={k: v for k, v in item["options"].items()
                                                           if k in ("ABCDE" if plan["type"] == "multi" else "ABCD")})
            if ok and signal == "easy" and a.harden:
                hard, hcost, note = harden(item, plan, writer_file, docs, others, summary, tmp, call_pool)
                cost += hcost
                rec["hardening"] = note
                if hard:
                    item, (h_summary, h_signal) = hard
                    rec.update(stem=item["stem"], options={k: v for k, v in item["options"].items()
                                                           if k in ("ABCDE" if plan["type"] == "multi" else "ABCD")},
                               verify=h_summary, difficulty_signal=h_signal,
                               checks={"fail": [], "warn": rule_checks(item, plan, docs, others)[1]})
        if a.dev:
            rec["status"] = "dev"
        rec["cost_usd"] = round(cost, 4)
        with LOCK:
            items.append(rec)
            if item:
                keys[plan["id"]] = {"key": plan["key"], "rule": item["rule"], "why": item["why"],
                                    "evidence": item["evidence"], "question_type": item["question_type"],
                                    "hardness_note": item["hardness_note"]}
            save_json(ITEMS, items)
            save_json(KEYS, keys)
        v = rec.get("verify") or {}
        detail = (f"{v.get('agree')}/{v.get('runs')} solver runs on the key · options-only {v.get('options_only')} "
                  f"· weak model {v.get('weak')} · difficulty {rec['difficulty_signal']}" if v else rec["reason"])
        if rec["status"] == "quarantined" and rec.get("reason"):
            detail += f" · {rec['reason']}"
        for k in ("repair", "hardening"):
            if rec.get(k):
                detail += f" · {rec[k]}"
        print(f"  {rec['id']} {plan['task']} {plan['type']:<6} → {rec['status']:<11} {detail} · ${cost:.2f}",
              flush=True)
        return rec

    with cf.ThreadPoolExecutor(max_workers=max(4, a.workers * 3)) as call_pool, \
            cf.ThreadPoolExecutor(max_workers=a.workers) as item_pool:
        recs = list(item_pool.map(one, plans))
    shutil.rmtree(tmp, ignore_errors=True)
    by = Counter(r["status"] for r in recs)
    total = sum(r["cost_usd"] for r in recs)
    print(f"\nDone in {round((time.time() - t0) / 60, 1)} min: " + ", ".join(f"{v} {k}" for k, v in by.items()) +
          f". Usage at list prices: ${total:.2f} (${total / max(1, len(recs)):.2f} per item). "
          "On a Claude plan this counts toward your usage limits rather than a bill.")


def cmd_repair(a):
    items = load_json(ITEMS, [])
    keys = load_json(KEYS, {})
    retryable = ("repair call failed", "repair failed verification (solver calls failed)")
    todo = [i for i in items if i["status"] == "quarantined" and i.get("repair", retryable[0]) in retryable
            and (i.get("reason") or "").startswith("second option defensible")]
    if not todo:
        print("Nothing to repair: no quarantined items with only a 'second option defensible' flag.")
        return
    tmp = Path(tempfile.mkdtemp(prefix="cca-bank-"))
    others_all = [(i["id"], grams(i["stem"])) for i in items]
    print(f"Repairing {len(todo)} quarantined item(s). Item text is never printed.")
    with cf.ThreadPoolExecutor(max_workers=8) as pool:
        for rec in todo:
            k = keys[rec["id"]]
            item = {"stem": rec["stem"], "options": rec["options"], "key": k["key"], "why": k["why"],
                    "evidence": k["evidence"]}
            plan = {"id": rec["id"], "task": rec["task"], "scenario": rec["scenario"], "type": rec["type"],
                    "key": k["key"]}
            writer_file, docs = system_files(rec["task"], rec.get("difficulty_target", "hard"), tmp)
            others = [g for iid, g in others_all if iid != rec["id"]]
            fixed, cost, note = repair(item, plan, writer_file, docs, others, rec["verify"], tmp, pool)
            rec["repair"], rec["cost_usd"] = note, round(rec.get("cost_usd", 0) + cost, 4)
            if fixed:
                new, (summary, signal) = fixed
                rec.update(status="verified", reason=None, verify=summary, difficulty_signal=signal,
                           stem=new["stem"], options={x: v for x, v in new["options"].items()
                                                      if x in ("ABCDE" if rec["type"] == "multi" else "ABCD")})
                keys[rec["id"]] = {"key": k["key"], "rule": new["rule"], "why": new["why"], "evidence": new["evidence"],
                                   "question_type": new["question_type"], "hardness_note": new["hardness_note"]}
            save_json(ITEMS, items)
            save_json(KEYS, keys)
            print(f"  {rec['id']} {rec['task']} → {rec['status']:<11} {note} · ${cost:.2f}", flush=True)
    shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------- status, forms, grading

def cmd_status(a):
    items = load_json(ITEMS, [])
    if not items:
        print("The bank is empty. Run: python3 scripts/bank.py generate --scenario S1 --n 10")
        return
    st = Counter(i["status"] for i in items)
    print("## Question bank\n" + ", ".join(f"{v} {k}" for k, v in sorted(st.items())))
    print("\n| Scenario | Verified | Unseen | Quarantined | Rejected | Difficulty signal (unseen) |")
    print("|---|---|---|---|---|---|")
    for s in cca.ORDER:
        si = [i for i in items if i["scenario"] == s]
        if not si:
            continue
        ver = [i for i in si if i["status"] == "verified"]
        un = [i for i in ver if not i["seen"]]
        sig = Counter(i.get("difficulty_signal") for i in un)
        print(f"| {s} | {len(ver)} | {len(un)} | {sum(i['status'] == 'quarantined' for i in si)} | "
              f"{sum(i['status'] == 'rejected' for i in si)} | " +
              ", ".join(f"{k} {v}" for k, v in sig.items() if k) + " |")
    ready = [s for s in cca.ORDER if sum(i["scenario"] == s and i["status"] == "verified" and not i["seen"]
                                         for i in items) >= 15]
    print(f"\nScenarios with 15+ unseen verified items: {', '.join(ready) or 'none'}. A full mock needs 4.")
    runs = [json.loads(x) for x in RUNS.read_text().splitlines()] if RUNS.exists() else []
    if runs:
        print(f"Claude calls so far: {len(runs)} · usage at list prices ${sum(r['cost_usd'] for r in runs):.2f}")


def new_form(kind, ids, scenarios):
    """Create a form. Its items count as seen from now on: once shown, they're no longer fresh."""
    sess = f"{scenarios[0]}-bank-{stamp()}" if kind == "block" else f"{stamp()}-F-bank"
    if (FORMS / f"{sess}.json").exists():
        sess += dt.datetime.now().strftime("%S")
    form = {"session": sess, "kind": kind, "created": cca.now(), "scenarios": scenarios, "items": ids,
            "answers": {}, "graded": None}
    save_json(FORMS / f"{sess}.json", form)
    items = load_json(ITEMS, [])
    for i in items:
        if i["id"] in ids and sess not in i["seen"]:
            i["seen"].append(sess)
    save_json(ITEMS, items)
    return form


def pick_items(pool, n, rng, targets=None):
    """Pick n items: spread over tasks (max 2 per task), no near-duplicate stems, optional domain targets."""
    rng.shuffle(pool)
    if targets:
        pool.sort(key=lambda i: -targets.get(i["domain"], 0))
    out, per_task = [], Counter()
    for i in pool:
        if len(out) == n:
            break
        if per_task[i["task"]] >= 2 or any(jaccard(grams(i["stem"]), grams(o["stem"])) > 0.3 for o in out):
            continue
        if targets is not None and targets.get(i["domain"], 0) <= 0 and any(v > 0 for v in targets.values()):
            continue
        out.append(i)
        per_task[i["task"]] += 1
        if targets is not None:
            targets[i["domain"]] = targets.get(i["domain"], 0) - 1
    return out


def cmd_form(a):
    items = load_json(ITEMS, [])
    rng = random.Random()
    fresh = [i for i in items if i["status"] == "verified" and not i["seen"]]
    if a.block:
        pool = [i for i in fresh if i["scenario"] == a.block]
        if not pool:
            die(f"no unseen verified items for {a.block}; generate some first")
        chosen = pick_items(pool, min(a.n, len(pool)), rng)
        form = new_form("block", [i["id"] for i in chosen], [a.block])
    else:
        ok = [s for s in cca.ORDER if sum(i["scenario"] == s for i in fresh) >= 15]
        if len(ok) < 4:
            die(f"a mock needs 15 unseen verified items in 4 scenarios; ready: {', '.join(ok) or 'none'}")
        scen = sorted(rng.sample(ok, 4))
        weights = {d: w for d, (_, w) in cca.EXAMS["F"]["domains"].items()}
        targets = cca.largest_remainder(60, weights)
        chosen = []
        for s in scen:
            chosen += pick_items([i for i in fresh if i["scenario"] == s], 15, rng, targets)
        form = new_form("mock", [i["id"] for i in chosen], scen)
    keys = load_json(KEYS, {})
    letters = Counter(k for i in form["items"] for k in keys[i]["key"])
    print(f"session: {form['session']}\nitems: {len(form['items'])} ({form['kind']}, {', '.join(form['scenarios'])})"
          f"\nkey letters: {dict(sorted(letters.items()))}")


def load_form(sess):
    f = FORMS / f"{sess}.json"
    if not f.exists():
        die(f"no form {sess}")
    return json.loads(f.read_text())


def cmd_show(a):
    form = load_form(a.session)
    items = {i["id"]: i for i in load_json(ITEMS, [])}
    if not 1 <= a.n <= len(form["items"]):
        die(f"item number must be 1–{len(form['items'])}")
    it = items[form["items"][a.n - 1]]
    prev = items[form["items"][a.n - 2]]["scenario"] if a.n > 1 else None
    if it["scenario"] != prev:
        print(f"## Scenario: {cca.EXAMS['F']['scenarios'][it['scenario']][0]}\n\n{scenario_frame(it['scenario'])}\n")
    print(f"### Q{a.n} of {len(form['items'])}\n\n{it['stem']}\n")
    for k, v in it["options"].items():
        print(f"{k}. {v}")


def cmd_answer(a):
    form = load_form(a.session)
    if form["graded"]:
        die("this form is already graded")
    if not 1 <= a.n <= len(form["items"]):
        die(f"item number must be 1–{len(form['items'])}")
    letters = "".join(sorted(set(a.letters.upper().replace(",", ""))))
    if not re.fullmatch(r"[A-E]{1,2}", letters):
        die("answer with one or two letters, e.g. B or BD")
    form["answers"][str(a.n)] = {"letters": letters, "conf": a.conf, "flag": a.flag}
    save_json(FORMS / f"{a.session}.json", form)
    print(f"recorded {a.n}: {letters}" + (f" [{a.conf}]" if a.conf else "") + (" [flag]" if a.flag else "") +
          f" · {len(form['answers'])}/{len(form['items'])} answered")


def doc_url(name):
    m = load_json(DOCS / "manifest.json", {}).get(name)
    return m["url"] if m else ""


def cmd_grade(a):
    form = load_form(a.session)
    if form["graded"]:
        die("already graded")
    items = load_json(ITEMS, [])
    by_id = {i["id"]: i for i in items}
    keys = load_json(KEYS, {})
    # a retake has seen its answers, so it's logged apart from first tries (practice_test.py retake)
    source = "retake" if form.get("retake_of") else "mock" if form["kind"] == "mock" else "scenario"
    correct, per_dom, misses = 0, defaultdict(lambda: [0, 0]), []
    for n, iid in enumerate(form["items"], 1):
        it, k = by_id[iid], keys[iid]
        ans = form["answers"].get(str(n), {})
        ok = ans.get("letters") == "".join(sorted(k["key"]))
        correct += ok
        per_dom[it["domain"]][0] += ok
        per_dom[it["domain"]][1] += 1
        row = {"ts": cca.now(), "exam": "F", "source": source, "task": it["task"], "domain": it["domain"],
               "correct": ok, "scenario": it["scenario"], "session": form["session"], "bank_item": iid}
        if ans.get("conf"):
            row["confidence"] = ans["conf"]
        if not ok:
            row["lesson"] = k["rule"]
            sup = [e for e in k["evidence"] if e["role"] == "supports key"]
            if sup and doc_url(sup[0]["doc"]):
                row["doc"] = doc_url(sup[0]["doc"])
            misses.append((n, iid, ans.get("conf")))
        cca.append(row)
        if form["session"] not in it["seen"]:
            it["seen"].append(form["session"])
    n = len(form["items"])
    lo, hi = wilson(correct, n)
    form["graded"] = {"date": cca.today().isoformat(), "correct": correct, "n": n,
                      "pct": round(100 * correct / n), "ci": [round(100 * lo), round(100 * hi)]}
    save_json(FORMS / f"{a.session}.json", form)
    save_json(ITEMS, items)
    print(f"## {form['session']} · {correct}/{n} = {round(100 * correct / n)}% "
          f"(95% interval {round(100 * lo)}–{round(100 * hi)}%)")
    for d, (c, t) in sorted(per_dom.items()):
        print(f"- D{d} {cca.EXAMS['F']['domains'][d][0]}: {c}/{t}")
    if misses:
        print("Missed: " + ", ".join(f"Q{m} ({iid}{', ' + c + ' confidence' if c else ''})" for m, iid, c in misses))
    print(f"Logged {n} items as source={source}. Review with: python3 scripts/bank.py review {form['session']}")


def print_item(it, k, num=None, answer=None):
    head = f"### {'Q' + str(num) + ' · ' if num else ''}{it['id']} · {it['task']} · {it['scenario']} · {it['status']}"
    print(head + "\n\n" + it["stem"] + "\n")
    for key, v in it["options"].items():
        mark = " ✓" if key in k["key"] else ""
        print(f"{key}. {v}{mark}")
    if answer is not None:
        print(f"\nYour answer: {answer.get('letters', '—')}" + (f" ({answer['conf']})" if answer.get("conf") else ""))
    print(f"Key: {'+'.join(k['key'])} · rule: {k['rule']}")
    for key in it["options"]:
        if k["why"].get(key):
            print(f"- {key}: {k['why'][key]}")
    for e in k["evidence"]:
        print(f'  > "{e["quote"]}" ({e["doc"]}{" · " + doc_url(e["doc"]) if doc_url(e["doc"]) else ""})')
    v = it.get("verify") or {}
    if v:
        print(f"Checks: {v['agree']}/{v['runs']} solver runs on the key · options-only {v['options_only']} · "
              f"weak model {v['weak']} · difficulty signal {it.get('difficulty_signal')}"
              + (f" · {it['reason']}" if it.get("reason") else ""))
    print()


def cmd_review(a):
    items = {i["id"]: i for i in load_json(ITEMS, [])}
    keys = load_json(KEYS, {})
    if a.quarantine:
        q = [i for i in items.values() if i["status"] == "quarantined"]
        if not q:
            print("No quarantined items.")
        for it in q:
            print_item(it, keys[it["id"]])
        return
    if not a.session:
        die("give a graded SESSION, or --quarantine")
    form = load_form(a.session)
    if not form["graded"]:
        die("grade the form first; reviewing before grading would show the keys")
    nums = [a.n] if a.n else range(1, len(form["items"]) + 1)
    for n in nums:
        iid = form["items"][n - 1]
        print_item(items[iid], keys[iid], n, form["answers"].get(str(n), {}))


def cmd_dispute(a):
    items = load_json(ITEMS, [])
    it = next((i for i in items if i["id"] == a.id), None) or die(f"no item {a.id}")
    it["status"], it["dispute"] = "disputed", {"date": cca.today().isoformat(), "note": a.note}
    save_json(ITEMS, items)
    print(f"{a.id} disputed: it won't appear in new forms until resolved")


def cmd_resolve(a):
    items = load_json(ITEMS, [])
    it = next((i for i in items if i["id"] == a.id), None) or die(f"no item {a.id}")
    it["status"] = "verified" if a.action == "keep" else "retired"
    it.setdefault("dispute", {})["resolution"] = {"date": cca.today().isoformat(), "action": a.action,
                                                  "note": a.note}
    save_json(ITEMS, items)
    print(f"{a.id} → {it['status']}")


def graded_forms():
    out = []
    for f in sorted(FORMS.glob("*.json")) if FORMS.exists() else []:
        form = json.loads(f.read_text())
        if form.get("graded"):
            out.append(form)
    return sorted(out, key=lambda x: x["created"])


def open_forms():
    """Forms built but neither graded nor voided: tests not taken yet, oldest first."""
    out = []
    for f in sorted(FORMS.glob("*.json")) if FORMS.exists() else []:
        form = json.loads(f.read_text())
        if not form.get("graded") and not form.get("void"):
            out.append(form)
    return sorted(out, key=lambda x: x["created"])


def cmd_history(a):
    forms = graded_forms()
    if not forms:
        print("No graded bank forms yet.")
        return
    print("| Date | Session | Kind | Score | 95% interval |\n|---|---|---|---|---|")
    for f in forms:
        g = f["graded"]
        kind = f"retake {f['attempt']} of {f['retake_of']}" if f.get("retake_of") else f["kind"]
        print(f"| {g['date']} | {f['session']} | {kind} | {g['correct']}/{g['n']} ({g['pct']}%) | "
              f"{g['ci'][0]}–{g['ci'][1]}% |")
    mocks = [f for f in forms if f["kind"] == "mock"][-3:]
    if mocks:
        c = sum(f["graded"]["correct"] for f in mocks)
        n = sum(f["graded"]["n"] for f in mocks)
        lo, hi = wilson(c, n)
        print(f"\nLast {len(mocks)} mock(s) pooled: {c}/{n} = {round(100 * c / n)}%, 95% interval "
              f"{round(100 * lo)}–{round(100 * hi)}%. Ready when 3 fresh mocks put the low end at 80% or more.")


def cmd_inspect(a):
    items = {i["id"]: i for i in load_json(ITEMS, [])}
    it = items.get(a.id) or die(f"no item {a.id}")
    if it["status"] not in ("dev", "rejected", "quarantined", "retired") and not it["seen"] and not a.force:
        die("this item is unseen and scorable; inspecting it would spoil it (use --force to burn it)")
    if a.force and not it["seen"]:
        it["seen"].append("inspected")
        save_json(ITEMS, list(items.values()))
    print_item(it, load_json(KEYS, {})[a.id])


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("snapshot")
    s.add_argument("--tasks")
    s.add_argument("--scenario")
    s.set_defaults(fn=cmd_snapshot)
    s = sub.add_parser("generate")
    s.add_argument("--scenario", required=True)
    s.add_argument("--n", type=int, default=10)
    s.add_argument("--difficulty", choices=["hard", "standard"], default="hard")
    s.add_argument("--workers", type=int, default=3)
    s.add_argument("--dev", action="store_true", help="mark items as dev: inspectable, never scored")
    s.add_argument("--harden", action="store_true",
                   help="rewrite easy items once to be harder (costs more; most rewrites fail the checks)")
    s.set_defaults(fn=cmd_generate)
    sub.add_parser("status").set_defaults(fn=cmd_status)
    sub.add_parser("repair").set_defaults(fn=cmd_repair)
    s = sub.add_parser("form")
    g = s.add_mutually_exclusive_group(required=True)
    g.add_argument("--block", metavar="S#")
    g.add_argument("--mock", action="store_true")
    s.add_argument("--n", type=int, default=15)
    s.set_defaults(fn=cmd_form)
    s = sub.add_parser("show")
    s.add_argument("session")
    s.add_argument("n", type=int)
    s.set_defaults(fn=cmd_show)
    s = sub.add_parser("answer")
    s.add_argument("session")
    s.add_argument("n", type=int)
    s.add_argument("letters")
    s.add_argument("--conf", choices=["high", "medium", "low"])
    s.add_argument("--flag", action="store_true")
    s.set_defaults(fn=cmd_answer)
    s = sub.add_parser("grade")
    s.add_argument("session")
    s.set_defaults(fn=cmd_grade)
    s = sub.add_parser("review")
    s.add_argument("session", nargs="?")
    s.add_argument("--n", type=int)
    s.add_argument("--quarantine", action="store_true")
    s.set_defaults(fn=cmd_review)
    s = sub.add_parser("dispute")
    s.add_argument("id")
    s.add_argument("--note", required=True)
    s.set_defaults(fn=cmd_dispute)
    s = sub.add_parser("resolve")
    s.add_argument("id")
    s.add_argument("action", choices=["keep", "retire"])
    s.add_argument("--note")
    s.set_defaults(fn=cmd_resolve)
    sub.add_parser("history").set_defaults(fn=cmd_history)
    s = sub.add_parser("inspect")
    s.add_argument("id")
    s.add_argument("--force", action="store_true")
    s.set_defaults(fn=cmd_inspect)
    a = p.parse_args()
    a.fn(a)
    if a.cmd in ("form", "grade"):  # what the dashboard shows: open and graded tests
        cca.refresh_dashboard()


if __name__ == "__main__":
    main()
