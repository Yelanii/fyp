"""FR16/FR17 (10 Nov 2026): FreshQA with two real judge families -- development run and confirmatory test.
See PREREGISTRATION_freshqa.md. Real verdicts come from the cached judge files (collected on the student's laptop
with Ollama at temperature 0); no model is called here.

Usage: python3 run_freshqa_confirm.py dev      # development seeds 2500-2509, Phi-4 Mini only, candidate rules
       python3 run_freshqa_confirm.py confirm  # seeds 2700-2719, both judges, frozen design
"""
import os, sys, itertools, json, time
os.environ.setdefault("EREPLAN_FMAX", "0.95")
from multiprocessing import Pool
import numpy as np
from scipy.stats import wilcoxon
from ereplan import freshqa_real as fr, runner, rule_rho  # noqa: F401
from ereplan.config import Tool
from ereplan.v5_exp import setting, SESSION

JUDGES = ("phi4-mini@plain", "llama3.1:8b@plain")
STREAMS, PSTALE, BPRICE = ("fqr_news", "fqr_mixed"), (100, 50, 25), (24.0, 30.0)
SEEDS = {"dev": tuple(range(2500, 2510)), "confirm": tuple(range(2700, 2720))}
BASE = fr._strats(JUDGES[0])
STRATS = {k: BASE[k] for k in ("never", "use_B", "always_x", "v4", "v5")}
STRATS.update(rho_cap=("Rule_v5_rho", dict(SESSION), "none"), rho_mean=("Rule_v5_rho_mean", dict(SESSION), "none"),
              rho_lcb=("Rule_v5_rho_lcb", dict(SESSION), "none"), rho_noaudit=("Rule_v5_rho_noaudit", dict(SESSION), "none"))
PROPOSED = "rho_cap"           # frozen in PREREGISTRATION_freshqa.md: the variant FR20 confirmed, not the dev-best
CONFIRM_KEYS = ("never", "use_B", "always_x", "v4", "v5", PROPOSED, "rho_noaudit")
_CAL = {}


def job(a):
    key, judge, stream, ps, pb, seed = a
    if judge not in _CAL:
        _CAL[judge] = fr.measure(judge, quiet=True)
    name, params, told = STRATS[key]
    c = _CAL[judge][stream[4:]]
    tools = (Tool("A_cheap", 20.0, 1.0, 0.95, 0.95), Tool("B_mid", pb, 1.0, 0.95, 0.95), Tool("C_premium", pb + 6, 1.0, 0.97, 0.95))
    s = setting(min(max(c["q"], 0.05), 0.99), 3.0, min(c["f"], 0.95), 1.0, told).with_(tools=tools)
    r = runner.run(name, dict(params), s, f"{stream}@p{ps}|{judge}", seed)
    return dict(strategy=key, judge=judge, stream=stream, p_stale=ps, b_price=pb, seed=seed, loss=r["total_loss_fail"],
                leak_rate=r["leak_rate"], fail_rate=r["fail_rate"], checks=r["checks_per_task"], switches=r["switches"],
                rho_hat=r.get("rho_hat"))


def _p(x, y):
    return 1.0 if np.allclose(x, y) else float(wilcoxon(x, y, alternative="less").pvalue)


def _ci(x, y, n=10000):
    idx = np.random.default_rng(0).integers(0, len(x), (n, len(x)))
    d = 100 * (x[idx].mean(axis=1) / y[idx].mean(axis=1) - 1)
    return float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))


def main(which):
    seeds = SEEDS[which]
    keys = list(STRATS) if which == "dev" else list(CONFIRM_KEYS)
    judges = JUDGES[:1] if which == "dev" else JUDGES
    jobs = list(itertools.product(keys, judges, STREAMS, PSTALE, BPRICE, seeds))
    t0 = time.time()
    with Pool(os.cpu_count() or 2) as pool:
        rows = pool.map(job, jobs, chunksize=4)
    sm = lambda k, filt=lambda r: True: np.array([np.mean([r["loss"] for r in rows if r["strategy"] == k and r["seed"] == sd and filt(r)]) for sd in seeds])
    L = [f"# FreshQA with real judges ({which}): seeds {seeds[0]}-{seeds[-1]}; judges {', '.join(judges)}", "",
         f"{len(rows)} runs; {time.time() - t0:.0f} s. Conditions per seed and judge: stream {{news, mixed}} x tool A goes stale in "
         "{100, 50, 25}% of runs x price of tool B {24, 30} (A costs 20). Wrong answer = 3 tasks. Metric: total loss per task.", "",
         "| Strategy | all | stale 100% | 50% | 25% | B at 24 | B at 30 | news | mixed | wrong kept | failed | checks/task |", "|---|" + "---|" * 11]
    for k in keys:
        g = lambda f: np.mean([r[f] for r in rows if r["strategy"] == k])
        c = lambda fn: f"{sm(k, fn).mean():.1f}"
        L.append(f"| {k} | {sm(k).mean():.1f} | {c(lambda r: r['p_stale'] == 100)} | {c(lambda r: r['p_stale'] == 50)} | {c(lambda r: r['p_stale'] == 25)} | "
                 f"{c(lambda r: r['b_price'] == 24)} | {c(lambda r: r['b_price'] == 30)} | {c(lambda r: r['stream'] == 'fqr_news')} | "
                 f"{c(lambda r: r['stream'] == 'fqr_mixed')} | {g('leak_rate'):.1%} | {g('fail_rate'):.1%} | {g('checks'):.2f} |")
    if which == "confirm":
        P = sm(PROPOSED); prim = {}
        for hid, b in (("H-F1", "use_B"), ("H-F2", "never"), ("H-F3", "v5")):
            y = sm(b); prim[hid] = (_p(P, y), b, y.mean()) + _ci(P, y)
        order = sorted(prim, key=lambda h: prim[h][0]); holm, stop = {}, False
        for j, h in enumerate(order):
            holm[h] = (not stop) and prim[h][0] < 0.05 / (len(order) - j); stop = stop or not holm[h]
        L += ["", "## Pre-registered hypotheses (PREREGISTRATION_freshqa.md)", ""]
        for h in ("H-F1", "H-F2", "H-F3"):
            p, b, ym, lo, hi = prim[h]
            L.append(f"- {h} {PROPOSED} below {b}: {P.mean():.1f} vs {ym:.1f} ({100 * (P.mean() / ym - 1):+.1f}%, 95% CI {lo:+.1f}% to {hi:+.1f}%), "
                     f"Wilcoxon p = {p:.2g} over {len(seeds)} seeds, Holm {'ok' if holm[h] else 'fail'} -> **{'CONFIRMED' if holm[h] else 'NOT CONFIRMED'}**")
        f4 = lambda r: r["p_stale"] == 25
        a, b = sm(PROPOSED, f4), sm("use_B", f4); p4 = _p(a, b); lo, hi = _ci(a, b)
        L.append(f"- H-F4 (secondary) where tool A goes stale in only 25% of runs, {PROPOSED} below use_B: {a.mean():.1f} vs {b.mean():.1f} "
                 f"({100 * (a.mean() / b.mean() - 1):+.1f}%, 95% CI {lo:+.1f}% to {hi:+.1f}%), p = {p4:.2g} -> **{'CONFIRMED' if p4 < 0.05 else 'NOT CONFIRMED'}**")
        L += ["", "## Per judge (descriptive)", "", "| Judge | " + " | ".join(keys) + " |", "|---|" + "---|" * len(keys)]
        for j in judges:
            L.append(f"| {j} | " + " | ".join(f"{sm(k, lambda r, j=j: r['judge'] == j).mean():.1f}" for k in keys) + " |")
        L += ["", f"## {PROPOSED} vs use_B by cell (descriptive; negative = the rule is cheaper)", "", "| stream | stale in | B price | rule | use_B | diff |", "|---|---|---|---|---|---|"]
        for st, ps, pb in itertools.product(STREAMS, PSTALE, BPRICE):
            fn = lambda r: r["stream"] == st and r["p_stale"] == ps and r["b_price"] == pb
            a, b = sm(PROPOSED, fn).mean(), sm("use_B", fn).mean()
            L.append(f"| {st[4:]} | {ps}% | {pb:.0f} | {a:.1f} | {b:.1f} | {100 * (a / b - 1):+.1f}% |")
    out = os.path.join("results", f"freshqa_{which}_{time.strftime('%Y%m%d-%H%M%S')}"); os.makedirs(out, exist_ok=True)
    json.dump(rows, open(os.path.join(out, "rows.json"), "w"))
    rep = "\n".join(L); open(os.path.join(out, "report.md"), "w").write(rep); print(rep); print("Saved to", out)


if __name__ == "__main__":
    main(sys.argv[1])
