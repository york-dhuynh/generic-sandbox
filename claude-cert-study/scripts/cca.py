#!/usr/bin/env python3
"""Progress tracker and randomizer for Claude Certified Architect exam prep.

Standard library only. Data lives in <study root>/progress/log.jsonl, one JSON object per line.

  cca.py log      --exam F --source quiz --task 1.4 --result wrong [--confidence high] [--scenario S1]
                  [--lesson "rule to remember"] [--doc URL] [--session ID]
  cca.py external --exam F --label "site diagnostic" --correct 31 --total 40 [--domain 2]
  cca.py stats    --exam F
  cca.py missed   --exam F [--task 1.4]
  cca.py draw     --exam F --quiz 5 [--domain 1 | --task 1.4 | --scenario S3 | --review]
  cca.py draw     --exam F --diagnostic
  cca.py draw     --exam F --mock [--save | --out DIR]
  cca.py labs     --list
  cca.py undo     --exam F                      # remove the most recent entry for that exam
  cca.py import   --exam F --source mock --session ID --file results.jsonl
                  (one JSON object per line: task, result, and optional confidence, scenario, lesson, doc)
                  Scenario guide blocks use --source scenario --session S1-block-YYYYMMDD-HHMM.

Daily rotation and review queue (Foundations scenarios; see scenarios/README.md):
  cca.py day      [--minutes 90] [--set N | --advance]   # today's plan: deep dive, overview, quick review
  cca.py day      --mark deep|overview|review [--partial]
  cca.py overview S3                                     # spoiler-free map of a scenario (no items, no keys)
  cca.py queue    add --scenario S1 --kind recall|open|pre --prompt "..." [--answer "..."] [--task 5.1]
                  [--ref "S1-block-YYYYMMDD-HHMM Q5"]
  cca.py queue    due [--scenarios S1,S3] [--per 3]       # today's review set, interleaved
  cca.py queue    show ID | mark ID --result right|wrong | drop ID
  cca.py queue    update ID [--kind K] [--prompt P] [--answer A] [--ref R] [--task T]
  cca.py queue    list [--scenario S1] [--kind open] [--all]
  Every queue change rewrites progress/notebook.md (prompts only, no answers).

Study journal and dashboard:
  cca.py journal  add --kind session|milestone|note --text "..." [--minutes 85] [--date YYYY-MM-DD]
  cca.py journal  list [--n 10]
  cca.py dashboard [--exam F] [--open]                  # writes progress/dashboard.html (scripts/dashboard.py)
  Commands that change progress rebuild the dashboard themselves; its Refresh button reloads the page.
  CCA_TODAY=YYYY-MM-DD overrides today's date, for testing.
"""
import argparse
import datetime as dt
import json
import os
import random
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "progress" / "log.jsonl"
MOCKS = ROOT / "progress" / "mocks"
LABS = ROOT / "labs"


def _tasks(prefix, counts):
    return {str(d): [f"{prefix}{d}.{i}" for i in range(1, n + 1)] for d, n in counts.items()}


F_TASKS = _tasks("", {1: 7, 2: 5, 3: 6, 4: 6, 5: 6})
P_TASKS = _tasks("P", {1: 6, 2: 5, 3: 8, 4: 6, 5: 5, 6: 5, 7: 3})

EXAMS = {
    "F": {
        "name": "CCAR-F (Architect – Foundations)",
        "items": 60,
        "domains": {
            "1": ("Agentic Architecture & Orchestration", 27),
            "2": ("Tool Design & MCP Integration", 18),
            "3": ("Claude Code Configuration & Workflows", 20),
            "4": ("Prompt Engineering & Structured Output", 20),
            "5": ("Context Management & Reliability", 15),
        },
        "tasks": F_TASKS,
        "scenarios": {
            "S1": ("Customer Support Resolution Agent", ["1", "2", "5"]),
            "S2": ("Code Generation with Claude Code", ["3", "5"]),
            "S3": ("Multi-Agent Research System", ["1", "2", "5"]),
            "S4": ("Developer Productivity with Claude", ["2", "3", "1"]),
            "S5": ("Claude Code for Continuous Integration", ["3", "4"]),
            "S6": ("Structured Data Extraction", ["4", "5"]),
        },
    },
    "P": {
        "name": "CCAR-P (Architect – Professional)",
        "items": 63,
        "domains": {
            "1": ("Solution Design & Architecture", 17),
            "2": ("Claude Models, Prompting & Context Engineering", 13),
            "3": ("Integration", 19),
            "4": ("Evaluation, Testing & Optimization", 16),
            "5": ("Governance, Safety & Risk Management", 14),
            "6": ("Stakeholder Communication & Lifecycle Management", 14),
            "7": ("Developer Productivity & Operational Enablement", 7),
        },
        "tasks": P_TASKS,
        "scenarios": {},
    },
}

SOURCES = ["quiz", "learn", "diagnostic", "review", "mock", "scenario"]

# Foundations scenarios that suit each task statement, best fit first. Used so a drawn
# objective lands in a scenario where it naturally arises (e.g. 3.6 CI in S5, 5.6 provenance in S3).
F_AFFINITY = {
    "1.1": ["S1", "S3", "S4"], "1.2": ["S3", "S1"], "1.3": ["S3", "S4"], "1.4": ["S1"],
    "1.5": ["S1", "S3"], "1.6": ["S3", "S5", "S4", "S2"], "1.7": ["S4", "S2", "S3"],
    "2.1": ["S1", "S3", "S4"], "2.2": ["S1", "S3"], "2.3": ["S3", "S1", "S6"],
    "2.4": ["S4", "S2"], "2.5": ["S4", "S2"],
    "3.1": ["S2", "S5", "S4"], "3.2": ["S2", "S4"], "3.3": ["S2", "S4"], "3.4": ["S2", "S4"],
    "3.5": ["S2", "S4"], "3.6": ["S5"],
    "4.1": ["S5", "S6"], "4.2": ["S5", "S6", "S1"], "4.3": ["S6", "S5"], "4.4": ["S6", "S5"],
    "4.5": ["S6", "S5"], "4.6": ["S5", "S2"],
    "5.1": ["S1", "S3"], "5.2": ["S1"], "5.3": ["S3"], "5.4": ["S4", "S2"],
    "5.5": ["S6"], "5.6": ["S3"],
}

MULTI_RATE = 0.12  # share of multiple-response items in drawn sets

ROTATION = ROOT / "progress" / "rotation.jsonl"
QUEUE = ROOT / "progress" / "queue.json"
NOTEBOOK = ROOT / "progress" / "notebook.md"
JOURNAL = ROOT / "progress" / "journal.jsonl"
SCEN_PROGRESS = ROOT / "progress" / "scenarios"

# Rotation order from scenarios/README.md. Day n: deep dive ORDER[n-1], overview ORDER[n] (first cycle only),
# quick review of every scenario introduced so far. From day 7 the deep dive keeps rotating.
ORDER = ["S1", "S3", "S6", "S5", "S4", "S2"]
FOLDERS = {"S1": "S1-customer-support", "S2": "S2-code-generation", "S3": "S3-multi-agent-research",
           "S4": "S4-developer-productivity", "S5": "S5-ci-cd", "S6": "S6-structured-extraction"}
KINDS = ["recall", "open", "pre"]
STEPS = [1, 7]  # days to the next review after a right answer in box 0, then box 1; right in box 2 = solid


def die(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(2)


def domain_of(task):
    return task.lstrip("P").split(".")[0]


def all_tasks(exam):
    return [t for d in EXAMS[exam]["domains"] for t in EXAMS[exam]["tasks"][d]]


def load(exam=None):
    if not LOG.exists():
        return []
    rows = []
    for n, line in enumerate(LOG.read_text().splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            print(f"warning: skipping malformed line {n} in {LOG}", file=sys.stderr)
            continue
        if exam is None or row.get("exam") == exam:
            rows.append(row)
    return rows


def append(row):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def now():
    return dt.datetime.now().replace(microsecond=0).isoformat()


def today():
    return dt.date.fromisoformat(os.environ["CCA_TODAY"]) if os.environ.get("CCA_TODAY") else dt.date.today()


def pct(c, n):
    return f"{round(100 * c / n)}%" if n else "–"


def largest_remainder(total, weights):
    raw = {k: total * w / sum(weights.values()) for k, w in weights.items()}
    out = {k: int(v) for k, v in raw.items()}
    for k in sorted(raw, key=lambda k: raw[k] - out[k], reverse=True)[: total - sum(out.values())]:
        out[k] += 1
    return out


def key_for(rng):
    if rng.random() < MULTI_RATE:
        return "multi(2)", ",".join(sorted(rng.sample("ABCDE", 2)))
    return "single", rng.choice("ABCD")


# ---------------------------------------------------------------- commands

def cmd_log(a):
    if a.task not in all_tasks(a.exam):
        die(f"unknown task '{a.task}' for exam {a.exam}. Valid: {', '.join(all_tasks(a.exam))}")
    if a.scenario and not EXAMS[a.exam]["scenarios"]:
        a.scenario = None  # Professional items are standalone; ignore any scenario value
    if a.scenario and a.scenario not in EXAMS[a.exam]["scenarios"]:
        die(f"unknown scenario '{a.scenario}' for exam {a.exam}")
    row = {"ts": now(), "exam": a.exam, "source": a.source, "task": a.task,
           "domain": domain_of(a.task), "correct": a.result == "correct"}
    for k in ("confidence", "scenario", "lesson", "doc", "session"):
        v = getattr(a, k)
        if v:
            row[k] = v
    append(row)
    mark = "correct" if row["correct"] else "wrong"
    print(f"logged {a.exam} {a.task} {mark} ({a.source})")


def cmd_external(a):
    if a.correct > a.total or a.total <= 0:
        die("need 0 <= correct <= total and total > 0")
    if a.domain and a.domain not in EXAMS[a.exam]["domains"]:
        die(f"unknown domain '{a.domain}' for exam {a.exam}")
    row = {"ts": now(), "exam": a.exam, "source": "external", "label": a.label,
           "ext_correct": a.correct, "ext_total": a.total}
    if a.domain:
        row["domain"] = a.domain
    append(row)
    print(f"logged external result {a.correct}/{a.total} ({a.label})")


def practice_rows(rows):
    return [r for r in rows if r.get("source") in SOURCES and "task" in r]


def mastery(rows, exam, window=10):
    """Per-task (credit, n) for adaptive draws: a low-confidence correct answer earns half credit."""
    by = defaultdict(list)
    for r in practice_rows(rows):
        credit = (0.5 if r.get("confidence") == "low" else 1.0) if r["correct"] else 0.0
        by[r["task"]].append(credit)
    return {t: (sum(by.get(t, [])[-window:]), len(by.get(t, [])[-window:])) for t in all_tasks(exam)}


def task_stats(rows, exam, window=10):
    by = defaultdict(list)
    for r in practice_rows(rows):
        by[r["task"]].append(r["correct"])
    out = {}
    for t in all_tasks(exam):
        hist = by.get(t, [])[-window:]
        out[t] = (sum(hist), len(hist), len(by.get(t, [])))
    return out


def lab_status():
    out = []
    if not LABS.exists():
        return out
    for d in sorted(p for p in LABS.iterdir() if p.is_dir()):
        status = "?"
        readme = d / "README.md"
        if readme.exists():
            for line in readme.read_text().splitlines():
                if line.lower().startswith("status:"):
                    status = line.split(":", 1)[1].strip()
                    break
        out.append((d.name, status))
    return out


def cmd_stats(a):
    ex = EXAMS[a.exam]
    rows = load(a.exam)
    prac = practice_rows(rows)
    print(f"## {ex['name']} progress")
    if not prac:
        print("No practice items logged yet. Start with "
              + ("`/cca-day` (day 1: S1 deep dive, S3 overview)." if a.exam == "F" else "`/cca-quiz diagnostic professional`."))
    by_src = defaultdict(int)
    for r in prac:
        by_src[r["source"]] += 1
    if prac:
        print(f"{len(prac)} practice items logged (" + ", ".join(f"{k} {v}" for k, v in sorted(by_src.items())) + ")\n")
        print("| Domain | Weight | Items | Accuracy | Last 20 |")
        print("|---|---|---|---|---|")
        weighted, wsum = 0.0, 0
        for d, (name, w) in ex["domains"].items():
            dr = [r["correct"] for r in prac if r["domain"] == d]
            last = dr[-20:]
            print(f"| D{d} {name} | {w}% | {len(dr)} | {pct(sum(dr), len(dr))} | {pct(sum(last), len(last))} |")
            if dr:
                weighted += w * sum(dr) / len(dr)
                wsum += w
        if wsum:
            print(f"\nBlueprint-weighted accuracy: {round(100 * weighted / wsum)}% "
                  f"(over attempted domains; practice items only, not a scaled score)")

        ts = task_stats(rows, a.exam)
        never = [t for t, (c, n, tot) in ts.items() if tot == 0]
        print(f"\nCoverage: {len(ts) - len(never)}/{len(ts)} objectives attempted."
              + (f" Never attempted: {', '.join(never)}" if never else ""))
        weak = [(t, c, n) for t, (c, n, tot) in ts.items() if n >= 2 and c / n < 0.8]
        weak.sort(key=lambda x: (x[1] / x[2]) - ex["domains"][domain_of(x[0])][1] / 200)
        if weak:
            print("Weakest (last 10 per objective, ≥2 attempts): "
                  + ", ".join(f"{t} ({c}/{n})" for t, c, n in weak[:6]))
        conf = [r for r in prac[-40:] if not r["correct"] and r.get("confidence") == "high"]
        if conf:
            print("Confident misses in last 40 items: "
                  + "; ".join(f"{r['task']}: {r.get('lesson', '(no lesson noted)')}" for r in conf[-5:]))

    sc_last = {}
    if prac and ex["scenarios"]:
        print("\n| Scenario | Items | Accuracy | Last 15 | Guide block (scenarios/) |")
        print("|---|---|---|---|---|")
        for s, (name, _) in ex["scenarios"].items():
            sr = [r for r in prac if r.get("scenario") == s]
            last = [r["correct"] for r in sr[-15:]]
            sc_last[s] = (sum(last), len(last))
            blocks = defaultdict(list)
            for r in sr:
                if r["source"] == "scenario" and r.get("session", "").startswith(f"{s}-block"):
                    blocks[r["session"]].append(r["correct"])
            block = "not started"
            if blocks:
                sid, res = sorted(blocks.items())[-1]
                block = f"{sum(res)}/{len(res)} ({sid.split('-block-')[-1][:8]})"
            print(f"| {s} {name} | {len(sr)} | {pct(sum(r['correct'] for r in sr), len(sr))} "
                  f"| {pct(*sc_last[s])} | {block} |")

    mocks = defaultdict(list)
    for r in prac:
        if r["source"] == "mock" and r.get("session"):
            mocks[r["session"]].append(r)
    if mocks:
        print("\nMocks:")
        for s, rs in sorted(mocks.items()):
            c = sum(r["correct"] for r in rs)
            per = []
            for d in ex["domains"]:
                dr = [r["correct"] for r in rs if r["domain"] == d]
                if dr:
                    per.append(f"D{d} {pct(sum(dr), len(dr))}")
            print(f"- {s}: {c}/{len(rs)} ({pct(c, len(rs))}) · " + " · ".join(per))

    ext = [r for r in rows if r.get("source") == "external"]
    if ext:
        print("\nExternal practice (third-party, not comparable to official items):")
        for r in ext[-5:]:
            dom = f" D{r['domain']}" if r.get("domain") else ""
            print(f"- {r['ts'][:10]} {r['label']}{dom}: {r['ext_correct']}/{r['ext_total']} "
                  f"({pct(r['ext_correct'], r['ext_total'])})")

    labs = lab_status()
    if labs:
        print("\nLabs: " + ", ".join(f"{n} [{s}]" for n, s in labs))

    if a.exam == "F" and (ROTATION.exists() or QUEUE.exists()):
        rr = rotation_rows()
        n = current_day(rr)
        q = load_queue()
        act = [e for e in q if e["status"] == "active"]
        due = sum(e["kind"] != "pre" and e["due"] <= today().isoformat() for e in act)
        when = "in progress today" if rr and rr[-1]["date"] == today().isoformat() else "next"
        print(f"\nRotation: day {n} ({when}, deep dive {day_parts(n)[0]}) · "
              f"{sum(e['kind'] == 'open' for e in act)} open questions · {due} review items due · "
              f"{sum(e['status'] == 'solid' for e in q)} solid")

    if prac:
        print("\nReadiness checklist (study heuristic, not an official conversion to the 720 scaled score):")
        for label, ok in readiness(rows, a.exam):
            print(f"- [{'x' if ok else ' '}] {label}")


def readiness(rows, exam):
    """The readiness checklist as (label, met) pairs. Shared by `stats` and the dashboard."""
    ex = EXAMS[exam]
    prac = practice_rows(rows)
    ts = task_stats(rows, exam)
    dom_last = {}
    for d in ex["domains"]:
        last = [r["correct"] for r in prac if r["domain"] == d][-20:]
        dom_last[d] = (sum(last), len(last))
    sc_last = {}
    for s in ex["scenarios"]:
        last = [r["correct"] for r in prac if r.get("scenario") == s][-15:]
        sc_last[s] = (sum(last), len(last))
    mocks = defaultdict(list)
    for r in prac:
        if r["source"] == "mock" and r.get("session"):
            mocks[r["session"]].append(r)
    full = sorted(mocks.items())[-2:]
    return [
        ("Every objective attempted at least 3 times", all(tot >= 3 for _, _, tot in ts.values())),
        ("Every domain at least 75% over its last 20 items",
         all(n >= 10 and c / n >= 0.75 for c, n in dom_last.values())),
        *([("Every scenario at least 75% over its last 15 items (any 4 of 6 can appear)",
            all(n >= 10 and c / n >= 0.75 for c, n in sc_last.values()))] if sc_last else []),
        ("Last 2 mocks each at least 80%",
         len(full) == 2 and all(sum(r["correct"] for r in rs) / len(rs) >= 0.8 for _, rs in full)),
        ("No confident misses in the last 30 items",
         not any((not r["correct"]) and r.get("confidence") == "high" for r in prac[-30:])),
    ]


def cmd_missed(a):
    prac = practice_rows(load(a.exam))
    if a.task:
        prac = [r for r in prac if r["task"] == a.task]
    by = defaultdict(list)
    for r in prac:
        by[r["task"]].append(r)
    any_out = False
    for t in all_tasks(a.exam):
        rs = by.get(t, [])
        misses = [r for r in rs if not r["correct"]]
        if not misses:
            continue
        any_out = True
        last_miss = max(i for i, r in enumerate(rs) if not r["correct"])
        fixed = sum(r["correct"] for r in rs[last_miss + 1:])
        state = "re-check" if fixed < 2 else "recovered"
        print(f"### {t} · {len(misses)} missed · {state} ({fixed} correct since last miss)")
        for r in misses[-4:]:
            conf = f" [{r['confidence']} confidence]" if r.get("confidence") else ""
            lesson = r.get("lesson", "(no lesson noted)")
            doc = f" · {r['doc']}" if r.get("doc") else ""
            print(f"- {r['ts'][:10]}{conf}: {lesson}{doc}")
    if not any_out:
        print("No misses logged" + (f" for {a.task}" if a.task else "") + ".")


def weighted_pick(rng, items, weights, k):
    items, weights, out = list(items), list(weights), []
    while items and len(out) < k:
        i = rng.choices(range(len(items)), weights=weights)[0]
        out.append(items.pop(i))
        weights.pop(i)
    return out


def scenario_for(rng, exam, task, forced=None):
    sc = EXAMS[exam]["scenarios"]
    if not sc:
        return "-"
    if forced:
        return forced
    fits = F_AFFINITY.get(task, [])
    if fits:
        return fits[0] if rng.random() < 0.6 else rng.choice(fits)
    hosts = [s for s, (_, doms) in sc.items() if domain_of(task) in doms]
    return rng.choice(hosts or list(sc))


def print_items(exam, items, title):
    sc = EXAMS[exam]["scenarios"]
    print(f"## {title}")
    print("| # | Objective | Domain | Scenario | Type | Key |")
    print("|---|---|---|---|---|---|")
    for i, it in enumerate(items, 1):
        s = it["scenario"]
        sname = f"{s} {sc[s][0]}" if s in sc else "standalone"
        print(f"| {i} | {it['task']} | D{domain_of(it['task'])} | {sname} | {it['type']} | {it['key']} |")


def cmd_draw(a):
    if a.seed is None:
        a.seed = random.SystemRandom().randrange(1, 10**6)
    print(f"seed: {a.seed} (rerun with --seed {a.seed} to reproduce this draw)")
    rng = random.Random(a.seed)
    ex = EXAMS[a.exam]
    if a.mock:
        return draw_mock(a, rng)
    if a.diagnostic:
        tasks = []
        for d in ex["domains"]:
            tasks += rng.sample(ex["tasks"][d], 2)
        rng.shuffle(tasks)
        title = f"Diagnostic draw · {ex['name']} · 2 per domain"
    else:
        n = a.quiz or 5
        pool = all_tasks(a.exam)
        if a.domain:
            if a.domain not in ex["domains"]:
                die(f"unknown domain {a.domain}")
            pool = ex["tasks"][a.domain]
        if a.task:
            if a.task not in pool:
                die(f"unknown task {a.task}")
            pool = [a.task]
        if a.scenario:
            if a.scenario not in ex["scenarios"]:
                die(f"unknown scenario {a.scenario}")
            doms = ex["scenarios"][a.scenario][1]
            pool = ([t for t in pool if a.scenario in F_AFFINITY.get(t, [])]
                    or [t for t in pool if domain_of(t) in doms] or pool)
        ts = task_stats(load(a.exam), a.exam)
        if a.review:
            prac = practice_rows(load(a.exam))
            review = []
            for t in pool:
                rs = [r for r in prac if r["task"] == t]
                if any(not r["correct"] for r in rs):
                    last_miss = max(i for i, r in enumerate(rs) if not r["correct"])
                    if sum(r["correct"] for r in rs[last_miss + 1:]) < 2:
                        review.append(t)
            if not review:
                print("Nothing to review: every missed objective has 2+ correct answers since its last miss.")
                return
            pool = review
        ms = mastery(load(a.exam), a.exam)
        weights = []
        for t in pool:
            _, _, tot = ts[t]
            c, k = ms[t]
            acc = (c + 1) / (k + 2)
            w = ex["domains"][domain_of(t)][1] * ((1 - acc) + 0.15)
            weights.append(w * (1.5 if tot == 0 else 1.0))
        tasks = []
        while len(tasks) < n:
            tasks += weighted_pick(rng, pool, weights, n - len(tasks))
        title = f"Quiz draw · {ex['name']} · {n} items" + (" · review" if a.review else "")
    items = []
    for t in tasks:
        typ, key = key_for(rng)
        items.append({"task": t, "scenario": scenario_for(rng, a.exam, t, a.scenario), "type": typ, "key": key})
    print_items(a.exam, items, title)


def draw_mock(a, rng):
    ex = EXAMS[a.exam]
    targets = largest_remainder(ex["items"], {d: w for d, (_, w) in ex["domains"].items()})
    task_cycle = {}
    for d in ex["domains"]:
        lst = ex["tasks"][d][:]
        rng.shuffle(lst)
        task_cycle[d] = lst

    used = defaultdict(int)

    def next_task(d, scenario=None):
        lst = task_cycle[d]
        fitting = [t for t in lst if scenario in F_AFFINITY.get(t, [])] if scenario else []
        pool = fitting or lst
        t = min(pool, key=lambda t: (used[t], lst.index(t)))
        used[t] += 1
        return t

    items = []
    if ex["scenarios"]:
        drawn = sorted(rng.sample(list(ex["scenarios"]), 4))
        per = ex["items"] // 4
        cap = {s: per for s in drawn}
        alloc = {s: [] for s in drawn}
        order = sorted(targets, key=lambda d: (sum(d in ex["scenarios"][s][1] for s in drawn), -targets[d]))
        for d in order:
            for _ in range(targets[d]):
                hosts = [s for s in drawn if cap[s] > 0 and d in ex["scenarios"][s][1]]
                hosts = hosts or [s for s in drawn if cap[s] > 0]
                best = max(cap[s] for s in hosts)
                s = rng.choice([h for h in hosts if cap[h] == best])
                cap[s] -= 1
                alloc[s].append(d)
        for s in drawn:
            block = alloc[s]
            rng.shuffle(block)
            for d in block:
                typ, key = key_for(rng)
                items.append({"task": next_task(d, s), "scenario": s, "type": typ, "key": key})
        title_extra = "Scenarios: " + ", ".join(f"{s} {ex['scenarios'][s][0]}" for s in drawn)
    else:
        doms = [d for d, n in targets.items() for _ in range(n)]
        rng.shuffle(doms)
        for d in doms:
            typ, key = key_for(rng)
            items.append({"task": next_task(d), "scenario": "-", "type": typ, "key": key})
        title_extra = "Standalone items"
    session = dt.datetime.now().strftime("%Y%m%d-%H%M") + f"-{a.exam}"
    counts = ", ".join(f"D{d} {n}" for d, n in targets.items())
    title = f"Mock plan · {ex['name']} · session {session} · {len(items)} items ({counts})"
    if a.save and not a.out:
        a.out = str(MOCKS / session)
    if a.out:
        out = Path(a.out)
        out.mkdir(parents=True, exist_ok=True)
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            print_items(a.exam, items, title)
            print(f"\n{title_extra}")
        (out / "plan.md").write_text(buf.getvalue())
        (out / "answers.md").write_text(f"# Answers · session {session}\n\n")
        print(f"session: {session}\nfolder: {out}\nplan written to {out / 'plan.md'}; answers file created")
    else:
        print(f"session: {session}")
        print_items(a.exam, items, title)
        print(f"\n{title_extra}")


def cmd_labs(a):
    labs = lab_status()
    if not labs:
        print("No labs started yet.")
    for n, s in labs:
        print(f"- {n}: {s}")


def cmd_undo(a):
    if not LOG.exists():
        die("no log yet")
    lines = LOG.read_text().splitlines()
    for i in range(len(lines) - 1, -1, -1):
        try:
            row = json.loads(lines[i])
        except json.JSONDecodeError:
            continue
        if row.get("exam") == a.exam:
            removed = lines.pop(i)
            LOG.write_text("\n".join(lines) + ("\n" if lines else ""))
            print(f"removed: {removed}")
            return
    die(f"no entries for exam {a.exam}")


def cmd_import(a):
    src = Path(a.file)
    if not src.exists():
        die(f"file not found: {src}")
    valid = set(all_tasks(a.exam))
    rows, errors = [], []
    for n, line in enumerate(src.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError as e:
            errors.append(f"line {n}: bad JSON ({e.msg})")
            continue
        t, res = r.get("task"), r.get("result")
        if t not in valid:
            errors.append(f"line {n}: unknown task {t!r}")
        elif res not in ("correct", "wrong"):
            errors.append(f"line {n}: result must be correct or wrong")
        elif r.get("confidence") not in (None, "high", "medium", "low"):
            errors.append(f"line {n}: bad confidence {r.get('confidence')!r}")
        else:
            row = {"ts": now(), "exam": a.exam, "source": a.source, "task": t,
                   "domain": domain_of(t), "correct": res == "correct"}
            for k in ("confidence", "lesson", "doc"):
                if r.get(k):
                    row[k] = r[k]
            if r.get("scenario") in EXAMS[a.exam]["scenarios"]:
                row["scenario"] = r["scenario"]
            if a.session:
                row["session"] = a.session
            rows.append(row)
    if errors:
        die("nothing imported; fix these lines first:\n  " + "\n  ".join(errors))
    for row in rows:
        append(row)
    c = sum(r["correct"] for r in rows)
    print(f"imported {len(rows)} items ({c} correct) into {a.exam} as {a.source}"
          + (f", session {a.session}" if a.session else ""))


# ---------------------------------------------------------------- rotation and review queue

def rotation_rows():
    if not ROTATION.exists():
        return []
    return [json.loads(line) for line in ROTATION.read_text().splitlines() if line.strip()]


def current_day(rows):
    """Study days, not calendar days: a new day starts the first time the rotation is touched on a new date."""
    if not rows:
        return 1
    return rows[-1]["day"] if rows[-1]["date"] == today().isoformat() else rows[-1]["day"] + 1


def day_parts(n):
    """Deep-dive scenario, overview scenario (None after the first cycle), and review set for day n."""
    k = len(ORDER)
    return ORDER[(n - 1) % k], (ORDER[n] if n < k else None), ORDER[:min(n + 1, k)]


def day_status(rows, n):
    """Parts recorded for day n, from the trailing run of rows for that day."""
    out = {}
    for r in reversed(rows):
        if r["day"] != n:
            break
        if r["part"] != "start":
            out.setdefault(r["part"], r.get("status", "done"))
    return out


def load_queue():
    return json.loads(QUEUE.read_text()) if QUEUE.exists() else []


def save_queue(q):
    QUEUE.parent.mkdir(parents=True, exist_ok=True)
    tmp = QUEUE.with_suffix(".tmp")
    tmp.write_text(json.dumps(q, indent=1, ensure_ascii=False) + "\n")
    tmp.replace(QUEUE)
    write_notebook(q)


def find_entry(q, eid):
    for e in q:
        if e["id"] == eid:
            return e
    die(f"no queue entry {eid}")


def write_notebook(q):
    names = EXAMS["F"]["scenarios"]
    lines = ["# Notebook", "",
             f"Generated by `scripts/cca.py` on {today()}. Don't edit it by hand. Answers are left out, "
             "so you can quiz yourself from it. `/cca-day questions` walks through it with you.", ""]
    active = [e for e in q if e["status"] == "active"]
    sections = [
        ("open", "Open questions to carry",
         "Specific things you haven't settled yet. Each comes up in quick review, and the scenario's next "
         "deep dive starts with the ones tied to an item."),
        ("pre", "Pre-questions for upcoming deep dives",
         "From an overview. Think about them before the deep dive; its wrap-up settles them."),
        ("recall", "In review", "Worked back in a deep dive. Reviewed until solid."),
    ]
    for kind, title, blurb in sections:
        es = [e for e in active if e["kind"] == kind]
        if not es:
            continue
        lines += [f"## {title} ({len(es)})", "", blurb, ""]
        for s in ORDER:
            se = [e for e in es if e["scenario"] == s]
            if not se:
                continue
            lines.append(f"### {s} {names[s][0]}")
            for e in se:
                extra = ([f"from {e['ref']}"] if e.get("ref") else []) + \
                        ([f"next review {e['due']}"] if kind != "pre" else [])
                lines.append(f"- **{e['id']}** {e['prompt']}" + (f" _({'; '.join(extra)})_" if extra else ""))
            lines.append("")
    solid = [e for e in q if e["status"] == "solid"]
    if solid:
        lines += [f"## Solid ({len(solid)})", ""] + [f"- {e['id']} {e['prompt']}" for e in solid] + [""]
    NOTEBOOK.write_text("\n".join(lines))


def guide_block_state(s):
    """Completed guide-block sessions for scenario s, and pause files with no results yet."""
    done = sorted({r["session"] for r in practice_rows(load("F"))
                   if r.get("scenario") == s and r.get("session", "").startswith(f"{s}-block")})
    paused = []
    if SCEN_PROGRESS.exists():
        paused = sorted(p.name for p in SCEN_PROGRESS.glob(f"{s}-block-*.md")
                        if not p.with_suffix(".jsonl").exists())
    return done, paused


def cmd_day(a):
    rows = rotation_rows()
    t = today().isoformat()
    if a.mark:
        n = current_day(rows)
        deep, ov, rev = day_parts(n)
        if a.mark == "overview" and not ov:
            die(f"day {n} has no overview")
        sc = {"deep": deep, "overview": ov, "review": ",".join(rev)}[a.mark]
        status = "partial" if a.partial else "done"
        ROTATION.parent.mkdir(parents=True, exist_ok=True)
        with ROTATION.open("a") as f:
            f.write(json.dumps({"ts": now(), "date": t, "day": n, "part": a.mark, "scenario": sc,
                                "status": status}) + "\n")
        print(f"day {n}: {a.mark} {sc} marked {status}")
        return
    if a.set or a.advance:
        n = a.set or current_day(rows) + (1 if rows and rows[-1]["date"] == t else 0)
        if n < 1:
            die("day must be 1 or more")
        ROTATION.parent.mkdir(parents=True, exist_ok=True)
        with ROTATION.open("a") as f:
            f.write(json.dumps({"ts": now(), "date": t, "day": n, "part": "start"}) + "\n")
        rows = rotation_rows()

    n = current_day(rows)
    deep, ov, rev = day_parts(n)
    names = EXAMS["F"]["scenarios"]
    status = day_status(rows, n)
    q = load_queue()
    active = [e for e in q if e["status"] == "active"]

    deep_dived = set(ORDER[:n])
    rev_min = sum(3 if s in deep_dived else 1 for s in rev)
    ov_min = 15 if ov else 0
    deep_min = a.minutes - rev_min - ov_min

    done, paused = guide_block_state(deep)
    leftovers = [e["id"] for e in active if e["scenario"] == deep and e["kind"] == "open" and e.get("ref")]
    pre = [e["id"] for e in active if e["scenario"] == deep and e["kind"] == "pre"]
    if paused:
        plan = f"resume the paused guide block (progress/scenarios/{paused[-1]})"
    elif not done:
        plan = f"guide block: scenarios/{FOLDERS[deep]}/exam.md"
    else:
        plan = (f"{len(leftovers)} leftover(s) first ({', '.join(leftovers)}), then " if leftovers else "") + \
               "a fresh block"
    if pre:
        plan += f" · settle {len(pre)} pre-question(s) in the wrap-up"
    if status.get("deep"):
        plan = f"next {deep} deep dive (day {n + len(ORDER)}): {plan}"
    due = [e for e in active if e["kind"] != "pre" and e["due"] <= t and e["scenario"] in rev]
    shown = sum(min(a.per, sum(e["scenario"] == s for e in due)) for s in rev)
    ov_only = [s for s in rev if s not in deep_dived]

    print(f"## Rotation · day {n} · cycle {(n - 1) // len(ORDER) + 1} · {t} · {a.minutes} min")
    print("| Part | Scenario | Min | Plan | Status |")
    print("|---|---|---|---|---|")
    print(f"| 1. Deep dive | {deep} {names[deep][0]} | {deep_min} | {plan} | {status.get('deep', '–')} |")
    if ov:
        print(f"| 2. Overview | {ov} {names[ov][0]} | {ov_min} | `cca.py overview {ov}`: frame, families, "
              f"3 pre-questions. No items | {status.get('overview', '–')} |")
    rev_plan = f"{shown} of {len(due)} due (cap {a.per} per scenario)"
    if ov_only:
        rev_plan += f" · {', '.join(ov_only)}: overview recall only"
    print(f"| 3. Quick review | {' '.join(rev)} | {rev_min} | {rev_plan} | {status.get('review', '–')} |")
    if deep_min < 30:
        print(f"\nOnly {deep_min} min left for the deep dive. Enough to sit the block; the work-back will be short.")
    if rows and rows[-1]["day"] != n:
        prev = rows[-1]["day"]
        pdeep, pov, _ = day_parts(prev)
        pst = day_status(rows, prev)
        missing = [p for p, s in (("deep dive " + pdeep, "deep"), (f"overview {pov}", "overview"),
                                  ("review", "review")) if (s != "overview" or pov) and pst.get(s) != "done"]
        if missing:
            print(f"\nDay {prev} left unfinished: {', '.join(missing)}. "
                  f"`cca.py day --set {prev}` goes back to it; otherwise the rotation moves on.")
    nd, nov, _ = day_parts(n + 1)
    print(f"\nNext study day: day {n + 1} · deep dive {nd}" + (f" · overview {nov}" if nov else ""))
    n_open = sum(e["kind"] == "open" for e in active)
    n_pre = sum(e["kind"] == "pre" for e in active)
    if n_open or n_pre:
        print(f"Carrying: {n_open} open question(s), {n_pre} pre-question(s). See progress/notebook.md.")


def cmd_overview(a):
    s = a.scenario
    if s not in FOLDERS:
        die(f"unknown scenario {s}")
    folder = ROOT / "scenarios" / FOLDERS[s]
    exam = (folder / "exam.md").read_text().splitlines()
    ans = (folder / "answers.md").read_text().splitlines()

    def block(lines, prefix):
        try:
            k = next(k for k, line in enumerate(lines) if line.startswith(prefix)) + 1
        except StopIteration:
            die(f"'{prefix}' not found in {folder.name}")
        out = []
        for line in lines[k:]:
            if out and not line.strip():
                break
            if line.strip():
                out.append(line)
        return out

    k = exam.index("## Scenario") + 1
    frame = []
    for line in exam[k:]:
        if line.strip() == "---":
            break
        frame.append(line)
    fam = block(ans, "### Question families")
    cells = [r.strip().strip("|").split("|") for r in fam]
    drop = [c.strip() for c in cells[0]].index("Deciding rule")
    if any(len(c) != len(cells[0]) for c in cells):
        die(f"question-families table in {folder.name} has a stray '|'; fix the table")
    tension = re.match(r"\*\*(.+?)\*\*", block(ans, "### The tension")[0])

    print(f"## {s} {EXAMS['F']['scenarios'][s][0]} · overview")
    print("A map, not answers: no exam items, no keys, and the families' deciding rules are held back.\n")
    print("### Frame\n" + "\n".join(frame).strip() + "\n")
    print("### What the frame puts in play")
    print("\n".join(block(ans, "### What the frame tells you")) + "\n")
    print("### Question families (deciding rules held back for the deep dive)")
    for c in cells:
        print("|" + "|".join(x for i, x in enumerate(c) if i != drop) + "|")
    if tension:
        print(f"\n### The question {s} is built around\n{tension.group(1)}")


def cmd_queue(a):
    q = load_queue()
    t = today()

    if a.qcmd == "add":
        if a.scenario not in FOLDERS:
            die(f"unknown scenario {a.scenario}")
        if a.task and a.task not in all_tasks("F"):
            die(f"unknown task {a.task}")
        if a.kind == "recall" and not a.answer:
            die("a recall entry needs --answer (the rule it checks)")
        n = 1 + sum(e["scenario"] == a.scenario for e in q)
        e = {"id": f"{a.scenario}-{n:02d}", "scenario": a.scenario, "kind": a.kind, "prompt": a.prompt,
             "added": t.isoformat(), "box": 0, "due": t.isoformat(), "status": "active", "history": []}
        for k in ("answer", "task", "ref"):
            if getattr(a, k):
                e[k] = getattr(a, k)
        q.append(e)
        save_queue(q)
        print(f"added {e['id']} ({a.kind})" + ("" if a.answer or a.kind == "pre" else
                                                " · no answer stored, so review feedback will need the source"))

    elif a.qcmd == "due":
        sc = a.scenarios.split(",") if a.scenarios else day_parts(current_day(rotation_rows()))[2]
        due = [e for e in q if e["status"] == "active" and e["kind"] != "pre"
               and e["due"] <= t.isoformat() and e["scenario"] in sc]
        by = {s: sorted((e for e in due if e["scenario"] == s),
                        key=lambda e: (e["due"], e["box"], e["added"]))[:a.per] for s in sc}
        picked = [by[s][i] for i in range(a.per) for s in sc if i < len(by[s])]
        print(f"## Quick review · {t} · {len(picked)} of {len(due)} due · {' '.join(sc)}")
        if picked:
            print("| # | ID | Kind | Box | Prompt |")
            print("|---|---|---|---|---|")
            for i, e in enumerate(picked, 1):
                print(f"| {i} | {e['id']} | {e['kind']} | {e['box']} | {e['prompt']} |")
        empty = [s for s in sc if not any(e["scenario"] == s and e["status"] == "active" and e["kind"] != "pre"
                                          for e in q)]
        if empty:
            print(f"\nNo review entries yet for {', '.join(empty)}. For each, recall the frame's key constraint "
                  "and the question the scenario is built around (`cca.py overview <S#>`).")
        if len(due) > len(picked):
            print(f"\n{len(due) - len(picked)} more due. The oldest come first next time.")

    elif a.qcmd == "show":
        print(json.dumps(find_entry(q, a.id), indent=1, ensure_ascii=False))

    elif a.qcmd == "mark":
        e = find_entry(q, a.id)
        if e["status"] != "active" or e["kind"] == "pre":
            die(f"{a.id} is {e['status']} {e['kind']}; only active recall or open entries are reviewed")
        if a.result == "wrong":
            e["box"], e["due"] = 0, (t + dt.timedelta(days=1)).isoformat()
            msg = "back to daily review"
        elif any(d == t.isoformat() and r == "right" for d, r in e["history"]):
            msg = "already moved up today; one step per day"
        elif e["box"] >= len(STEPS):
            e["status"] = "solid"
            msg = "solid: leaves the review queue"
        else:
            e["due"] = (t + dt.timedelta(days=STEPS[e["box"]])).isoformat()
            e["box"] += 1
            msg = f"box {e['box']}, next review {e['due']}"
        e["history"].append([t.isoformat(), a.result])
        save_queue(q)
        print(f"{a.id} {a.result}: {msg}")

    elif a.qcmd == "update":
        e = find_entry(q, a.id)
        if a.kind and a.kind != e["kind"]:
            if a.kind == "recall" and e["kind"] in ("open", "pre"):
                e["resolved"] = t.isoformat()
            if e["kind"] == "pre":
                e["due"] = t.isoformat()
            e["kind"] = a.kind
        for k in ("prompt", "answer", "ref", "task"):
            if getattr(a, k):
                e[k] = getattr(a, k)
        if e["kind"] == "recall" and not e.get("answer"):
            die("a recall entry needs --answer (the rule it checks)")
        save_queue(q)
        print(f"updated {a.id} ({e['kind']})")

    elif a.qcmd == "drop":
        find_entry(q, a.id)["status"] = "dropped"
        save_queue(q)
        print(f"dropped {a.id}")

    elif a.qcmd == "list":
        es = [e for e in q if (a.all or e["status"] == "active")
              and (not a.scenario or e["scenario"] == a.scenario) and (not a.kind or e["kind"] == a.kind)]
        if not es:
            print("No matching queue entries.")
            return
        print("| ID | Kind | Status | Box | Due | Ref | Prompt |")
        print("|---|---|---|---|---|---|---|")
        for e in es:
            print(f"| {e['id']} | {e['kind']} | {e['status']} | {e['box']} | {e['due']} "
                  f"| {e.get('ref', '')} | {e['prompt']} |")


# ---------------------------------------------------------------- journal and dashboard

def journal_rows():
    if not JOURNAL.exists():
        return []
    return [json.loads(line) for line in JOURNAL.read_text().splitlines() if line.strip()]


def cmd_journal(a):
    if a.jcmd == "add":
        date = a.date or today().isoformat()
        try:
            dt.date.fromisoformat(date)
        except ValueError:
            die(f"bad --date {date!r}; use YYYY-MM-DD")
        row = {"ts": now(), "date": date, "kind": a.kind, "text": a.text}
        if a.minutes:
            row["minutes"] = a.minutes
        JOURNAL.parent.mkdir(parents=True, exist_ok=True)
        with JOURNAL.open("a") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"journal: {date} {a.kind}" + (f" ({a.minutes} min)" if a.minutes else ""))
        return
    rows = journal_rows()[-a.n:]
    if not rows:
        print("Journal is empty.")
    for r in rows:
        mins = f" · {r['minutes']} min" if r.get("minutes") else ""
        print(f"- {r['date']} [{r['kind']}{mins}] {r['text']}")


def cmd_dashboard(a):
    import dashboard  # scripts/dashboard.py, next to this file
    path = dashboard.build(a.exam, a.out)
    print(f"dashboard written to {path}")
    if a.open:
        dashboard.open_file(path)


# Commands after which the dashboard is rebuilt, so its Refresh button (a reload) shows the change.
# `day` changes nothing on its own, but it starts each study day, which updates what's due.
REFRESH = {"log", "external", "undo", "import", "day", "queue", "journal"}


def refresh_dashboard():
    """Rebuild progress/dashboard.html (and the Professional one, if it exists). Never fails the command."""
    try:
        import dashboard
        dashboard.build("F")
        if dashboard.out_path("P").exists():
            dashboard.build("P")
    except Exception as e:  # a dashboard bug mustn't block logging
        print(f"(dashboard not refreshed: {e})", file=sys.stderr)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    def exam_arg(sp):
        sp.add_argument("--exam", choices=["F", "P"], required=True)

    s = sub.add_parser("log")
    exam_arg(s)
    s.add_argument("--source", choices=SOURCES, required=True)
    s.add_argument("--task", required=True)
    s.add_argument("--result", choices=["correct", "wrong"], required=True)
    s.add_argument("--confidence", choices=["high", "medium", "low"])
    s.add_argument("--scenario")
    s.add_argument("--lesson")
    s.add_argument("--doc")
    s.add_argument("--session")
    s.set_defaults(fn=cmd_log)

    s = sub.add_parser("external")
    exam_arg(s)
    s.add_argument("--label", required=True)
    s.add_argument("--correct", type=int, required=True)
    s.add_argument("--total", type=int, required=True)
    s.add_argument("--domain")
    s.set_defaults(fn=cmd_external)

    s = sub.add_parser("stats")
    exam_arg(s)
    s.set_defaults(fn=cmd_stats)

    s = sub.add_parser("missed")
    exam_arg(s)
    s.add_argument("--task")
    s.set_defaults(fn=cmd_missed)

    s = sub.add_parser("draw")
    exam_arg(s)
    g = s.add_mutually_exclusive_group(required=True)
    g.add_argument("--quiz", type=int, metavar="N")
    g.add_argument("--diagnostic", action="store_true")
    g.add_argument("--mock", action="store_true")
    s.add_argument("--domain")
    s.add_argument("--task")
    s.add_argument("--scenario")
    s.add_argument("--review", action="store_true")
    s.add_argument("--out", help="folder for plan.md (mock only)")
    s.add_argument("--save", action="store_true", help="mock only: save to progress/mocks/<session>/")
    s.add_argument("--seed", type=int)
    s.set_defaults(fn=cmd_draw)

    s = sub.add_parser("undo")
    exam_arg(s)
    s.set_defaults(fn=cmd_undo)

    s = sub.add_parser("import")
    exam_arg(s)
    s.add_argument("--source", choices=SOURCES, required=True)
    s.add_argument("--session")
    s.add_argument("--file", required=True)
    s.set_defaults(fn=cmd_import)

    s = sub.add_parser("labs")
    s.add_argument("--list", action="store_true")
    s.set_defaults(fn=cmd_labs)

    s = sub.add_parser("day")
    s.add_argument("--minutes", type=int, default=90)
    s.add_argument("--per", type=int, default=3, help="review items per scenario")
    g = s.add_mutually_exclusive_group()
    g.add_argument("--mark", choices=["deep", "overview", "review"])
    g.add_argument("--set", type=int, metavar="N", help="make today rotation day N")
    g.add_argument("--advance", action="store_true", help="start the next rotation day today")
    s.add_argument("--partial", action="store_true")
    s.set_defaults(fn=cmd_day)

    s = sub.add_parser("overview")
    s.add_argument("scenario")
    s.set_defaults(fn=cmd_overview)

    s = sub.add_parser("queue")
    qs = s.add_subparsers(dest="qcmd", required=True)
    x = qs.add_parser("add")
    x.add_argument("--scenario", required=True)
    x.add_argument("--kind", choices=KINDS, required=True)
    x.add_argument("--prompt", required=True)
    for k in ("--answer", "--task", "--ref"):
        x.add_argument(k)
    x = qs.add_parser("due")
    x.add_argument("--scenarios", help="comma-separated; default: today's review set")
    x.add_argument("--per", type=int, default=3)
    for name in ("show", "drop"):
        qs.add_parser(name).add_argument("id")
    x = qs.add_parser("mark")
    x.add_argument("id")
    x.add_argument("--result", choices=["right", "wrong"], required=True)
    x = qs.add_parser("update")
    x.add_argument("id")
    x.add_argument("--kind", choices=KINDS)
    for k in ("--prompt", "--answer", "--ref", "--task"):
        x.add_argument(k)
    x = qs.add_parser("list")
    x.add_argument("--scenario")
    x.add_argument("--kind", choices=KINDS)
    x.add_argument("--all", action="store_true")
    s.set_defaults(fn=cmd_queue)

    s = sub.add_parser("journal")
    js = s.add_subparsers(dest="jcmd", required=True)
    x = js.add_parser("add")
    x.add_argument("--kind", choices=["session", "milestone", "note"], required=True)
    x.add_argument("--text", required=True)
    x.add_argument("--minutes", type=int)
    x.add_argument("--date")
    x = js.add_parser("list")
    x.add_argument("--n", type=int, default=10)
    s.set_defaults(fn=cmd_journal)

    s = sub.add_parser("dashboard")
    s.add_argument("--exam", choices=["F", "P"], default="F")
    s.add_argument("--out")
    s.add_argument("--open", action="store_true")
    s.set_defaults(fn=cmd_dashboard)

    a = p.parse_args()
    a.fn(a)
    if a.cmd in REFRESH:
        refresh_dashboard()


if __name__ == "__main__":
    main()
