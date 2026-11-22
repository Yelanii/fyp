"""Five-minute demonstration of the rule.

    python -m ereplan.showcase

Part 1  Watch rule v4 decide, call by call, in one simulated run where the cheap tool quietly degrades
        and the checker raises persistent false alarms (as the real LLM checkers did).
Part 2  The same run for every strategy: who loses least, and why.
Part 3  Replay of the real-LLM test (qwen2.5:1.5b, seeds 3000-3002) from the saved answers, no Ollama needed.
Part 4  The confirmed findings, each from a pre-registered test.
A plot of Part 1 is saved to results/showcase_v4.png.
"""
import json, os, re, zlib
import numpy as np

from .config import Setting
from .runner import run

SESSION = dict(window=60, epsilon=0.02, k=3, horizon_mode="session", session_cap=50)
STRATS = {
    "Never check": ("B2_never", dict(window=30)),
    "Always check": ("B1_always", dict(window=30)),
    "Change alarm (CUSUM)": ("B4_cusum", dict(h=6, p1=0.8)),
    "Rule v2": ("Rule_leakaware", dict(SESSION)),
    "Rule v3": ("Rule_v3_selfcal", dict(SESSION, q_prior_strength=3.0)),
    "Rule v4 (ours)": ("Rule_v4_fa", dict(SESSION, q_prior_strength=3.0)),
}
SEED, SCENARIO = 5000, "drop_0.75"          # seed 5000 is used only for this demonstration


def line(c="-"):
    print(c * 78)


def part1(s):
    line("=")
    print("PART 1  One run, call by call: the cheap tool (A_cheap, price 20) silently drops from 95% to 75%")
    print("        success at a random moment. Half of its failures are loud (an error), half are silent")
    print("        (a wrong answer). A check costs 3.7, catches 95% of silent failures, but wrongly")
    print(f"        rejects {s.false_alarm:.0%} of correct steps, every time it is asked (like the real LLM checker).")
    print("        A wrong answer that slips through costs 3 tasks. The agent does NOT know when the drop happens.")
    line("=")
    res = run("Rule_v4_fa", STRATS["Rule v4 (ours)"][1], s, SCENARIO, SEED, record=True)
    tr = res["trace"]
    names = [t.name for t in s.tools]
    from .env import Environment
    t0 = int(np.argmax(Environment(s, SCENARIO, SEED).p[0] < 0.9))
    print(f"(Hidden from the agent: the drop happens at call {t0}.)\n")
    shown, last = 0, None
    for x in tr:
        key = (x["action"], x["tool"])
        near_drop = t0 - 3 <= x["t"] <= t0 + 400
        if x["action"] == "switch" or (key != last and shown < 14 and (x["t"] < 12 or near_drop)):
            pv, dv, fa = x.get("pv", 0.0), x.get("dv", 0.0), x.get("fa_cost", 0.0)
            why = (f"value of a check {pv + dv:5.1f} - false-alarm risk {fa:4.1f} vs price {s.check_price:.1f}"
                   if "pv" in x else "")
            if x["action"] == "switch":
                msg = f"SWITCH away from {names[x['tool']]}: its whole likely range ({x['low']:.0%}-{x['high']:.0%}) is now below the switch line ({x['line']:.0%})"
            elif x["action"] == "call_and_check":
                msg = f"call {names[x['tool']]} and PAY FOR A CHECK  ({why}{'; random audit' if x.get('audit') else ''})"
            else:
                msg = f"call {names[x['tool']]}, skip the check   ({why})"
            print(f"  call {x['t']:3d} | true success {x['true_p']:.0%} | agent's estimate {x['mean']:.0%} | {msg}")
            shown += 1
        last = key
    sw = [x["t"] for x in tr if x["action"] == "switch" and x["tool"] == 0 and x["t"] >= t0]
    if sw:
        print(f"\n  The agent left the degraded tool {sw[0] - t0} calls after the hidden drop, mostly from FREE loud errors,")
        print("  because with persistent false alarms it judged most checks not worth their price plus risk.")
    print(f"\n  Over 120 tasks: {res['checks_per_task']:.2f} checks per task, {res['switches']} switch(es), "
          f"{res['leak_rate']:.1%} of tasks leaked a wrong answer, {res['fail_rate']:.1%} failed.")
    _plot(tr, s, t0)
    return res


def _plot(tr, s, t0):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return
    rows = [x for x in tr if x["tool"] == 0 and x["action"] != "switch"]
    t = np.array([x["t"] for x in rows])
    fig, ax = plt.subplots(figsize=(11, 4.3))
    ax.fill_between(t, [x["low"] for x in rows], [x["high"] for x in rows], alpha=0.25, step="post",
                    label="agent's likely range for A_cheap's success rate")
    ax.plot(t, [x["true_p"] for x in rows], "k--", lw=1, label="true success rate (hidden from the agent)")
    ax.step(t, [x["line"] for x in rows], where="post", color="red", lw=1.2, label="switch line")
    chk = [x["t"] for x in rows if x["action"] == "call_and_check"]
    ax.scatter(chk, [0.42] * len(chk), marker="|", color="purple", s=40, label="paid for a check")
    for x in tr:
        if x["action"] == "switch" and x["tool"] == 0:
            ax.axvline(x["t"], color="green", lw=2, label="switched to another tool")
    ax.axvline(t0, color="grey", lw=1, ls=":", label="hidden moment of degradation")
    ax.set_ylim(0.4, 1.0); ax.set_xlabel("call number"); ax.set_ylabel("success rate")
    ax.set_title("Rule v4 in one simulated run (persistent false alarms 14%, wrong answer costs 3 tasks)")
    h, l = ax.get_legend_handles_labels(); u = dict(zip(l, h))
    ax.legend(u.values(), u.keys(), fontsize=8, loc="lower left")
    fig.tight_layout(); os.makedirs("results", exist_ok=True)
    fig.savefig(os.path.join("results", "showcase_v4.png"), dpi=130)


def part2(s, mine):
    line("=")
    print("PART 2  Exactly the same world (same random outcomes) for every strategy")
    line("=")
    print(f"  {'Strategy':22s} {'total loss/task':>15s} {'checks/task':>11s} {'wrong answers':>13s} {'failed tasks':>12s}")
    rows = []
    for label, (name, p) in STRATS.items():
        r = mine if name == "Rule_v4_fa" else run(name, p, s, SCENARIO, SEED)
        rows.append((label, r))
    best = min(r["total_loss_fail"] for _, r in rows)
    for label, r in rows:
        star = "  <- lowest" if r["total_loss_fail"] == best else ""
        print(f"  {label:22s} {r['total_loss_fail']:15.1f} {r['checks_per_task']:11.2f} {r['leak_rate']:13.1%} {r['fail_rate']:12.1%}{star}")
    print("\n  Total loss = money spent on tools and checks + 3 tasks' cost per wrong answer that slipped")
    print("  through + 1 task's cost per task that failed (e.g. because a false alarm blocked a correct step).")
    print("  This is ONE run; the claims rest on the pre-registered tests in Part 4, not on this example.")


def part3():
    line("=")
    print("PART 3  The real AI: replay of the laptop run with qwen2.5:1.5b (saved answers, no Ollama needed)")
    line("=")
    plans = os.path.join("data", "processed", "gsm8k_plans_qwen2.5_1.5b.json")
    cal = os.path.join("data", "processed", "judge_calibration_qwen2.5_1.5b.json")
    if not (os.path.exists(plans) and os.path.exists(cal)):
        print("  (Skipped: the saved real-AI files are not in data/processed on this computer.)")
        return
    os.environ["EREPLAN_REPLAY"] = "1"
    from .realagent import LLM, Judge, run_one, STRATS as RS
    llm = LLM("qwen2.5:1.5b")
    P, C = json.load(open(plans)), json.load(open(cal))
    judge = Judge(llm, C.get("judge", "recompute"))
    q, f = max(0.05, min(0.99, C["catch_rate_obvious"])), C["false_alarm_rate"]
    print(f"  Real checker: catches {C['catch_rate_obvious']:.0%} of wrong answers, wrongly rejects {f:.0%} of correct ones.")
    print(f"  {'Strategy':10s} " + "  ".join(f"{k:>7s}" for k in RS))
    res = {k: [] for k in RS}
    for sd in (3000, 3001, 3002):
        for k in RS:
            res[k].append(run_one(P["tasks"], judge, k, sd, 0.75, q, 0.15, 3.0, f_assumed=f)["total_loss"])
    print(f"  {'loss/task':10s} " + "  ".join(f"{np.mean(v):7.1f}" for v in res.values()))
    print(f"  (Tool A drops to 75%, wrong answer costs 3 tasks, 3 of the 10 test seeds; "
          f"{llm.misses} answers were not in the saved file.)")
    print("  Full pre-registered result (10 seeds, 4 conditions): v4 73.8 vs CUSUM 81.0, never 82.0,")
    print("  v3 86.4, v2 95.2, always 108.9 (all p < 1e-5).")


def part4():
    line("=")
    print("PART 4  What has been shown (every test written down before it was run; results folders in brackets)")
    line("=")
    for t in [
        "RQ1 When does checking pay?  Most at MODERATE silent degradation (the 'hump'). With a wrong answer",
        "    costing 3 tasks: median saving 31% at a drop to 75%, vs 9% at 95% and 18% at 60%",
        "    [checkmap_20261021-144627]. The hump survives false alarms (peak at 80%) [famap_...].",
        "RQ2 How does checking backfire?",
        "    (a) A check that shares the tool's blind spot: always-check WORSE than never-check in 16/16",
        "        conditions (204.7 vs 168.6) [confirm_selfcal_...].",
        "    (b) Real LLM checkers reject correct steps and repeat it: 14% (1.5B) / 5% (3B) false alarms,",
        "        repeated on retry 99% / 100% of the time; always-check failed 29% / 19% of tasks.",
        "RQ3 How should an agent decide?  Rule v4 (prices + wrong-answer loss + switching + imperfect checker):",
        "    simulation: 19% below v3, below never/always/CUSUM (p < 1e-26) [confirm_fa_...];",
        "    real LLM, fresh seeds: lowest loss with both checkers (vs CUSUM: 73.8 vs 81.0; 75.4 vs 77.6).",
        "Honest limits: one model family (Qwen2.5), arithmetic tasks only; v4 loses slightly to never-check",
        "    when the tool never degrades; the old rules v1-v2 lost in the real test (that is what led to v4).",
    ]:
        print("  " + t)


def main(argv=None):
    s = Setting().with_(q_true=0.95, q_assumed=0.95, check_frac=0.15, leak_mult=3.0, false_alarm=0.14)
    mine = part1(s)
    part2(s, mine)
    part3()
    part4()
    line("=")
    print("Plot of Part 1 saved to results/showcase_v4.png")


if __name__ == "__main__":
    main()
