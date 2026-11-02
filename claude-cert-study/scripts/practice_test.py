#!/usr/bin/env python3
"""Take a practice test in your browser, then paste your answers back into Claude Code.

Standard library only. Questions come from the verified question bank (scripts/bank.py): fresh items for one
scenario. The page has no answer keys in it. When you finish, its "Copy results" button copies a
`/cca-test results ...` line; paste that into Claude Code to grade the test and talk it through.

  practice_test.py [new] [--scenario S1] [--n 10] [--no-open]    build and open a test
                                                                  (default scenario: today's rotation day)
  practice_test.py submit SESSION 1:B:h 2:AD:m:f 3:- [time=845]   record the answers and grade
  practice_test.py list                                           every browser test: taken, not taken, void
  practice_test.py open SESSION                                   reopen a test you haven't taken
  practice_test.py void SESSION [--release]                       drop a test you won't take
  practice_test.py retake [SESSION | --scenario S1]               take a test again, questions in a new order
                                                                  (default: the one practiced longest ago)

A test you build but don't take stays open, and `new` reopens it instead of building another on the same
scenario (--another builds a second one anyway). `void` drops it. New tests draw on questions not yet used in a
test; a voided test's questions stay used unless --release says you never read them.

A retake is a new attempt at a test you've taken, with its own session. It's logged as source=retake, so it shows
on the dashboard's practice chart but stays out of accuracy by domain: you've seen the answers. Grading a retake
lists which questions changed since the attempt before.

Answer tokens: question:letters[:h|m|l][:f], where "-" means unanswered and f means flagged.
Pages are saved in progress/tests/<session>.html.
"""
import argparse
import html
import json
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bank  # noqa: E402
import cca  # noqa: E402

TESTS = cca.ROOT / "progress" / "tests"
MIN_ITEMS = 5


def die(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(2)


def default_scenario():
    return cca.day_parts(cca.current_day(cca.rotation_rows()))[0]


# ---------------------------------------------------------------- page

def inline(s):
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", html.escape(s))


def block(s):
    out, para, items = [], [], []

    def flush():
        if para:
            out.append("<p>" + " ".join(inline(x) for x in para) + "</p>")
            para.clear()
        if items:
            out.append("<ul>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ul>")
            items.clear()

    for line in s.splitlines():
        t = line.strip()
        if t.startswith(("- ", "* ")):
            if para:
                flush()
            items.append(t[2:])
        elif not t:
            flush()
        else:
            if items:
                flush()
            para.append(t)
    flush()
    return "".join(out)


CSS = """
:root{color-scheme:light;--page:#f9f9f7;--surface:#fcfcfb;--ink:#0b0b0b;--ink-2:#52514e;--muted:#898781;
--line:#e1e0d9;--border:rgba(11,11,11,0.10);--accent:#2a78d6;--accent-wash:rgba(42,120,214,0.10);--good:#006300}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){color-scheme:dark;--page:#0d0d0d;--surface:#1a1a19;
--ink:#f0efec;--ink-2:#c3c2b7;--muted:#898781;--line:#2c2c2a;--border:rgba(255,255,255,0.10);--accent:#3987e5;
--accent-wash:rgba(57,135,229,0.16);--good:#0ca30c}}
*{box-sizing:border-box}
body{margin:0;background:var(--page);color:var(--ink);font:16px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:820px;margin:0 auto;padding:16px 16px 96px}
header.top{position:sticky;top:0;z-index:5;background:var(--page);border-bottom:1px solid var(--line);
padding:10px 0;margin-bottom:16px;display:flex;flex-wrap:wrap;gap:6px 16px;align-items:baseline;justify-content:space-between}
h1{font-size:18px;margin:0;font-weight:600}
.stat{color:var(--ink-2);font-size:14px;font-variant-numeric:tabular-nums}
.stat strong{color:var(--ink)}
.over{color:#d03b3b}
.frame{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:14px 16px;margin-bottom:20px}
.frame h2{font-size:13px;text-transform:uppercase;letter-spacing:.04em;color:var(--ink-2);margin:0 0 6px}
.frame p{margin:0}
.q{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px;margin-bottom:16px;scroll-margin-top:72px}
.qhead{display:flex;gap:10px;align-items:center;margin-bottom:8px;font-size:13px;color:var(--ink-2)}
.badge{border:1px solid var(--border);border-radius:10px;padding:0 8px;font-size:12px}
.stem p{margin:0 0 10px}.stem ul{margin:0 0 10px;padding-left:22px}
code{font:13px/1.4 ui-monospace,SFMono-Regular,Menlo,monospace;background:var(--page);border:1px solid var(--line);
border-radius:4px;padding:0 4px}
.opts{display:flex;flex-direction:column;gap:8px;margin:12px 0}
.opt{display:grid;grid-template-columns:auto 22px 1fr;gap:10px;align-items:start;padding:10px 12px;border:1px solid var(--line);
border-radius:8px;cursor:pointer}
.opt:hover{border-color:var(--muted)}
.opt:has(input:checked){border-color:var(--accent);background:var(--accent-wash)}
.opt input{margin-top:5px;accent-color:var(--accent)}
.letter{font-weight:600}
.meta{display:flex;flex-wrap:wrap;gap:10px 18px;align-items:center;font-size:14px;color:var(--ink-2)}
.conf{display:inline-flex;border:1px solid var(--line);border-radius:8px;overflow:hidden}
.conf label{padding:4px 10px;cursor:pointer;border-left:1px solid var(--line)}
.conf label:first-of-type{border-left:0}
.conf input{position:absolute;opacity:0;pointer-events:none}
.conf label:has(input:checked){background:var(--accent-wash);color:var(--ink);font-weight:600}
.conf label:has(input:focus-visible){outline:2px solid var(--accent);outline-offset:-2px}
.flag{display:inline-flex;gap:6px;align-items:center;cursor:pointer}
.finish{display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin-top:8px}
button{font:inherit;font-weight:600;border-radius:8px;padding:10px 18px;cursor:pointer;border:1px solid var(--accent);
background:var(--accent);color:#fff}
button.secondary{background:transparent;color:var(--accent)}
#results{display:none;background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px;margin-top:16px}
#results h2{font-size:16px;margin:0 0 8px}
#results textarea{width:100%;min-height:84px;font:13px/1.4 ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--ink);
background:var(--page);border:1px solid var(--line);border-radius:8px;padding:8px}
#copied{color:var(--good);font-size:14px;font-weight:600}
.missing a{color:var(--accent)}
.help{color:var(--ink-2);font-size:14px}
"""

JS = r"""
(function(){
  var S=SESSION, N=COUNT, key='cca-test-'+S, st={a:{},c:{},f:{},el:0};
  try{var saved=JSON.parse(localStorage.getItem(key)||'null'); if(saved) st=saved;}catch(e){}
  if(typeof st.el!=='number') st.el=0;  // pages built before the clock fix saved a start time instead
  function save(){try{localStorage.setItem(key,JSON.stringify(st));}catch(e){}}
  function q(n){return document.getElementById('q'+n);}
  function restore(){
    for(var n=1;n<=N;n++){
      (st.a[n]||[]).forEach(function(l){var i=q(n).querySelector('.opts input[value="'+l+'"]'); if(i) i.checked=true;});
      if(st.c[n]){var c=q(n).querySelector('.conf input[value="'+st.c[n]+'"]'); if(c) c.checked=true;}
      if(st.f[n]) q(n).querySelector('.flag input').checked=true;
    }
  }
  function answered(){var k=0; for(var n=1;n<=N;n++) if((st.a[n]||[]).length) k++; return k;}
  function progress(){document.getElementById('done').textContent=answered();}
  document.querySelectorAll('.q').forEach(function(sec){
    var n=+sec.dataset.n, multi=sec.dataset.multi==='1';
    sec.querySelectorAll('.opts input').forEach(function(inp){
      inp.addEventListener('change',function(){
        var picked=[].slice.call(sec.querySelectorAll('.opts input:checked')).map(function(x){return x.value;});
        if(multi && picked.length>2){inp.checked=false; picked=picked.filter(function(v){return v!==inp.value;});}
        st.a[n]=picked.sort(); save(); progress();
      });
    });
    sec.querySelectorAll('.conf input').forEach(function(inp){inp.addEventListener('change',function(){st.c[n]=inp.value; save();});});
    sec.querySelector('.flag input').addEventListener('change',function(e){st.f[n]=e.target.checked; save();});
  });
  function fmt(s){var m=Math.floor(s/60), r=s%60; return m+':'+(r<10?'0':'')+r;}
  function secs(){return Math.floor(st.el/1000);}
  var last=Date.now();
  function tick(){  // the clock runs only while the page is on screen, so a test resumed days later reads true
    var t=Date.now(), d=t-last; last=t;
    if(!document.hidden && d<5000){st.el+=d; save();}
    var s=secs(), el=document.getElementById('clock'); el.textContent=fmt(s); el.className=s>N*120?'over':'';}
  setInterval(tick,1000); tick(); save(); restore(); progress();
  function resultText(){
    var parts=[];
    for(var n=1;n<=N;n++){
      var a=(st.a[n]||[]).join('')||'-', t=n+':'+a;
      if(a!=='-' && st.c[n]) t+=':'+st.c[n];
      if(st.f[n]) t+=':f';
      parts.push(t);
    }
    return '/cca-test results '+S+' '+parts.join(' ')+' time='+secs();
  }
  document.getElementById('finish').addEventListener('click',function(){
    var box=document.getElementById('results'), miss=[], flags=[];
    for(var n=1;n<=N;n++){ if(!(st.a[n]||[]).length) miss.push(n); if(st.f[n]) flags.push(n); }
    var m=document.getElementById('missing'); m.textContent='';
    function links(label, list){
      if(!list.length) return; var p=document.createElement('p'); p.className='missing'; p.appendChild(document.createTextNode(label+' '));
      list.forEach(function(n,i){var a=document.createElement('a'); a.href='#q'+n; a.textContent='Q'+n; p.appendChild(a);
        if(i<list.length-1) p.appendChild(document.createTextNode(', '));}); m.appendChild(p);
    }
    links('Unanswered (they count as wrong):', miss); links('Flagged:', flags);
    document.getElementById('out').value=resultText(); box.style.display='block'; box.scrollIntoView({behavior:'smooth'});
  });
  document.getElementById('copy').addEventListener('click',function(){
    var ta=document.getElementById('out'); ta.value=resultText(); var ok=document.getElementById('copied');
    function done(){ok.textContent='Copied. Paste it into Claude Code.';}
    function fallback(){ta.focus(); ta.select(); try{document.execCommand('copy'); done();}catch(e){ok.textContent='Select the text above and copy it.';}}
    if(navigator.clipboard && window.isSecureContext){navigator.clipboard.writeText(ta.value).then(done,fallback);} else fallback();
  });
})();
"""


def render(form, items):
    s = form["scenarios"][0]
    n = len(form["items"])
    qs = []
    for k, iid in enumerate(form["items"], 1):
        it = items[iid]
        multi = it["type"] == "multi"
        kind = "checkbox" if multi else "radio"
        opts = "".join(f'<label class="opt"><input type="{kind}" name="q{k}" value="{L}"><span class="letter">{L}</span>'
                       f'<span>{inline(v)}</span></label>' for L, v in it["options"].items())
        conf = "".join(f'<label><input type="radio" name="c{k}" value="{v}">{lbl}</label>'
                       for v, lbl in (("h", "High"), ("m", "Medium"), ("l", "Low")))
        qs.append(f'<section class="q" id="q{k}" data-n="{k}" data-multi="{int(multi)}">'
                  f'<div class="qhead"><span>Question {k} of {n}</span>'
                  f'{"<span class=badge>Select TWO</span>" if multi else ""}</div>'
                  f'<div class="stem">{block(it["stem"])}</div><div class="opts">{opts}</div>'
                  f'<div class="meta"><span>Confidence</span><span class="conf" role="radiogroup" '
                  f'aria-label="Confidence for question {k}">{conf}</span>'
                  f'<label class="flag"><input type="checkbox"> Flag for review</label></div></section>')
    name = cca.EXAMS["F"]["scenarios"][s][0]
    attempt = f" · attempt {form['attempt']}" if form.get("retake_of") else ""
    js = JS.replace("SESSION", json.dumps(form["session"])).replace("COUNT", str(n))
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Practice Test</title><style>{CSS}</style></head><body><main>
<header class="top"><h1>{html.escape(s)} {html.escape(name)} · practice test{attempt}</h1>
<span class="stat"><strong id="done">0</strong>/{n} answered · <strong id="clock">0:00</strong> of about {2 * n}:00</span></header>
<div class="frame"><h2>Scenario</h2>{block(bank.scenario_frame(s))}</div>
<p class="help">Pick an answer for each question and say how sure you are. No feedback until the end. Your answers
are saved in this browser if you close the tab, and the clock runs only while this page is open.
Session {html.escape(form["session"])}.</p>
{"".join(qs)}
<div class="finish"><button id="finish" type="button">Finish and get my results</button></div>
<div id="results" role="region" aria-label="Results to copy"><h2>Copy this into Claude Code</h2>
<div id="missing"></div>
<textarea id="out" readonly aria-label="Results text"></textarea>
<div class="finish"><button id="copy" type="button">Copy results</button><span id="copied" role="status"></span></div>
<p class="help">Paste it into Claude Code and press Enter. Claude grades the test, logs it, and talks it through with
you. The answer keys aren't in this page.</p></div>
</main><script>{js}</script></body></html>
"""


# ---------------------------------------------------------------- commands

def page_path(session):
    return TESTS / f"{session}.html"


def write_page(form, items=None):
    """Build (or rebuild) a test's page from its form. Safe to repeat: the page holds no keys, and answers
    given so far are saved in the browser under the session name."""
    items = items or {i["id"]: i for i in bank.load_json(bank.ITEMS, [])}
    TESTS.mkdir(parents=True, exist_ok=True)
    path = page_path(form["session"])
    path.write_text(render(form, items))
    return path


def untaken(scenario=None):
    """Browser tests built but not graded or voided, oldest first."""
    return [f for f in bank.open_forms()
            if f.get("format") == "browser" and scenario in (None, f["scenarios"][0])]


def root(form):
    """The test a form belongs to: itself, or for a retake, the original."""
    return form.get("retake_of") or form["session"]


def attempts(orig):
    """Graded attempts at a test, the first try included, oldest first."""
    return [f for f in bank.graded_forms() if root(f) == orig]


def describe(form):
    again = f", attempt {form['attempt']} of {form['retake_of']}" if form.get("retake_of") else ""
    return (f"{form['session']} ({form['scenarios'][0]}, {len(form['items'])} questions{again}, "
            f"built {form['created'][:10]})")


def show(form, no_open):
    path = write_page(form)
    print(f"page: {path}")
    if not no_open:
        import dashboard
        dashboard.open_file(path)


def cmd_new(a):
    s = (a.scenario or default_scenario()).upper()
    if s not in cca.FOLDERS:
        die(f"unknown scenario {s}")
    waiting = untaken(s)
    if waiting and not a.another:
        form = waiting[0]
        print(f"Not taken yet: {describe(form)}. Reopening it instead of building another; answers already "
              f"given are still saved in the browser.\nsession: {form['session']}\n"
              f"For a different test: --another builds one and leaves this open, or "
              f"practice_test.py void {form['session']} drops this one.")
        show(form, a.no_open)
        return
    items = bank.load_json(bank.ITEMS, [])
    pool = [i for i in items if i["scenario"] == s and i["status"] == "verified" and not i["seen"]]
    if len(pool) < MIN_ITEMS:
        print(f"Only {len(pool)} fresh verified {s} question(s) in the bank; a test needs at least {MIN_ITEMS}.\n"
              f"Generate more (several minutes, uses your Claude plan): "
              f"python3 scripts/bank.py generate --scenario {s} --n {max(10, 2 * a.n)}")
        sys.exit(1)
    chosen = bank.pick_items(pool, min(a.n, len(pool)), random.Random())
    form = bank.new_form("block", [i["id"] for i in chosen], [s])
    form["format"] = "browser"
    bank.save_json(bank.FORMS / f"{form['session']}.json", form)
    print(f"session: {form['session']}\nquestions: {len(chosen)} ({s}{', fewer than asked: the bank ran short' if len(chosen) < a.n else ''})"
          f"\nfresh {s} questions left in the bank: {len(pool) - len(chosen)}")
    show(form, a.no_open)
    others = [f for f in untaken() if f["session"] != form["session"]]
    if others:
        print("Also not taken yet: " + "; ".join(describe(f) for f in others))


def cmd_open(a):
    form = bank.load_form(a.session)
    if form["graded"]:
        die(f"this test is graded; to take it again: practice_test.py retake {a.session}")
    if form.get("void"):
        die("this test was voided")
    if form.get("format") != "browser":
        die("this test is taken in chat, not the browser: /cca-mock-exam resume")
    show(form, a.no_open)


def cmd_list(a):
    groups = {}  # original test -> its browser attempts, oldest first
    for f in sorted((json.loads(x.read_text()) for x in bank.FORMS.glob("*.json")), key=lambda f: f["created"]):
        if f.get("format") == "browser":
            groups.setdefault(root(f), []).append(f)
    if not groups:
        print("No browser tests yet. Build one with: python3 scripts/practice_test.py new")
        return
    print("| Built | Test | Questions | Attempts | Next |\n|---|---|---|---|---|")
    for orig, fs in groups.items():
        tries = " → ".join(f"{g['correct']}/{g['n']} on {g['date']}" for g in (f.get("graded") for f in fs) if g)
        pending = [f for f in fs if not f.get("graded") and not f.get("void")]
        if pending:
            nxt = f"take it: practice_test.py open {pending[0]['session']}"
        elif tries:
            nxt = f"practice_test.py retake {orig}"
        else:
            v = fs[-1]["void"]
            nxt = f"void {v['date']}" + (", questions released" if v["released"] else "")
        print(f"| {fs[0]['created'][:10]} | {orig} | {len(fs[0]['items'])} | {tries or '–'} | {nxt} |")


def cmd_retake(a):
    if a.session:
        orig = root(bank.load_form(a.session))
    else:
        s = (a.scenario or default_scenario()).upper()
        last = {}  # original test -> date of its latest attempt (graded_forms runs oldest first)
        for f in bank.graded_forms():
            if f["kind"] == "block" and f["scenarios"][0] == s:
                last[root(f)] = f["graded"]["date"]
        if not last:
            die(f"no taken {s} test to retake yet; take one first: practice_test.py new --scenario {s}")
        orig = min(last, key=last.get)  # the one practiced longest ago
    first = bank.load_form(orig)
    if not first["graded"]:
        die(f"{orig} hasn't been taken yet, so take it first: practice_test.py open {orig}")
    if first["kind"] != "block":
        die("only single-scenario tests can be retaken in the browser")
    waiting = [f for f in untaken() if root(f) == orig]
    if waiting:
        print(f"Not taken yet: {describe(waiting[0])}. Reopening it instead of building another retake.\n"
              f"session: {waiting[0]['session']}")
        show(waiting[0], a.no_open)
        return
    done = attempts(orig)
    ids = list(first["items"])
    random.shuffle(ids)  # a new order, so answers can't be remembered by position
    form = bank.new_form("block", ids, first["scenarios"])
    form.update(format="browser", retake_of=orig, attempt=len(done) + 1)
    bank.save_json(bank.FORMS / f"{form['session']}.json", form)
    g = done[-1]["graded"]
    print(f"session: {form['session']}\nretake of {orig}: attempt {form['attempt']}, {len(ids)} questions in a new "
          f"order\nlast attempt: {g['date']}, {g['correct']}/{g['n']}")
    show(form, a.no_open)


def cmd_void(a):
    form = bank.load_form(a.session)
    if form["graded"]:
        die("this test is graded; its results stay in your log")
    if form.get("void"):
        die("this test is already void")
    form["void"] = {"date": cca.today().isoformat(), "released": a.release}
    bank.save_json(bank.FORMS / f"{a.session}.json", form)
    if a.release:
        items = bank.load_json(bank.ITEMS, [])
        for i in items:
            if i["id"] in form["items"] and a.session in i["seen"]:
                i["seen"].remove(a.session)
        bank.save_json(bank.ITEMS, items)
    page_path(a.session).unlink(missing_ok=True)
    print(f"{a.session} voided and its page deleted. " +
          ("Its questions are back in the fresh pool." if a.release else
           "Its questions stay used, since you may have read them. If you never did, run void with --release "
           "next time to put them back."))


def cmd_submit(a):
    form = bank.load_form(a.session)
    if form["graded"]:
        die("this test is already graded")
    if form.get("void"):
        die("this test was voided")
    n = len(form["items"])
    conf = {"h": "high", "m": "medium", "l": "low"}
    answers, seconds = {}, None
    for tok in a.answers:
        if tok.lower().startswith("time="):
            seconds = int(re.sub(r"\D", "", tok) or 0)
            continue
        m = re.fullmatch(r"(\d+):([A-Ea-e]{1,2}|-)(?::([hmlHML]))?(?::([fF]))?", tok)
        if not m:
            die(f"can't read answer {tok!r}; expected e.g. 3:B:h or 4:AD:m:f")
        k = int(m.group(1))
        if not 1 <= k <= n:
            die(f"question {k} is outside 1–{n}")
        if m.group(2) != "-":
            answers[str(k)] = {"letters": "".join(sorted(m.group(2).upper())),
                               "conf": conf.get((m.group(3) or "").lower()), "flag": bool(m.group(4))}
    form["answers"] = answers
    if seconds is not None:
        form["duration_s"] = seconds
    bank.save_json(bank.FORMS / f"{a.session}.json", form)
    if seconds is not None:
        print(f"Time: {seconds // 60}:{seconds % 60:02d} for {n} questions (target about {2 * n}:00)")
    bank.cmd_grade(argparse.Namespace(session=a.session))
    if form.get("retake_of"):
        changes(bank.load_form(a.session))


def changes(form):
    """After grading a retake: how each question went compared with the attempt before."""
    prev = [f for f in attempts(root(form)) if f["session"] != form["session"]]
    if not prev:
        return
    print("Earlier attempts: " + ", ".join(f"{g['correct']}/{g['n']} on {g['date']}"
                                           for g in (f["graded"] for f in prev)))
    res = {(r["session"], r["bank_item"]): r["correct"] for r in cca.load("F") if r.get("bank_item")}
    before = prev[-1]["session"]
    out = {"Missed again": [], "Missed now, right last time": [], "Right now, missed last time": []}
    for k, iid in enumerate(form["items"], 1):
        was, now = res.get((before, iid)), res.get((form["session"], iid))
        if was is None or now is None:
            continue
        if not now:
            out["Missed again" if not was else "Missed now, right last time"].append(f"Q{k}")
        elif not was:
            out["Right now, missed last time"].append(f"Q{k}")
    for label, qs in out.items():
        if qs:
            print(f"{label}: {', '.join(qs)}")


def main():
    argv = sys.argv[1:]
    if not argv or argv[0] not in ("new", "submit", "list", "open", "void", "retake", "-h", "--help"):
        argv = ["new"] + argv
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("new")
    s.add_argument("--scenario")
    s.add_argument("--n", type=int, default=10)
    s.add_argument("--no-open", action="store_true")
    s.add_argument("--another", action="store_true", help="build a new test even if one on this scenario is open")
    s.set_defaults(fn=cmd_new)
    s = sub.add_parser("submit")
    s.add_argument("session")
    s.add_argument("answers", nargs="+")
    s.set_defaults(fn=cmd_submit)
    sub.add_parser("list").set_defaults(fn=cmd_list)
    s = sub.add_parser("open")
    s.add_argument("session")
    s.add_argument("--no-open", action="store_true")
    s.set_defaults(fn=cmd_open)
    s = sub.add_parser("void")
    s.add_argument("session")
    s.add_argument("--release", action="store_true", help="return its questions to the fresh pool (only if unread)")
    s.set_defaults(fn=cmd_void)
    s = sub.add_parser("retake")
    s.add_argument("session", nargs="?")
    s.add_argument("--scenario")
    s.add_argument("--no-open", action="store_true")
    s.set_defaults(fn=cmd_retake)
    a = p.parse_args(argv)
    a.fn(a)
    if a.cmd in ("new", "submit", "void", "retake"):  # the dashboard lists open tests and graded scores
        cca.refresh_dashboard()


if __name__ == "__main__":
    main()
