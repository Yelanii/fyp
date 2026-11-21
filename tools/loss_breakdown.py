"""Where the loss comes from: what each strategy spent (tools, checks, cross-checks, switches) against what it lost
on wrong answers kept and failed tasks, for the main experiments. Reads the saved rows only; nothing is re-run.

    python tools/loss_breakdown.py
"""
import glob, json, os, sys
import numpy as np

sys.path.insert(0, os.getcwd())
ORDER = ("never", "always", "cusum", "v4", "v4_nocal", "always_x", "v5_told", "v5", "v5_fix", "v5_cal", "fix_B")
EXPS = [("Simulator, label-free rule (seeds 8200-8219)", "v5_confirm_*_netpv"),
        ("CostBench, real-checker rates (seeds 8400-8417)", "fr11_confirm_*_netpv"),
        ("Live tools, 200 seeds (seeds 7400-7599)", "d1power_confirm_*")]


def live_spend(r):
    """Live-tool rows store loss, wrong and failed shares; spend = loss - L x wrong - F x failed (agent_live.run_one)."""
    from ereplan import agent_live as d
    F = d.make_setting(r["price_b"], r["L"], "true").mean_price
    return r["loss"] - r["L"] * r["wrong_rate"] - F * r["fail_rate"]


def main():
    for title, pattern in EXPS:
        found = sorted(d for d in glob.glob(os.path.join("results", pattern)) if os.path.isdir(d))
        if not found:
            print(f"## {title}\n\nNo folder results/{pattern}.\n"); continue
        rows = json.load(open(os.path.join(found[-1], "rows.json")))
        rows = rows["rows"] if isinstance(rows, dict) else rows
        keys = [k for k in ORDER if any(r["strategy"] == k for r in rows)]
        keys += sorted({r["strategy"] for r in rows} - set(keys))
        print(f"## {title}\n\nFrom {found[-1]}. Per task, averaged over all runs.\n")
        print("| Strategy | total loss | spend | wrong answers and failed tasks | wrong kept | failed | checks/task |")
        print("|---|---|---|---|---|---|---|")
        for k in keys:
            R = [r for r in rows if r["strategy"] == k]
            loss = np.mean([r["loss"] for r in R])
            spend = np.mean([r["spend"] if "spend" in r else live_spend(r) for r in R])
            wrong = np.mean([r.get("leak_rate", r.get("wrong_rate", np.nan)) for r in R])
            fail = np.mean([r["fail_rate"] for r in R])
            chk = np.mean([r.get("checks", r.get("checks_per_task", np.nan)) for r in R])
            print(f"| {k} | {loss:.1f} | {spend:.1f} | {loss - spend:.1f} | {100 * wrong:.1f}% | {100 * fail:.1f}% | {chk:.2f} |")
        print()


if __name__ == "__main__":
    main()
