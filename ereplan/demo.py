"""Working demonstration (Section 3.3.5.10): one command that
  1. prints the rule's decision messages around a silent degradation,
  2. plots the tool's success-rate range against its switch line, with checks and switches marked,
  3. tabulates cost per successful task for the strategies on the same run.

Usage:  python -m ereplan.demo [--scenario S1_sudden] [--seed 0] [--params results/.../manifest.json]
"""
import argparse, json, os
import numpy as np

from .config import Setting, SCENARIOS
from .runner import run

DEFAULTS = {"Rule": dict(window=30, epsilon=0.05, k=3), "B1_always": dict(window=30),
            "B2_never": dict(window=30), "B3_fixed": dict(window=30, rate=0.1),
            "B4_cusum": dict(h=4, p1=0.7), "B8_fixed_est": dict(rate=0.1), "B6_oracle": dict()}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", default="S1_sudden", choices=SCENARIOS)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--params", help="manifest.json from a pilot run, to use its tuned settings")
    ap.add_argument("--out", default="results")
    a = ap.parse_args(argv)
    params = dict(DEFAULTS)
    if a.params:
        params.update({k: v for k, v in json.load(open(a.params))["chosen"].items() if k in DEFAULTS})
    s = Setting()
    os.makedirs(a.out, exist_ok=True)

    res = run("Rule", params["Rule"], s, a.scenario, a.seed, record=True)
    tr = res["trace"]
    print(f"\n=== Decision messages: rule on {a.scenario}, seed {a.seed} (simulated prices) ===")
    names = [t.name for t in s.tools]
    shown, last_tool = 0, None
    for x in tr:
        interesting = x["action"] != "call" or x["tool"] != last_tool
        last_tool = x["tool"]
        if interesting and (shown < 20 or x["action"] == "switch"):
            verb = {"switch": "SWITCHED from", "call_and_check": "Checked", "call": "Called"}[x["action"]]
            print(f"t={x['t']:3d}  {verb} {names[x['tool']]}: {x.get('reason', '')}  [true p = {x.get('true_p', float('nan')):.2f}]")
            shown += 1

    # plot the primary tool's range against its switch line
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    a_rows = [x for x in tr if x["tool"] == 0 and x["action"] != "switch"]
    t = np.array([x["t"] for x in a_rows])
    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.fill_between(t, [x["low"] for x in a_rows], [x["high"] for x in a_rows], alpha=0.25,
                    step="post", label="95% success-rate range (estimated)")
    ax.plot(t, [x["mean"] for x in a_rows], lw=1, label="estimated success rate")
    ax.plot(t, [x["true_p"] for x in a_rows], "k--", lw=1, label="true success rate (hidden)")
    ax.step(t, [x["line"] for x in a_rows], where="post", color="red", lw=1.2, label="switch line (moves with plan)")
    chk = [x for x in a_rows if x["action"] == "call_and_check"]
    ax.scatter([x["t"] for x in chk], [0.42] * len(chk), marker="|", color="purple", s=40, label="check")
    sw = [x for x in tr if x["action"] == "switch" and x["tool"] == 0]
    for x in sw:
        ax.axvline(x["t"], color="green", lw=2, label="switch away")
    ax.set_ylim(0.4, 1.0)
    ax.set_xlabel("call number")
    ax.set_ylabel("success rate of tool A_cheap")
    ax.set_title(f"e-Replan three-zone rule, {a.scenario}, seed {a.seed}")
    h, l = ax.get_legend_handles_labels()
    uniq = dict(zip(l, h))
    ax.legend(uniq.values(), uniq.keys(), fontsize=8, loc="lower left")
    fig.tight_layout()
    fig_path = os.path.join(a.out, f"demo_{a.scenario}_seed{a.seed}.png")
    fig.savefig(fig_path, dpi=130)

    print(f"\n=== Same run, all strategies (identical tool outcomes) ===")
    print(f"{'Strategy':14s} {'cost/success':>12s} {'checks/task':>11s} {'switches':>8s} {'leak rate':>9s}")
    for name, p in params.items():
        r = res if name == "Rule" else run(name, p, s, a.scenario, a.seed)
        print(f"{name:14s} {r['cost_per_success']:12.1f} {r['checks_per_task']:11.2f} {r['switches']:8d} {r['leak_rate']:9.3f}")
    print(f"\nPlot saved to {fig_path}")


if __name__ == "__main__":
    main()
