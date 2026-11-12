"""Core 4 (31 October 2026): cross-checking when two wrong outputs can agree (shared mistakes, sigma).

Usage: python -m ereplan.core4_exp dev        # development seeds 2600-2603
       python -m ereplan.core4_exp confirm    # seeds 2610-2629 (after PREREGISTRATION_core4.md)
"""
import argparse, itertools, json, os, time
from multiprocessing import Pool
import numpy as np

from .runner import run
from . import rule_v5s  # noqa: F401
from .v5_exp import STRATS as V5_STRATS, setting, DROPS, QS, LEAKS, FS, PIS, _p, _boot_ci, SESSION

SIGMAS = (0.0, 0.3, 0.6)
SEEDS = {"dev": tuple(range(2600, 2604)), "confirm": tuple(range(2610, 2630))}
S = {k: V5_STRATS[k] for k in ("never", "v4", "always_x", "v5")}
S["v5_s"] = ("Rule_v5_s", dict(SESSION), "none")


def _job(a):
    key, drop, q, lm, f, pi, sg, seed = a
    name, params, told = S[key]
    st = setting(q, lm, f, pi, told).with_(xc_shared=sg)
    r = run(name, dict(params), st, f"drop_{drop:.2f}", seed)
    return dict(strategy=key, drop=drop, q=q, leak_mult=lm, f=f, pi=pi, sigma=sg, seed=seed, loss=r["total_loss_fail"],
                leak_rate=r["leak_rate"], fail_rate=r["fail_rate"], checks=r["checks_per_task"],
                switches=r["switches"], f_hat=r.get("f_hat"), q_hat=r.get("q_hat_cm"))


def main(which, procs):
    seeds = SEEDS[which]
    jobs = [(k, *c, sd) for k in S for c in itertools.product(DROPS, QS, LEAKS, FS, PIS, SIGMAS) for sd in seeds]
    t0 = time.time()
    with Pool(procs) as pool:
        rows = pool.map(_job, jobs, chunksize=8)
    g = lambda k, fn, fld="loss": float(np.mean([r[fld] for r in rows if r["strategy"] == k and fn(r)
                                                   and r[fld] is not None]))
    L = [f"# Core 4: shared mistakes in cross-checks ({which} seeds {seeds[0]}-{seeds[-1]})", "",
         f"{len(rows)} runs; {time.time() - t0:.0f} s. 64 conditions x sigma {SIGMAS}.", "",
         "| Strategy | " + " | ".join(f"loss, sigma {s}" for s in SIGMAS) + " | " + " | ".join(f"f error, sigma {s}" for s in SIGMAS) + " |",
         "|---|" + "---|" * (2 * len(SIGMAS))]
    for k in S:
        cells = [f"{g(k, lambda r, s=s: r['sigma'] == s):.1f}" for s in SIGMAS]
        if k.startswith("v5"):
            cells += [f"{np.mean([r['f_hat'] - r['f'] for r in rows if r['strategy'] == k and r['sigma'] == s and r['f_hat'] is not None]):+.3f}"
                      for s in SIGMAS]
        else:
            cells += ["-"] * len(SIGMAS)
        L.append(f"| {k} | " + " | ".join(cells) + " |")
    sm = lambda k, s: np.array([np.mean([r["loss"] for r in rows if r["strategy"] == k and r["sigma"] == s and r["seed"] == sd])
                                for sd in seeds])
    L += ["", "## v5_s vs v5 by sigma (seed means)", ""]
    for s in SIGMAS:
        x, y = sm("v5_s", s), sm("v5", s)
        lo, hi = _boot_ci(x, y)
        L.append(f"- sigma {s}: v5_s {x.mean():.1f} vs v5 {y.mean():.1f} ({100 * (x.mean() / y.mean() - 1):+.2f}%, "
                 f"CI {lo:+.2f}% to {hi:+.2f}%), p = {_p(x, y):.2g}")
    for s in SIGMAS:
        x, y = sm("v5", s), sm("v4", s)
        L.append(f"- sigma {s}: v5 {x.mean():.1f} vs v4 {y.mean():.1f} ({100 * (x.mean() / y.mean() - 1):+.2f}%)")
    out = os.path.join("results", f"core4_{which}_{time.strftime('%Y%m%d-%H%M%S')}")
    os.makedirs(out, exist_ok=True)
    json.dump(rows, open(os.path.join(out, "rows.json"), "w"))
    open(os.path.join(out, "report.md"), "w").write("\n".join(L))
    print("\n".join(L)); print("Saved to", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("which", choices=tuple(SEEDS))
    ap.add_argument("--procs", type=int, default=os.cpu_count() or 2)
    a = ap.parse_args()
    main(a.which, a.procs)
