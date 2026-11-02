#!/usr/bin/env python3
"""Build a self-contained HTML dashboard of study progress from the files in progress/.

Standard library only. Reads what the tracker writes (log.jsonl, rotation.jsonl, queue.json,
journal.jsonl, plan.md) and writes one HTML file that makes no network requests.

  python3 scripts/dashboard.py [--exam F|P] [--out FILE] [--open]
  python3 scripts/cca.py dashboard [--exam F] [--open]     # same thing; pre-approved in the skills

Default output: progress/dashboard.html (progress/dashboard-P.html for Professional).
Colors are the dataviz reference palette; the heatmap ramp was checked with its validator (--ordinal).
"""
import argparse
import datetime as dt
import html
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cca  # noqa: E402

E = html.escape
TARGET = 75  # accuracy line on the bar and trend charts; matches the readiness checklist


def out_path(exam, out=None):
    return Path(out) if out else cca.ROOT / "progress" / ("dashboard.html" if exam == "F" else "dashboard-P.html")


def open_file(path):
    opener = {"darwin": ["open"], "win32": ["cmd", "/c", "start", ""]}.get(sys.platform, ["xdg-open"])
    subprocess.run(opener + [str(path)], check=False)


def pct(c, n):
    return round(100 * c / n) if n else None


def exam_date():
    p = cca.ROOT / "progress" / "plan.md"
    if not p.exists():
        return None
    m = re.search(r"Exam date:\**\s*(\d{4}-\d{2}-\d{2})", p.read_text())
    return dt.date.fromisoformat(m.group(1)) if m else None


# ---------------------------------------------------------------- building blocks

def card(title, body, sub="", table="", wide=False):
    tv = f'<details class="tv"><summary>Table view</summary>{table}</details>' if table else ""
    s = f'<p class="sub">{E(sub)}</p>' if sub else ""
    return f'<section class="card{" wide" if wide else ""}"><h2>{E(title)}</h2>{s}{body}{tv}</section>'


def table(headers, rows, num=()):
    th = "".join(f'<th{" class=num" if i in num else ""}>{E(h)}</th>' for i, h in enumerate(headers))
    trs = "".join("<tr>" + "".join(f'<td{" class=num" if i in num else ""}>{E(str(c))}</td>'
                                    for i, c in enumerate(r)) + "</tr>" for r in rows)
    return f'<div class="tbl"><table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>'


def empty(msg):
    return f'<p class="empty">{E(msg)}</p>'


def tile(label, value, sub="", delta=None):
    d = ""
    if delta:
        up = delta > 0
        d = f'<span class="delta {"up" if up else "down"}">{"▲" if up else "▼"} {abs(delta)} pts</span> '
    return (f'<div class="tile"><div class="tile-label">{E(label)}</div>'
            f'<div class="tile-value">{E(str(value))}</div><div class="tile-sub">{d}{E(sub)}</div></div>')


def bars(items):
    """Horizontal accuracy bars. items: (label, sub, value or None, tooltip)."""
    rows = []
    for label, sub, v, tip in items:
        bar = f'<span class="bar" style="--v:{v}"></span>' if v else ""
        val = (f'<span class="bar-val" style="--v:{v}">{v}%</span>' if v is not None
               else '<span class="bar-val none" style="--v:0">no items yet</span>')
        rows.append(f'<div class="bar-row" tabindex="0" data-tip="{E(tip)}">'
                    f'<div class="bar-label">{E(label)} <span class="muted">{E(sub)}</span></div>'
                    f'<div class="bar-track"><span class="bar-target"></span>{bar}{val}</div></div>')
    return ('<div class="bars">' + "".join(rows) + '</div>'
            f'<p class="note"><span class="key-target"></span>{TARGET}% target</p>')


# ---------------------------------------------------------------- sections

def kpis(exam, prac, days, journal, q, rot):
    last7 = (cca.today() - dt.timedelta(days=6)).isoformat()
    recent = prac[-30:]
    prev = prac[-60:-30]
    acc = pct(sum(r["correct"] for r in recent), len(recent))
    delta = acc - pct(sum(r["correct"] for r in prev), len(prev)) if acc is not None and len(prev) >= 10 else None
    ex = cca.EXAMS[exam]
    w_sum = w_tot = 0
    for d, (_, w) in ex["domains"].items():
        dr = [r["correct"] for r in prac if r["domain"] == d]
        if dr:
            w_sum += w * sum(dr) / len(dr)
            w_tot += w
    minutes = sum(j.get("minutes", 0) for j in journal if j["kind"] == "session")
    tiles = [
        tile("Study days", len(days), f"{minutes} min logged" if minutes else
             (f"since {min(days)}" if days else "none yet")),
        tile("Practice items", len(prac), f"{sum(r['ts'][:10] >= last7 for r in prac)} in the last 7 days"),
        tile("Accuracy", f"{acc}%" if acc is not None else "–",
             ("vs previous 30" if delta else f"last {len(recent)} items") if prac else "no items yet", delta),
        tile("Blueprint-weighted", f"{round(100 * w_sum / w_tot)}%" if w_tot else "–",
             "practice estimate, not a scaled score"),
    ]
    if exam == "F":
        n = cca.current_day(rot)
        started = bool(rot) and rot[-1]["date"] == cca.today().isoformat()
        deep = cca.day_parts(n)[0]
        tiles.append(tile("Rotation", f"Day {n}", f"{'today' if started else 'next'}: {deep} deep dive · "
                          f"cycle {(n - 1) // len(cca.ORDER) + 1}"))
        act = [e for e in q if e["status"] == "active"]
        due = sum(e["kind"] != "pre" and e["due"] <= cca.today().isoformat() for e in act)
        solid = sum(e["status"] == "solid" for e in q)
        in_rev = sum(e["kind"] != "pre" for e in act)
        tiles.append(tile("Review queue", f"{solid} solid",
                          f"{in_rev} in review · {due} due · {sum(e['kind'] == 'open' for e in act)} open"))
    return '<div class="kpis">' + "".join(tiles) + "</div>"


def domains_card(exam, prac):
    ex = cca.EXAMS[exam]
    items, rows = [], []
    for d, (name, w) in ex["domains"].items():
        dr = [r["correct"] for r in prac if r["domain"] == d]
        last = dr[-20:]
        v = pct(sum(last), len(last))
        tip = (f"D{d} {name} · weight {w}% · " +
               (f"last {len(last)}: {sum(last)}/{len(last)} · all-time {sum(dr)}/{len(dr)} ({pct(sum(dr), len(dr))}%)"
                if dr else "no items yet"))
        items.append((f"D{d} {name}", f"{w}%", v, tip))
        rows.append([f"D{d} {name}", f"{w}%", len(dr), f"{pct(sum(dr), len(dr))}%" if dr else "–",
                     f"{v}%" if v is not None else "–"])
    return card("Domains", bars(items), "Accuracy over each domain's last 20 items. The exam is scored by domain.",
                table(["Domain", "Weight", "Items", "All-time", "Last 20"], rows, num=(1, 2, 3, 4)))


def scenarios_card(prac, q, rot):
    names = cca.EXAMS["F"]["scenarios"]
    items, rows = [], []
    for s in cca.ORDER:
        sr = [r for r in prac if r.get("scenario") == s]
        last = [r["correct"] for r in sr[-15:]]
        v = pct(sum(last), len(last))
        done, _ = cca.guide_block_state(s)
        block = "not started"
        if done:
            res = [r["correct"] for r in sr if r.get("session") == done[-1]]
            block = f"{sum(res)}/{len(res)}"
        dives = len({r["day"] for r in rot if r["part"] == "deep" and r.get("scenario") == s})
        tip = (f"{s} {names[s][0]} · guide block {block} · deep dives {dives} · " +
               (f"last {len(last)}: {sum(last)}/{len(last)}" if sr else "no items yet"))
        items.append((f"{s} {names[s][0]}", f"block {block}", v, tip))
        rows.append([f"{s} {names[s][0]}", len(sr), f"{v}%" if v is not None else "–", block, dives])
    return card("Scenarios", bars(items),
                "Accuracy over each scenario's last 15 items. Any 4 of the 6 can appear, so all six need to clear the line.",
                table(["Scenario", "Items", "Last 15", "Guide block", "Deep dives"], rows, num=(1, 2, 4)))


def heatmap_card(exam, rows):
    ex = cca.EXAMS[exam]
    ts = cca.task_stats(rows, exam)
    out, trows = ['<div class="heat">'], []
    for d, (name, w) in ex["domains"].items():
        cells = []
        for t in ex["tasks"][d]:
            c, n, tot = ts[t]
            b = 0 if n == 0 else (1 if c / n < .5 else 2 if c / n < .75 else 3 if c / n < .9 else 4)
            tip = (f"{t} · not attempted yet" if tot == 0
                   else f"{t} · last {n}: {c}/{n} ({pct(c, n)}%) · {tot} attempts in all")
            cells.append(f'<span class="cell b{b}" tabindex="0" data-tip="{E(tip)}">{E(t)}</span>')
            trows.append([t, f"D{d}", f"{c}/{n}" if n else "–", f"{pct(c, n)}%" if n else "–", tot])
        out.append(f'<div class="heat-row"><span class="heat-label" title="{E(name)}">D{d} '
                   f'<span class="muted">{w}%</span></span><span class="heat-cells">{"".join(cells)}</span></div>')
    out.append("</div>")
    legend = "".join(f'<span class="lg"><span class="sw b{b}"></span>{E(lbl)}</span>' for b, lbl in
                     [(0, "not yet"), (1, "under 50%"), (2, "50–74%"), (3, "75–89%"), (4, "90% and up")])
    out.append(f'<div class="legend">{legend}</div>')
    return card("Objectives", "".join(out),
                "Each task statement, shaded by accuracy over its last 10 items. Hover a cell for counts.",
                table(["Objective", "Domain", "Last 10", "Accuracy", "All attempts"], trows, num=(2, 3, 4)),
                wide=True)


def trend_card(prac):
    n = len(prac)
    if n < 2:
        return card("Accuracy trend", empty("The trend appears after your first few practice items."))
    W, H, L, R, T, B = 480, 230, 34, 40, 10, 26
    pts = []
    for i in range(n):
        win = prac[max(0, i - 19):i + 1]
        pts.append(100 * sum(r["correct"] for r in win) / len(win))

    def x(i):
        return L + (W - L - R) * i / (n - 1)

    def y(v):
        return T + (H - T - B) * (1 - v / 100)

    g = []
    for v in (0, 25, 50, 75, 100):
        cls = "axis" if v == 0 else "grid"
        g.append(f'<line class="{cls}" x1="{L}" x2="{W - R}" y1="{y(v):.1f}" y2="{y(v):.1f}"/>'
                 f'<text class="tick" x="{L - 6}" y="{y(v) + 4:.1f}" text-anchor="end">{v}%</text>')
    g.append(f'<line class="target" x1="{L}" x2="{W - R}" y1="{y(TARGET):.1f}" y2="{y(TARGET):.1f}"/>')
    for i in sorted({0, (n - 1) // 2, n - 1}):
        g.append(f'<text class="tick" x="{x(i):.1f}" y="{H - 8}" text-anchor="middle">{i + 1}</text>')
    path = "M" + " L".join(f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(pts))
    ex, ey = x(n - 1), y(pts[-1])
    data = [{"x": round(x(i), 1), "y": round(y(v), 1),
             "t": f"Item {i + 1} · {r['ts'][:10]} · rolling 20: {round(v)}% · this item: "
                  f"{'right' if r['correct'] else 'wrong'} ({r['task']}{', ' + r['scenario'] if r.get('scenario') else ''})"}
            for i, (v, r) in enumerate(zip(pts, prac))]
    svg = (f'<svg class="trend" viewBox="0 0 {W} {H}" role="img" aria-label="Rolling accuracy over the last 20 items" '
           f'data-points="{E(json.dumps(data))}">{"".join(g)}'
           f'<path class="line" d="{path}"/><circle class="end" cx="{ex:.1f}" cy="{ey:.1f}" r="4"/>'
           f'<text class="endlabel" x="{ex + 8:.1f}" y="{ey - 6:.1f}">{round(pts[-1])}%</text>'
           f'<line class="cross" y1="{T}" y2="{H - B}" x1="-10" x2="-10"/><circle class="hover-dot" r="4" cx="-10" cy="-10"/>'
           f'<rect class="hit" x="{L}" y="{T}" width="{W - L - R}" height="{H - T - B}"/></svg>'
           f'<p class="note"><span class="key-target"></span>{TARGET}% target · x axis: practice item number</p>')
    trows = [[i + 1, r["ts"][:10], r["task"], r.get("scenario", "–"), "right" if r["correct"] else "wrong",
              f"{round(v)}%"] for i, (v, r) in enumerate(zip(pts, prac))][-40:]
    return card("Accuracy trend", svg, "Rolling accuracy over your last 20 items, item by item.",
                table(["#", "Date", "Objective", "Scenario", "Result", "Rolling 20"], trows, num=(0, 5)))


READY = 80  # readiness line for practice exams: the low end of 3 fresh mocks should clear it


def untaken(out_dir):
    """Tests built but not taken yet. Browser tests link to their page, relative to the dashboard."""
    import bank
    li = []
    for f in bank.open_forms():
        again = f" · retake, attempt {f['attempt']}" if f.get("retake_of") else ""
        what = f"{' '.join(f['scenarios'])}{again} · {len(f['items'])} questions · built {f['created'][:10]}"
        page = cca.ROOT / "progress" / "tests" / f"{f['session']}.html"
        if f.get("format") != "browser":
            what = E(what) + ' <span class="muted">· taken in chat: /cca-mock-exam resume</span>'
        elif page.exists():
            what = (f'<a href="{E(quote(os.path.relpath(page, out_dir)))}" target="_blank" rel="noopener">'
                    f'{E(what)}</a>')
        else:
            what = E(what) + f' <span class="muted">· python3 scripts/practice_test.py open {E(f["session"])}</span>'
        li.append(f'<li>{what} <span class="muted">· /cca-test reopens this before building a new {E(f["scenarios"][0])} test'
                  f'</span></li>')
    return '<h3>Not taken yet</h3><ul class="qs">' + "".join(li) + "</ul>" if li else ""


def practice_card(out_dir):
    import bank  # scripts/bank.py
    forms = bank.graded_forms()
    if not forms:
        return card("Practice exams over time", empty(
            "No practice tests taken yet. Run /cca-test for a 10-question browser test on today's scenario.")
            + untaken(out_dir), wide=True)
    W, H, L, R, T, B = 1000, 260, 44, 16, 12, 30
    n = len(forms)

    def x(i):
        return L + (W - L - R) * ((i + 0.5) / n)

    def y(v):
        return T + (H - T - B) * (1 - v / 100)

    g = []
    for v in (0, 25, 50, 75, 100):
        g.append(f'<line class="{"axis" if v == 0 else "grid"}" x1="{L}" x2="{W - R}" y1="{y(v):.1f}" '
                 f'y2="{y(v):.1f}"/><text class="tick" x="{L - 6}" y="{y(v) + 4:.1f}" text-anchor="end">{v}%</text>')
    g.append(f'<line class="target" x1="{L}" x2="{W - R}" y1="{y(READY):.1f}" y2="{y(READY):.1f}"/>')
    rows = []
    step = max(1, n // 8)
    for i, f in enumerate(forms):
        gr = f["graded"]
        lo, hi = gr["ci"]
        cx, cy = x(i), y(gr["pct"])
        if f.get("retake_of"):
            label = f"{' '.join(f['scenarios'])} retake, attempt {f['attempt']}"
            mark = f'<path class="pt retake" d="M{cx:.1f} {cy - 6:.1f}l6 6-6 6-6-6z"/>'
        else:
            label = "full mock" if f["kind"] == "mock" else f"{' '.join(f['scenarios'])} block"
            mark = (f'<circle class="pt {"mock" if f["kind"] == "mock" else "block"}" cx="{cx:.1f}" cy="{cy:.1f}" '
                    f'r="5"/>')
        tip = f"{gr['date']} · {label} · {gr['correct']}/{gr['n']} = {gr['pct']}% · 95% interval {lo}–{hi}%"
        g.append(f'<g tabindex="0" data-tip="{E(tip)}"><rect class="hitbox" x="{cx - 12:.1f}" y="{T}" width="24" '
                 f'height="{H - T - B}"/><line class="whisker" x1="{cx:.1f}" x2="{cx:.1f}" y1="{y(hi):.1f}" '
                 f'y2="{y(lo):.1f}"/>{mark}</g>')
        if i % step == 0 or i == n - 1:
            g.append(f'<text class="tick" x="{x(i):.1f}" y="{H - 10}" text-anchor="middle">{gr["date"][5:]}</text>')
        rows.append([gr["date"], f["session"], label, f"{gr['correct']}/{gr['n']}", f"{gr['pct']}%", f"{lo}–{hi}%"])
    svg = (f'<svg class="trend" viewBox="0 0 {W} {H}" role="img" aria-label="Practice exam scores with 95% '
           f'intervals">{"".join(g)}</svg>')
    mocks = [f for f in forms if f["kind"] == "mock"][-3:]
    pooled = ""
    if mocks:
        c = sum(f["graded"]["correct"] for f in mocks)
        t = sum(f["graded"]["n"] for f in mocks)
        lo, hi = bank.wilson(c, t)
        verdict = ("clears the readiness line" if 100 * lo >= READY and len(mocks) == 3
                   else "doesn't clear the readiness line yet")
        pooled = (f" Last {len(mocks)} mock{'s' if len(mocks) > 1 else ''} pooled: {round(100 * c / t)}%, "
                  f"interval {round(100 * lo)}–{round(100 * hi)}%: the low end {verdict}.")
    legend = ('<p class="note"><span class="lg"><svg width="12" height="12"><circle class="pt mock" cx="6" cy="6" '
              'r="5"/></svg>full mock</span><span class="lg"><svg width="12" height="12"><circle class="pt block" '
              'cx="6" cy="6" r="4"/></svg>scenario block</span><span class="lg"><svg width="12" height="12"><path '
              'class="pt retake" d="M6 1l5 5-5 5-5-5z"/></svg>retake</span><span class="key-target"></span>'
              f'{READY}% readiness line · bars: 95% interval</p>')
    return card("Practice exams over time", svg + legend + untaken(out_dir),
                "Scores on verified bank questions. The bar shows how much the score could move by chance: "
                "short tests have wide bars. A retake has seen its answers, so it measures what you kept, not "
                "a first try." + pooled,
                table(["Date", "Session", "Kind", "Score", "%", "95% interval"], rows), wide=True)


def calibration_card(prac):
    items, rows = [], []
    for conf, label in (("high", "High"), ("medium", "Medium"), ("low", "Low")):
        cr = [r["correct"] for r in prac if r.get("confidence") == conf]
        v = pct(sum(cr), len(cr))
        items.append((label, f"{len(cr)} items", v,
                       f"{label} confidence · {sum(cr)}/{len(cr)} right" if cr else f"{label} confidence · no items yet"))
        rows.append([label, len(cr), f"{v}%" if v is not None else "–"])
    return card("Confidence calibration", bars(items),
                "How often you're right at each confidence level. High should sit well above the line; "
                "high-confidence misses are listed below.",
                table(["Confidence", "Items", "Right"], rows, num=(1, 2)))


def study_days(prac, rot, journal):
    days = defaultdict(lambda: {"parts": [], "items": 0, "right": 0, "minutes": 0, "day": None})
    for r in prac:
        d = days[r["ts"][:10]]
        d["items"] += 1
        d["right"] += r["correct"]
    for r in rot:
        if r["part"] != "start":
            d = days[r["date"]]
            d["parts"].append(f"{r['part']} {r.get('scenario', '')}".strip() +
                              (" (partial)" if r.get("status") == "partial" else ""))
            d["day"] = r["day"]
    for j in journal:
        if j["kind"] == "session":
            days[j["date"]]["minutes"] += j.get("minutes", 0)
    return dict(days)


def rotation_card(days, rot):
    today = cca.today()
    start = today - dt.timedelta(days=today.weekday() + 7 * 7)
    cols = []
    for w in range(8):
        cells = []
        for k in range(7):
            d = start + dt.timedelta(days=7 * w + k)
            iso = d.isoformat()
            if d > today:
                cells.append('<span class="day future"></span>')
                continue
            info = days.get(iso)
            if info:
                bits = ([f"day {info['day']}"] if info["day"] else []) + info["parts"] + \
                       ([f"{info['items']} items, {info['right']} right"] if info["items"] else []) + \
                       ([f"{info['minutes']} min"] if info["minutes"] else [])
                cells.append(f'<span class="day on" tabindex="0" data-tip="{E(iso + " · " + " · ".join(bits))}"></span>')
            else:
                cells.append(f'<span class="day off" data-tip="{E(iso)} · no study"></span>')
        cols.append('<span class="week">' + "".join(cells) + "</span>")
    cal = ('<div class="cal"><span class="cal-days"><span>Mon</span><span></span><span>Wed</span><span></span>'
           '<span>Fri</span><span></span><span></span></span>' + "".join(cols) + "</div>"
           '<p class="note"><span class="sw on"></span>studied · last 8 weeks</p>')
    by_day = {}
    for r in rot:
        if r["part"] == "start":
            continue
        e = by_day.setdefault(r["day"], {"date": r["date"], "deep": "–", "overview": "–", "review": "–"})
        sc = r.get("scenario", "")
        if r["part"] == "review":
            sc = f"{len(sc.split(','))} scenarios"
        e[r["part"]] = f"{sc} {'✓' if r.get('status') == 'done' else '(partial)'}".strip()
    trows = [[n, e["date"], e["deep"], e["overview"], e["review"], days.get(e["date"], {}).get("minutes") or "–"]
             for n, e in sorted(by_day.items(), reverse=True)][:10]
    n = cca.current_day(rot)
    deep, ov, rev = cca.day_parts(n)
    sub = (f"Day {n} {'in progress' if rot and rot[-1]['date'] == today.isoformat() else 'is next'}: "
           f"{deep} deep dive" + (f", {ov} overview" if ov else "") + f", review {' '.join(rev)}.")
    body = cal + (table(["Day", "Date", "Deep dive", "Overview", "Review", "Min"], trows, num=(0, 5)) if trows
                  else empty("No rotation days yet. Run /cca-day to start day 1."))
    return card("Rotation", body, sub)


def queue_card(q):
    names = cca.EXAMS["F"]["scenarios"]
    rows, meters = [], []
    for s in cca.ORDER:
        es = [e for e in q if e["scenario"] == s and e["status"] != "dropped"]
        act = [e for e in es if e["status"] == "active" and e["kind"] != "pre"]
        b = [sum(e["box"] == k for e in act) for k in range(3)]
        solid = sum(e["status"] == "solid" for e in es)
        total = sum(b) + solid
        v = pct(solid, total) or 0
        rows.append([f"{s} {names[s][0]}", b[0], b[1], b[2], solid,
                     sum(e["kind"] == "open" and e["status"] == "active" for e in es)])
        meters.append(f'<div class="mrow" tabindex="0" data-tip="{E(f"{s} · {solid} of {total} solid · new or missed {b[0]} · box 1 {b[1]} · box 2 {b[2]}")}">'
                      f'<span class="mlabel">{s}</span><span class="meter"><span style="--v:{v}"></span></span>'
                      f'<span class="mval">{solid}/{total}</span></div>')
    week = (cca.today() - dt.timedelta(days=6)).isoformat()
    hist = [r for e in q for d, r in e.get("history", []) if d >= week]
    rate = pct(sum(r == "right" for r in hist), len(hist))
    sub = (f"Review answers in the last 7 days: {rate}% right ({len(hist)} answers). " if hist else "") + \
          "A question is solid after three right answers: the next day, a week later, then retired."
    body = ('<div class="meters">' + "".join(meters) + "</div>" if any(r[1:5] != [0, 0, 0, 0] for r in rows)
            else empty("The queue fills as deep dives add questions."))
    return card("Review queue", body, sub,
                table(["Scenario", "New or missed", "Box 1", "Box 2", "Solid", "Open"], rows, num=(1, 2, 3, 4, 5)))


def carrying_card(q):
    names = cca.EXAMS["F"]["scenarios"]
    act = [e for e in q if e["status"] == "active" and e["kind"] in ("open", "pre")]
    if not act:
        return card("What you're carrying", empty("No open questions yet. Deep dives add the ones you don't settle."))
    out, shown, cap = [], 0, 15
    for s in cca.ORDER:
        es = [e for e in act if e["scenario"] == s][:max(0, cap - shown)]
        shown += len(es)
        if not es:
            continue
        lis = "".join(f'<li><span class="qid">{E(e["id"])}</span> {E(e["prompt"])}'
                      f'<span class="muted"> · {"pre-question" if e["kind"] == "pre" else "open"}'
                      f'{" · " + E(e["ref"]) if e.get("ref") else ""}</span></li>' for e in es)
        out.append(f'<h3>{E(s)} {E(names[s][0])}</h3><ul class="qs">{lis}</ul>')
    if len(act) > shown:
        out.append(f'<p class="note">{len(act) - shown} more in progress/notebook.md.</p>')
    return card("What you're carrying", "".join(out),
                "Open questions and pre-questions, without answers. Also in progress/notebook.md.")


def misses_card(prac):
    conf = [r for r in prac if not r["correct"] and r.get("confidence") == "high"][-8:][::-1]
    if not conf:
        return card("High-confidence misses", empty("None yet."))
    rows = [[r["ts"][:10], r["task"], r.get("scenario", "–"), r.get("lesson", "(no lesson noted)")] for r in conf]
    return card("High-confidence misses", table(["Date", "Objective", "Scenario", "Lesson"], rows),
                "Answers you were sure of and got wrong: the misconceptions worth the most attention.")


def readiness_card(rows, exam):
    prac = cca.practice_rows(rows)
    checks = cca.readiness(rows, exam) if prac else []
    if not checks:
        return card("Readiness", empty("The checklist appears once practice items are logged."))
    lis = "".join(f'<li class="{"met" if ok else "unmet"}"><span class="ic" aria-hidden="true">{"✓" if ok else "○"}</span>'
                  f'<span class="sr">{"met" if ok else "not yet"}: </span>{E(label)}</li>' for label, ok in checks)
    return card("Readiness", f'<ul class="checks">{lis}</ul>',
                f"{sum(ok for _, ok in checks)} of {len(checks)} met. A study heuristic, not a conversion to the 720 scaled score.")


def journal_card(journal):
    if not journal:
        return card("Journal", empty("No entries yet. /cca-day adds one at the end of each study day."))
    lis = "".join(f'<li><span class="jdate">{E(j["date"])}</span><span class="badge">{E(j["kind"])}</span>'
                  f'{" <span class=muted>" + str(j["minutes"]) + " min</span>" if j.get("minutes") else ""}'
                  f'<div>{E(j["text"])}</div></li>' for j in journal[-12:][::-1])
    return card("Journal", f'<ul class="journal">{lis}</ul>', "Study sessions and milestones, newest first.")


def mocks_card(exam, prac):
    mocks = defaultdict(list)
    for r in prac:
        if r["source"] == "mock" and r.get("session"):
            mocks[r["session"]].append(r)
    if not mocks:
        return ""
    ex = cca.EXAMS[exam]
    rows = []
    for s, rs in sorted(mocks.items()):
        per = []
        for d in ex["domains"]:
            dr = [r["correct"] for r in rs if r["domain"] == d]
            per.append(f"{pct(sum(dr), len(dr))}%" if dr else "–")
        rows.append([s, f"{sum(r['correct'] for r in rs)}/{len(rs)}", f"{pct(sum(r['correct'] for r in rs), len(rs))}%"] + per)
    return card("Mock exams", table(["Session", "Score", "%"] + [f"D{d}" for d in ex["domains"]], rows,
                                    num=tuple(range(1, 3 + len(ex["domains"])))),
                "Readiness wants the last two at 80% or better.", wide=True)


# ---------------------------------------------------------------- page

LIGHT = """--page:#f9f9f7;--surface:#fcfcfb;--ink:#0b0b0b;--ink-2:#52514e;--muted:#898781;--grid:#e1e0d9;
--axis:#c3c2b7;--border:rgba(11,11,11,0.10);--series-1:#2a78d6;--good:#006300;--down:#d03b3b;--link:#2a78d6;
--track:#cde2fb;--b1:#86b6ef;--b2:#5598e7;--b3:#2a78d6;--b4:#1c5cab;
--i1:#0b0b0b;--i2:#0b0b0b;--i3:#ffffff;--i4:#ffffff;"""
DARK = """color-scheme:dark;--page:#0d0d0d;--surface:#1a1a19;--ink:#f0efec;--ink-2:#c3c2b7;--muted:#898781;
--grid:#2c2c2a;--axis:#383835;--border:rgba(255,255,255,0.10);--series-1:#3987e5;--good:#0ca30c;--down:#d03b3b;--link:#3987e5;
--track:#0d366b;--b1:#184f95;--b2:#256abf;--b3:#3987e5;--b4:#6da7ec;
--i1:#ffffff;--i2:#ffffff;--i3:#0b0b0b;--i4:#0b0b0b;"""

CSS = """
:root{color-scheme:light;LIGHT}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){DARK}}
:root[data-theme="dark"]{DARK}
*{box-sizing:border-box}
body{margin:0;background:var(--page);color:var(--ink);font:14px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1180px;margin:0 auto;padding:24px 16px 48px}
header{display:flex;flex-wrap:wrap;gap:8px 16px;align-items:baseline;justify-content:space-between;margin-bottom:16px}
h1{font-size:22px;margin:0;font-weight:600}
.meta{color:var(--ink-2);margin:4px 0 0}
a{color:var(--link)}
.actions{display:flex;gap:8px}
#theme,#refresh{font:inherit;color:var(--ink-2);background:var(--surface);border:1px solid var(--border);border-radius:6px;padding:4px 10px;cursor:pointer}
#refresh{color:var(--ink)}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:16px}
.tile{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:12px 14px}
.tile-label{color:var(--ink-2);font-size:13px}
.tile-value{font-size:26px;font-weight:600;margin:2px 0}
.tile-sub{color:var(--ink-2);font-size:12px}
.delta.up{color:var(--good)}.delta.down{color:var(--down)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,440px),1fr));gap:16px}
.card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px;min-width:0}
.card.wide{grid-column:1/-1}
h2{font-size:15px;margin:0 0 2px;font-weight:600}
h3{font-size:13px;margin:12px 0 4px;color:var(--ink-2);font-weight:600}
.sub{color:var(--ink-2);margin:0 0 12px;font-size:13px}
.muted{color:var(--ink-2);font-weight:400}
.empty{color:var(--ink-2);margin:8px 0}
.note{color:var(--ink-2);font-size:12px;margin:8px 0 0;display:flex;align-items:center;gap:6px}
.bars{display:flex;flex-direction:column;gap:6px}
.bar-row{display:grid;grid-template-columns:minmax(0,5fr) minmax(0,6fr);gap:10px;align-items:center;border-radius:6px;padding:2px 4px;outline:none}
.bar-row:hover,.bar-row:focus-visible{background:var(--page)}
.bar-label{font-size:13px;overflow-wrap:anywhere}
.bar-track{position:relative;height:24px}
.bar{position:absolute;left:0;top:5px;height:14px;width:calc((100% - 52px) * var(--v) / 100);background:var(--series-1);border-radius:0 4px 4px 0}
.bar-val{position:absolute;top:2px;left:calc((100% - 52px) * var(--v) / 100 + 6px);font-size:12px;font-variant-numeric:tabular-nums;white-space:nowrap}
.bar-val.none{color:var(--ink-2)}
.bar-target,.key-target{position:absolute;top:0;bottom:0;left:calc((100% - 52px) * 0.75);width:1px;background:var(--muted)}
.key-target{position:static;display:inline-block;height:12px}
@media (max-width:520px){.bar-row{grid-template-columns:1fr;gap:2px}}
.heat{display:flex;flex-direction:column;gap:2px}
.heat-row{display:flex;align-items:center;gap:10px}
.heat-label{width:64px;flex:none;font-size:13px}
.heat-cells{display:flex;flex-wrap:wrap;gap:2px}
.cell{width:56px;height:34px;display:inline-flex;align-items:center;justify-content:center;font-size:12px;font-weight:600;border-radius:4px;outline:none;font-variant-numeric:tabular-nums}
.cell:hover,.cell:focus-visible{filter:brightness(1.12)}
@media (max-width:520px){.cell{width:36px;height:30px;font-size:11px}.heat-label{width:40px}.heat-row{gap:8px}}
.b0{background:var(--grid);color:var(--ink-2);font-weight:400}
.b1{background:var(--b1);color:var(--i1)}.b2{background:var(--b2);color:var(--i2)}
.b3{background:var(--b3);color:var(--i3)}.b4{background:var(--b4);color:var(--i4)}
.legend{display:flex;flex-wrap:wrap;gap:6px 14px;margin-top:10px;font-size:12px;color:var(--ink-2)}
.lg{display:inline-flex;align-items:center;gap:6px}
.sw{display:inline-block;width:12px;height:12px;border-radius:3px}
.sw.on{background:var(--series-1)}
svg.trend{width:100%;height:auto;display:block;touch-action:none}
svg .grid{stroke:var(--grid);stroke-width:1}
svg .axis{stroke:var(--axis);stroke-width:1}
svg .target{stroke:var(--muted);stroke-width:1}
svg .tick{fill:var(--muted);font-size:11px;font-variant-numeric:tabular-nums}
svg .line{fill:none;stroke:var(--series-1);stroke-width:2;stroke-linejoin:round;stroke-linecap:round}
svg .end,svg .hover-dot{fill:var(--series-1);stroke:var(--surface);stroke-width:2}
svg .endlabel{fill:var(--ink);font-size:12px;font-weight:600}
svg .cross{stroke:var(--axis);stroke-width:1}
svg .hit{fill:transparent;cursor:crosshair}
svg .hitbox{fill:transparent}
svg .whisker{stroke:var(--series-1);stroke-width:2;stroke-linecap:round;opacity:.45}
svg .pt{stroke:var(--surface);stroke-width:2}
svg .pt.mock{fill:var(--series-1)}
svg .pt.block,svg .pt.retake{fill:var(--surface);stroke:var(--series-1)}
svg g[tabindex]{outline:none}
svg g[tabindex]:hover .whisker,svg g[tabindex]:focus-visible .whisker{opacity:1}
.cal{display:flex;gap:2px;margin-bottom:4px}
.cal-days,.week{display:flex;flex-direction:column;gap:2px}
.cal-days span{height:14px;font-size:10px;line-height:14px;color:var(--muted);width:28px}
.day{width:14px;height:14px;border-radius:3px;outline:none}
.day.on{background:var(--series-1)}.day.off{background:var(--grid)}.day.future{background:transparent}
.day.on:hover,.day.on:focus-visible{filter:brightness(1.15)}
.meters{display:flex;flex-direction:column;gap:8px}
.mrow{display:grid;grid-template-columns:32px 1fr 44px;gap:10px;align-items:center;outline:none}
.mlabel{font-size:13px}.mval{font-size:12px;color:var(--ink-2);text-align:right;font-variant-numeric:tabular-nums}
.meter{height:10px;background:var(--track);border-radius:5px;overflow:hidden}
.meter span{display:block;height:100%;width:calc(var(--v) * 1%);background:var(--series-1);border-radius:5px}
.qs,.checks,.journal{list-style:none;margin:0;padding:0}
.qs li{padding:6px 0;border-top:1px solid var(--border)}
.qs li:first-child{border-top:0}
.qid{font-weight:600;font-variant-numeric:tabular-nums;margin-right:4px}
.checks li{display:flex;gap:8px;padding:4px 0}
.checks .ic{width:16px;flex:none;text-align:center;font-weight:700}
.checks .met .ic{color:var(--good)}.checks .unmet .ic{color:var(--muted)}.checks .unmet{color:var(--ink-2)}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}
.journal li{padding:8px 0;border-top:1px solid var(--border)}
.journal li:first-child{border-top:0}
.jdate{font-variant-numeric:tabular-nums;margin-right:8px;font-weight:600}
.badge{font-size:11px;color:var(--ink-2);border:1px solid var(--border);border-radius:10px;padding:0 7px;margin-right:6px}
.tv{margin-top:12px}
.tv summary{cursor:pointer;color:var(--ink-2);font-size:12px}
.tbl{overflow-x:auto;margin-top:8px}
table{border-collapse:collapse;width:100%;font-size:12px}
th,td{text-align:left;padding:5px 8px;border-bottom:1px solid var(--grid);vertical-align:top;white-space:nowrap}
td:last-child{white-space:normal}
th{color:var(--ink-2);font-weight:600}
.num{text-align:right;font-variant-numeric:tabular-nums}
#tip{position:fixed;z-index:10;pointer-events:none;max-width:320px;background:var(--surface);color:var(--ink);border:1px solid var(--border);
border-radius:8px;padding:6px 10px;font-size:12px;box-shadow:0 4px 16px rgba(0,0,0,.12);display:none}
footer{color:var(--ink-2);font-size:12px;margin-top:20px}
""".replace("LIGHT", LIGHT).replace("DARK", DARK)

JS = """
(function(){
  var tip=document.getElementById('tip');
  function show(text,x,y){tip.textContent=text;tip.style.display='block';
    var w=tip.offsetWidth,h=tip.offsetHeight,px=Math.min(x+12,innerWidth-w-8),py=y-h-12<8?y+16:y-h-12;
    tip.style.left=Math.max(8,px)+'px';tip.style.top=py+'px';}
  function hide(){tip.style.display='none';}
  document.querySelectorAll('[data-tip]').forEach(function(el){
    el.addEventListener('pointermove',function(e){show(el.dataset.tip,e.clientX,e.clientY);});
    el.addEventListener('pointerleave',hide);
    el.addEventListener('focus',function(){var r=el.getBoundingClientRect();show(el.dataset.tip,r.left+r.width/2,r.top);});
    el.addEventListener('blur',hide);
  });
  document.querySelectorAll('svg.trend[data-points]').forEach(function(svg){  // the practice chart has no crosshair
    var pts=JSON.parse(svg.dataset.points),cross=svg.querySelector('.cross'),dot=svg.querySelector('.hover-dot'),hit=svg.querySelector('.hit');
    hit.addEventListener('pointermove',function(e){
      var p=svg.createSVGPoint();p.x=e.clientX;p.y=e.clientY;var loc=p.matrixTransform(svg.getScreenCTM().inverse());
      var best=0;for(var i=1;i<pts.length;i++){if(Math.abs(pts[i].x-loc.x)<Math.abs(pts[best].x-loc.x))best=i;}
      cross.setAttribute('x1',pts[best].x);cross.setAttribute('x2',pts[best].x);
      dot.setAttribute('cx',pts[best].x);dot.setAttribute('cy',pts[best].y);show(pts[best].t,e.clientX,e.clientY);});
    hit.addEventListener('pointerleave',function(){cross.setAttribute('x1',-10);cross.setAttribute('x2',-10);dot.setAttribute('cx',-10);hide();});
  });
  document.getElementById('refresh').addEventListener('click',function(){location.reload();});
  var d=new Date(),p=function(n){return (n<10?'0':'')+n;},day=d.getFullYear()+'-'+p(d.getMonth()+1)+'-'+p(d.getDate());
  if(document.body.dataset.built<day)document.getElementById('stale').hidden=false;
  var btn=document.getElementById('theme'),modes=['auto','light','dark'];
  function apply(m){if(m==='auto')document.documentElement.removeAttribute('data-theme');else document.documentElement.dataset.theme=m;btn.textContent='Theme: '+m;}
  var cur='auto';try{cur=localStorage.getItem('cca-theme')||'auto';}catch(e){}
  apply(cur);
  btn.addEventListener('click',function(){cur=modes[(modes.indexOf(cur)+1)%3];apply(cur);try{localStorage.setItem('cca-theme',cur);}catch(e){}});
})();
"""


def build(exam="F", out=None):
    ex = cca.EXAMS[exam]
    rows = cca.load(exam)
    prac = cca.practice_rows(rows)
    rot = cca.rotation_rows() if exam == "F" else []
    q = cca.load_queue() if exam == "F" else []
    journal = cca.journal_rows()
    days = study_days(prac + [r for r in rows if r.get("source") == "retake"], rot, journal)

    ed = exam_date()
    when = (f"Exam date {ed} ({(ed - cca.today()).days} days)" if ed
            else "Exam date not set (/cca-coach plan)")
    generated = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    path = out_path(exam, out)

    parts = ([practice_card(path.parent)] if exam == "F" else []) + [domains_card(exam, prac)]
    if exam == "F":
        parts.append(scenarios_card(prac, q, rot))
    parts += [heatmap_card(exam, rows), trend_card(prac), calibration_card(prac)]
    if exam == "F":
        parts += [rotation_card(days, rot), queue_card(q), carrying_card(q)]
    parts += [misses_card(prac), readiness_card(rows, exam), journal_card(journal), mocks_card(exam, prac)]

    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Study Progress</title><style>{CSS}</style></head>
<body data-built="{dt.date.today().isoformat()}"><main>
<header><div><h1>{E(ex['name'])} · study progress</h1>
<p class="meta">{E(when)} · updated {generated}</p>
<p class="meta" id="stale" hidden>Built on an earlier day, so what's due is as of then. It rebuilds when you next
study, or run <code>python3 scripts/cca.py dashboard</code>.</p></div>
<div class="actions"><button id="refresh" type="button" title="Show the latest progress. The page is rebuilt every time
progress is logged.">Refresh</button><button id="theme" type="button">Theme: auto</button></div></header>
{kpis(exam, prac, days, journal, q, rot)}
<div class="grid">{"".join(parts)}</div>
<footer>Practice percentages are not scaled scores. This page is rebuilt from progress/ whenever progress is logged;
Refresh reloads it.</footer>
</main><div id="tip" role="status"></div><script>{JS}</script></body></html>
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(page)
    return path


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--exam", choices=["F", "P"], default="F")
    p.add_argument("--out")
    p.add_argument("--open", action="store_true")
    a = p.parse_args()
    path = build(a.exam, a.out)
    print(f"dashboard written to {path}")
    if a.open:
        open_file(path)


if __name__ == "__main__":
    main()
