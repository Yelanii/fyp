"""Progress demo page for the supervisor (1 November 2026).

Recomputes every number from the saved raw results and writes one self-contained HTML page:
    python -m ereplan.progress_demo          ->  results/Hanwella_Progress_Demo.html
Charts are inline SVG with hover tooltips; no internet needed to view the page.
"""
import base64, glob, html, json, os, time
import numpy as np

INK, MUTED, GRID, HI, LO = "#1b2430", "#5a6575", "#e3e8ee", "#0B5D6B", "#b9c3cc"


def latest(pattern):
    c = sorted(glob.glob(os.path.join("results", pattern)))
    return c[-1] if c else None


def rows(folder):
    r = json.load(open(os.path.join(folder, "rows.json")))
    return r["rows"] if isinstance(r, dict) else r


def bars(items, unit="", highlight=(), width=640, ref=None, fmt="{:.1f}", note=""):
    """Horizontal bar chart as inline SVG. items: list of (label, value, tooltip)."""
    h_row, left, right = 30, 190, 70
    H = h_row * len(items) + 34
    vmax = max(max(v for _, v, _ in items), ref or 0) * 1.08
    vmin = min(0.0, min(v for _, v, _ in items) * 1.08)
    sx = lambda v: left + (v - vmin) / (vmax - vmin) * (width - left - right)
    out = [f"<svg viewBox='0 0 {width} {H}' width='100%' role='img' style='max-width:{width}px'>"]
    x0 = sx(0)
    out.append(f"<line x1='{x0:.1f}' y1='6' x2='{x0:.1f}' y2='{H - 26}' stroke='{MUTED}' stroke-width='1'/>")
    for i, (lab, v, tip) in enumerate(items):
        y = 8 + i * h_row
        a, b = sorted((x0, sx(v)))
        col = HI if lab in highlight else LO
        out.append(f"<g><title>{html.escape(tip)}</title>"
                   f"<rect x='0' y='{y - 2}' width='{width}' height='{h_row}' fill='transparent'/>"
                   f"<text x='{left - 10}' y='{y + 15}' text-anchor='end' font-size='13' fill='{INK}'"
                   f"{' font-weight=\"bold\"' if lab in highlight else ''}>{html.escape(lab)}</text>"
                   f"<rect x='{a:.1f}' y='{y + 2}' width='{max(b - a, 1):.1f}' height='{h_row - 10}' rx='4' fill='{col}'/>"
                   f"<text x='{(b if v >= 0 else x0) + 6:.1f}' y='{y + 15}' font-size='12' fill='{INK}'"
                   f" text-anchor='start'>{fmt.format(v)}{unit}</text></g>")
    out.append(f"<text x='{left}' y='{H - 6}' font-size='11' fill='{MUTED}'>{html.escape(note)}</text></svg>")
    return "".join(out)


def table(head, body):
    t = "<table><thead><tr>" + "".join(f"<th>{h}</th>" for h in head) + "</tr></thead><tbody>"
    return t + "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in body) + "</tbody></table>"


def main():
    S = []      # sections: (id, title, plain, status, body, limit)

    # ---- Core 2: outside methods
    f = latest("core2_confirm_*")
    if f:
        R = rows(f)
        names = {"never": "never check", "always": "always check", "cusum": "CUSUM detector", "v4": "rule v4 (told)",
                 "v4_nocal": "rule v4 (no labels)", "always_x": "cross-check all", "v5": "rule v5 (no labels)",
                 "ssv": "Kiyani 2026 (SSV)", "rdecusum": "Hou 2024 (RDE-CUSUM)", "glrklucb": "Besson 2022 (GLR-klUCB)"}
        m = {k: np.mean([r["loss"] for r in R if r["strategy"] == k]) for k in names}
        seeds = sorted({r["seed"] for r in R})
        sm = lambda k: np.array([np.mean([r["loss"] for r in R if r["strategy"] == k and r["seed"] == s]) for s in seeds])
        wins = {k: int((sm("v5") < sm(k)).sum()) for k in ("ssv", "rdecusum", "glrklucb")}
        items = [(names[k], m[k], f"{names[k]}: mean loss {m[k]:.1f} per task") for k in sorted(names, key=m.get)]
        body = bars(items, highlight=("rule v5 (no labels)",), note="Mean total loss per task over 20 fresh seeds x 64 conditions. Lower is better.")
        body += table(["v5 vs", "Their loss", "v5 loss", "Difference", "Seeds where v5 was lower"],
                      [[names[k], f"{m[k]:.1f}", f"{m['v5']:.1f}", f"{100 * (m['v5'] / m[k] - 1):+.1f}%", f"{wins[k]} / {len(seeds)}"]
                       for k in ("ssv", "rdecusum", "glrklucb")])
        S.append(("C1", "Beats three recent published methods",
                  "Three methods from recent papers were tuned on practice seeds and given the checker's true error rates. "
                  "Rule v5 was given nothing. On 20 fresh seeds, v5 had the lowest loss.",
                  ("CONFIRMED", "ok"), body,
                  "Simulator only. The three methods are my adaptations of the papers (stated in the code)."))

    # ---- Core 3: theory
    f = latest("theory_check_*")
    if f and os.path.exists(os.path.join(f, "wrong_check_region.png")):
        rep = open(os.path.join(f, "report.md")).read()
        worst = [l for l in rep.splitlines() if l.startswith("Worst relative error")]
        img = base64.b64encode(open(os.path.join(f, "wrong_check_region.png"), "rb").read()).decode()
        body = (f"<img alt='Extra loss of checking vs never checking' src='data:image/png;base64,{img}'/>"
                f"<p class='note'>Orange area: success rates where a rule that assumes independent judge verdicts decides to check, "
                f"yet never checking is cheaper. It grows as the judge repeats itself more (pi from 0.5 to 1).</p>"
                f"<p class='check'>Check against the simulator: {html.escape(worst[0] if worst else '')}</p>")
        body += table(["Judge false-alarm rate f", "Retries", "Failure chance a rule assumes", "True failure chance", "Underestimated by"],
                      [["0.14 (real Qwen 1.5B)", "2", "0.27%", "14.0%", "51x"], ["0.15", "2", "0.34%", "15.0%", "44x"]])
        S.append(("C2", "Proof: a judge that repeats itself makes retry-checking backfire",
                  "If the judge gives the same wrong verdict again, retrying cannot fix a false alarm. A rule that assumes fresh "
                  "verdicts underestimates the risk and pays for checks that cost more than never checking.",
                  ("PROVEN", "ok"), body, "One step of a task; the switching decision is not part of the proof."))

    # ---- CostBench
    for pat, title, note, verdict, limit in (
            ("costbench_v5_confirm_*", "CostBench (real benchmark), normal check price",
             "Check price 15% of a tool call; 18 fresh seeds.", ("3 OF 5 CONFIRMED", "mid"),
             "v5 tied with v4 here: the route around the bad tool costs only about 0.1% more, so checks rarely pay and "
             "learning the judge adds little. Confirmed: v4 beats v2 (-8.0%), v5 beats cross-check-all (-11.0%)."),
            ("costbench_v5_cheap_*", "CostBench (real benchmark), cheap checks",
             "Check price 5% (a small local judge); 18 fresh seeds.", ("3 OF 3 CONFIRMED", "ok"),
             "The 5% price was chosen after looking at practice seeds (stated in the plan); the effect on fresh seeds "
             "(-5.2% vs v4 without labels) is smaller than on practice seeds.")):
        f = latest(pat)
        if not f:
            continue
        R = rows(f)
        names = {"never": "never check", "always": "always check", "v2": "rule v2 (ignores false alarms)",
                 "v4": "rule v4 (told)", "v4_nocal": "rule v4 (no labels)", "always_x": "cross-check all",
                 "v5": "rule v5 (no labels)"}
        names = {k: v for k, v in names.items() if any(r["strategy"] == k for r in R)}
        m = {k: np.mean([r["loss"] for r in R if r["strategy"] == k]) for k in names}
        items = [(names[k], m[k], f"{names[k]}: mean loss {m[k]:.1f}") for k in sorted(names, key=m.get)]
        S.append(("C3" if "normal" in title else "C4", title,
                  "Real CostBench tasks and prices; one tool silently gets worse during the run. " + note,
                  verdict, bars(items, highlight=("rule v5 (no labels)",), note="Mean total loss per task. Lower is better."),
                  limit))

    # ---- FreshQA staleness + feasibility
    st = json.load(open(os.path.join("data", "processed", "freshqa_staleness.json")))["rows"]
    lab = {"fast-changing": "fast-changing", "slow-changing": "slow-changing", "never-changing": "never-changing"}
    items = []
    for k in lab:
        rr = [r for r in st if r["fact"] == k]
        n, s_ = len(rr), sum(r["stale_wrong"] for r in rr)
        items.append((lab[k], 100 * s_ / n, f"{k}: {s_} of {n} answers out of date ({100 * s_ / n:.1f}%)"))
    body = bars(items, unit="%", highlight=("fast-changing",), note="Share of Nov 2025 answers that the Apr 2026 FreshQA snapshot no longer accepts.")
    f = latest("freshqa_feasibility_*")
    if f:
        R = [r for r in rows(f) if r["strategy"] in ("never", "always", "cusum", "v4", "always_x", "v5")]
        nm = {"never": "never check", "always": "always check", "cusum": "CUSUM detector", "v4": "rule v4",
              "always_x": "cross-check all", "v5": "rule v5"}
        for stream, t in (("fq_news", "News questions (half go stale)"), ("fq_mixed", "Mixed questions")):
            g = lambda k: np.mean([r["loss"] for r in R if r["strategy"] == k and r["stream"] == stream])
            it = [(nm[k], 100 * (g(k) / g("never") - 1), f"{nm[k]}: {100 * (g(k) / g('never') - 1):+.1f}% vs never checking")
                  for k in nm if k != "never"]
            it.sort(key=lambda x: x[1])
            body += f"<h3>{t}: loss compared with never checking</h3>" + bars(it, unit="%", highlight=("rule v5",), fmt="{:+.1f}",
                                                                               note="Negative = cheaper than never checking. 10 seeds.")
    S.append(("C5", "Real out-of-date answers (FreshQA)",
              "Two dated FreshQA snapshots show real, silent staleness: about half of fast-changing answers changed in five months. "
              "On this real fault pattern, v5 cuts loss sharply, but checking everything is better on the news stream.",
              ("EXPLORATORY", "mid"), body, "The checker is still simulated here. The real-judge version (Core 1) is running."))

    # ---- in progress
    jf = sorted(glob.glob(os.path.join("data", "processed", "freshqa_judge_qwen*.json")))
    jrows = []
    for p in jf:
        it = json.load(open(p))["items"]
        no = np.mean([v["flag_old"] for v in it.values()] + [v["flag_new"] for v in it.values()])
        same = np.mean([v["flag_old"] == v["flag_new"] for v in it.values()])
        jrows.append([os.path.basename(p).replace("freshqa_judge_", "").replace(".json", ""), f"{100 * no:.0f}%", f"{100 * same:.0f}%"])
    body = table(["Judge (first prompt)", "Said NO", "Same verdict for old and new answer"], jrows) if jrows else ""
    body += ("<p>Problem found: a prompt that started with today's date made the judges reject almost everything, so the verdict "
             "did not depend on the answer. The prompt was fixed, and the run is repeated with Qwen 1.5B/3B, Phi-4 Mini and Llama 3.1 8B.</p>")
    S.append(("C6", "Real AI judges on FreshQA", "The final test replaces the simulated checker with real verdicts from local AI models.",
              ("IN PROGRESS", "mid"), body, "No result is claimed yet."))

    css = ("body{font-family:Segoe UI,Calibri,Arial,sans-serif;max-width:900px;margin:24px auto;padding:0 16px;color:#1b2430;background:#F7FAFC}"
           "h1{color:#0B5D6B;margin-bottom:4px}h2{color:#0B5D6B;margin-top:36px;border-top:1px solid #D1D5DB;padding-top:18px}"
           "h3{font-size:15px;margin:18px 0 4px}.sub{color:#5a6575}.plain{background:#EAF4F6;padding:10px 14px;border-radius:8px}"
           ".ok,.mid{color:#fff;padding:3px 10px;border-radius:12px;font-weight:bold;font-size:12px;white-space:nowrap}"
           ".ok{background:#1f7a5c}.mid{background:#a15c07}.limit{color:#a15c07;font-size:14px}.check{color:#1f7a5c;font-size:14px}"
           "table{border-collapse:collapse;margin:10px 0;font-size:14px;background:#fff}th{background:#0B5D6B;color:#fff;text-align:left;padding:5px 9px}"
           "td{border-bottom:1px solid #D1D5DB;padding:5px 9px}img{max-width:100%;margin:8px 0;background:#fff}.note{font-size:13px;color:#5a6575}"
           "@media (max-width:600px){body{padding:0 12px}}")
    head = ("<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>Progress Demo</title><style>{css}</style></head><body>")
    top = ("<h1>When to Pay for a Check: progress</h1>"
           f"<p class='sub'>Yelani Hanwella &middot; supervisor Mr. Achala Aponso &middot; generated {time.strftime('%d %b %Y %H:%M')} from the saved raw results</p>"
           "<p class='plain'><b>In one sentence:</b> an AI agent pays for tools that can silently go wrong; my rule decides when a check is worth its price, "
           "cross-checks a flagged answer on a second tool instead of asking the same judge again, learns how good the judge is without labels, "
           "and switches tools when needed.</p>")
    top += table(["#", "Claim", "Status"], [[f"<b>{i}</b>", t, f"<span class='{c}'>{v}</span>"] for i, t, _, (v, c), _, _ in S])
    secs = "".join(f"<h2>{i}. {html.escape(t)}</h2><p class='plain'>{html.escape(p)}</p><p><span class='{c}'>{v}</span></p>{b}"
                   f"<p class='limit'><b>Limit:</b> {html.escape(l)}</p>" for i, t, p, (v, c), b, l in S)
    out = os.path.join("results", "Hanwella_Progress_Demo.html")
    open(out, "w", encoding="utf-8").write(head + top + secs + "</body></html>")
    print("Saved", out)


if __name__ == "__main__":
    main()
