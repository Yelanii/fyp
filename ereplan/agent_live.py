"""D1: the rule on live model-backed tools with NATURAL silent degradation (20 Nov 2026). See PREREGISTRATION_D1.md.

What is real here (unlike realagent.py, whose calculator faults are injected):
- the tools are solver services backed by real models (tools_live.SolverService);
- the degradation is a provider-side model swap: service A answers with qwen2.5:3b until a seeded point in the run,
  then silently with qwen2.5:1.5b. Its wrong answers are the model's own mistakes; nothing is injected;
- loud failures are real: a solution with no usable final number;
- the checker is llama3.1:8b judging the whole worked solution (genuinely uncertain);
- the cross-check runs the problem on the other service (phi4-mini) and compares the final numbers exactly;
- every service is deterministic (temperature 0): a retry of the same service on the same problem returns the same
  answer, and the checker repeats its verdict on it (pi = 1 as measured, not set).

Every model answer is produced once (`prepare`) and cached, so all strategies and seeds see the same answers and the
run replays exactly. Problems: 201-500 of the subset-seed-11 shuffle of the GSM8K test set (Study M2's problems).
The rule's priors and the told rates come from Study M (problems 1-200), which is disjoint.

Usage:  python -m ereplan.agent_live prepare          # model calls (needs Ollama; resumable)
        python -m ereplan.agent_live run dev          # seeds 7000-7004, pipeline check
        python -m ereplan.agent_live run confirm      # seeds 7100-7119, the pre-registered test
"""
import itertools, json, os, sys, time, zlib
import numpy as np
from scipy.stats import wilcoxon

if "EREPLAN_NETPV" not in os.environ:
    os.environ["EREPLAN_NETPV"] = "1"            # the corrected check criterion, as in every result for the rule
from .config import Setting, Tool
from .strategies import REGISTRY
from . import crosscheck, rule_v6  # noqa: F401  (registers the cross-check rules and the fixed-tool baselines)
from .v5_exp import STRATS as V5
from .tools_live import SolverService, Checker, load_gsm8k, same_number

MODELS = {"A_before": "qwen2.5:3b", "A_after": "qwen2.5:1.5b", "B": "phi4-mini"}
CHECKER = "llama3.1:8b"
SUBSET_SEED, FIRST, N_PROBLEMS = 11, 200, 300
TABLE = os.path.join("data", "processed", "d1_table.json")

# Study M (problems 1-200; results/assumptions_confirm_20261118-131727/report.md). Used as the rule's priors (the
# services' advertised accuracies) and as the labelled calibration given to the "told" strategies.
ADV = {"A": 0.660, "B": 0.850}               # qwen2.5:3b and phi4-mini accuracy on problems 1-200
TOLD_Q, TOLD_F = 68 / 151, 11 / 239          # llama3.1:8b on the Qwen solvers, pooled: q 36/89 + 32/62, f 4/107 + 7/132
RHO = 0.10                                   # loud share of failures, pooled over the three solvers: (0.02+0.03+0.05)/(0.465+0.34+0.15)

PRICE_A = 20.0
# (wrong-answer cost L, price of B). Chosen from Study M's accuracies so that, by the per-call cost
# g(c, p) = c/p + (1 - p)(1 - rho)L, service A is the better buy before its swap (p = 0.660) and B after it (A at the
# 1.5B model's 0.535; B at 0.850). Break-even ranges: L = 100 -> 40 < price of B < 56; L = 200 -> 55 < price of B < 80.
CONDS = ((100.0, 45.0), (100.0, 52.0), (200.0, 62.0), (200.0, 74.0))
SEEDS = {"dev": tuple(range(7000, 7005)), "confirm": tuple(range(7100, 7120))}
STRATS = {k: V5[k] for k in ("never", "always", "cusum", "v4", "v4_nocal", "always_x", "v5_told", "v5")}
STRATS["fix_B"] = ("R_fix_B", dict(window=30), "true")
RNG_ALIAS = {"v5_told": "v5"}


# ----------------------------------------------------------------------------- 1. model answers (live, cached)
def prepare(llms=None, log=print, n=N_PROBLEMS):
    llms = {} if llms is None else llms
    tasks = load_gsm8k(FIRST + n, seed=SUBSET_SEED)[FIRST:]
    chk = Checker(CHECKER, price=0, llms=llms)
    table = {"problems": [t["id"] for t in tasks], "truth": [t["truth"] for t in tasks], "out": {}}
    t0 = time.time()

    def save():
        for l in llms.values():
            l.save()

    for key, model in MODELS.items():                    # one model at a time, so Ollama loads each model once
        svc = SolverService(key, 0, model, llms=llms)
        rows = []
        for i, task in enumerate(tasks):
            o = svc(task)
            rows.append({"value": o["value"], "correct": o["correct"], "loud": o["loud"], "text": o["text"]})
            if (i + 1) % 25 == 0:
                save(); log(f"  {model}: {i + 1}/{n} solutions ({time.time() - t0:.0f} s)")
        table["out"][key] = rows
        save()
    for key in MODELS:                                     # then the checker on every solution with a number
        for i, task in enumerate(tasks):
            o = table["out"][key][i]
            o["flag"] = None if o["loud"] else bool(chk(task, o, "maths")["flag"])
            if (i + 1) % 25 == 0:
                save(); log(f"  checker {CHECKER} on {MODELS[key]}: {i + 1}/{n} ({time.time() - t0:.0f} s)")
        save()
    for rows in table["out"].values():
        for o in rows:
            o.pop("text")
    os.makedirs(os.path.dirname(TABLE), exist_ok=True)
    json.dump(table, open(TABLE, "w"), indent=0)
    log(f"Saved {TABLE} ({time.time() - t0:.0f} s)")
    return table


# ----------------------------------------------------------------------------- 2. one run of one strategy
def make_setting(price_b, L, told):
    tools = (Tool("A_qwen", PRICE_A, 1.0, ADV["A"], ADV["A"]), Tool("B_phi4", price_b, 1.0, ADV["B"], ADV["B"]))
    s = Setting(tools=tools, steps_per_task=1, n_tasks=N_PROBLEMS, rho=RHO, q_true=TOLD_Q, q_assumed=TOLD_Q,
                false_alarm=TOLD_F, fa_persistence=1.0, check_frac=0.15)
    s = s.with_(leak_mult=L / s.mean_price)               # an accepted wrong answer costs exactly L
    if told == "none":
        s = s.with_(q_assumed=0.5, fa_assumed=0.0)
    return s


def run_one(table, key, seed, price_b, L, n=None):
    out = table["out"]
    N = len(table["truth"]) if n is None else n
    r = np.random.default_rng(zlib.crc32(f"d1|{seed}".encode()))
    order = r.permutation(len(table["truth"]))[:N]
    t_swap = int(r.integers(N // 4, N // 2))              # service A is silently swapped to the weaker model here
    name, params, told = STRATS[key]
    s = make_setting(price_b, L, told)
    params = dict(params)
    hm, cap = params.pop("horizon_mode", "task"), params.pop("session_cap", 50)
    st = REGISTRY[name](s, np.random.default_rng(zlib.crc32(f"strat|{RNG_ALIAS.get(key, key)}|{seed}".encode())), **params)
    st.horizon_mode, st.session_cap = hm, cap
    xcheck = bool(getattr(st, "crosscheck", False))
    prices = [x.price for x in s.tools]

    def answer(k, i, t):
        return out["B"][i] if k == 1 else out["A_after" if t >= t_swap else "A_before"][i]

    spend = wrong = failed = checks = xchecks = 0.0
    on_a_after = correct_a_after = 0
    for t, i in enumerate(order):
        ctx = {"t": t, "u": 1, "cur": None, "left_in_run": N - t}
        cur = st.start_task(ctx)
        ctx = {"t": t, "u": 1, "cur": cur, "left_in_run": N - t}
        act = st.decide(ctx, allow_switch=True)
        if act == "switch":
            spend += s.switch_cost
            cur = st.switch_to(ctx)
            ctx = {"t": t, "u": 1, "cur": cur, "left_in_run": N - t}
            act = st.decide(ctx, allow_switch=False)
        chk = act == "call_and_check"
        o = answer(cur, i, t)
        if cur == 0 and t >= t_swap:
            on_a_after += 1; correct_a_after += int(o["correct"])
        final = None
        for att in range(3):                               # first call and up to two retries; a retry repeats the answer
            spend += prices[cur] + (s.check_price if chk else 0.0)
            checks += chk
            if o["loud"]:
                st.observe(cur, chk, True, kind="loud")
                continue
            flagged = chk and bool(o["flag"])
            if flagged and xcheck:
                jx = st.crosscheck_tool(ctx)
                a_hat = st.alt_mean(jx)
                spend += prices[jx]; xchecks += 1
                alt = answer(jx, i, t)
                st.observe(jx, False, alt["loud"], kind="loud" if alt["loud"] else "none")
                if alt["loud"]:
                    st.observe(cur, chk, True, kind="flag_altloud", a=a_hat)
                    continue
                if same_number(alt["value"], o["value"]):
                    st.observe(cur, chk, False, kind="flag_agree", a=a_hat); final = o
                else:
                    st.observe(cur, chk, True, kind="flag_disagree", a=a_hat); final = alt
                break
            if flagged:
                st.observe(cur, chk, True, kind="caught")
                continue
            st.observe(cur, chk, False, kind="none"); final = o
            break
        if final is None:
            failed += 1
        elif not final["correct"]:
            wrong += 1
    F = s.mean_price                                      # a known failure costs one call, to redo the task
    return dict(strategy=key, seed=seed, price_b=price_b, L=L, loss=(spend + L * wrong + F * failed) / N,
                wrong_rate=wrong / N, fail_rate=failed / N, checks_per_task=checks / N, xchecks_per_task=xchecks / N,
                t_swap=int(t_swap), acc_a_after=(correct_a_after / on_a_after if on_a_after else None),
                f_hat=(st.cm.f_mean if hasattr(st, "cm") else None), q_hat=(st.cm.q_mean if hasattr(st, "cm") else None))


# ----------------------------------------------------------------------------- 3. the experiment
def _boot(x, y, n=10000, seed=0):
    d = 100 * (x / y - 1)
    r = np.random.default_rng(seed)
    m = [100 * (x[ix].mean() / y[ix].mean() - 1) for ix in r.integers(0, len(x), (n, len(x)))]
    return np.percentile(m, 2.5), np.percentile(m, 97.5)


def run(which, table=None):
    table = table or json.load(open(TABLE))
    seeds = SEEDS[which]
    t0 = time.time()
    rows = [run_one(table, k, sd, pb, Lc) for k, sd, (Lc, pb) in itertools.product(STRATS, seeds, CONDS)]
    sm = lambda k, f=lambda r: True: np.array([np.mean([r["loss"] for r in rows if r["strategy"] == k and r["seed"] == sd and f(r)]) for sd in seeds])
    av = lambda k, field: np.mean([r[field] for r in rows if r["strategy"] == k and r[field] is not None])
    out = table["out"]
    acc = {k: np.mean([o["correct"] for o in v]) for k, v in out.items()}
    L = [f"# D1: the rule on live model-backed tools with natural degradation ({which}), seeds {seeds[0]}-{seeds[-1]}", "",
         f"{len(table['truth'])} GSM8K problems (201-500, subset seed {SUBSET_SEED}); {len(rows)} runs; {time.time() - t0:.0f} s.", "",
         "Service accuracy on these problems: " + ", ".join(f"{MODELS[k]} {acc[k]:.3f}" for k in MODELS) + ".", "",
         "| Strategy | total loss | wrong answers kept | failed tasks | checks/task | cross-checks/task |", "|---|---|---|---|---|---|"]
    for k in STRATS:
        L.append(f"| {k} | {sm(k).mean():.1f} | {100 * av(k, 'wrong_rate'):.1f}% | {100 * av(k, 'fail_rate'):.1f}% | "
                 f"{av(k, 'checks_per_task'):.2f} | {av(k, 'xchecks_per_task'):.2f} |")
    L += ["", "| B price | wrong-answer cost | " + " | ".join(STRATS) + " |", "|---|---|" + "---|" * len(STRATS)]
    for Lc, pb in CONDS:
        L.append(f"| {pb:g} | {Lc:g} | " + " | ".join(f"{sm(k, lambda r: r['price_b'] == pb and r['L'] == Lc).mean():.1f}" for k in STRATS) + " |")
    fh = [r["f_hat"] for r in rows if r["strategy"] == "v5" and r["f_hat"] is not None]
    L += ["", f"Rule's learned f: median {np.median(fh):.3f} (Study M calibration: {TOLD_F:.3f})."]
    tests = {"H-L1 the rule (no labels) below the retrying rule without labels": ("v5", "v4_nocal"),
             "H-L3 the rule below never checking": ("v5", "never")}
    ps = {h: (1.0 if np.allclose(sm(a), sm(b)) else float(wilcoxon(sm(a), sm(b), alternative="less").pvalue)) for h, (a, b) in tests.items()}
    order = sorted(ps, key=ps.get); holm, stop = {}, False
    for j, h in enumerate(order):
        holm[h] = (not stop) and ps[h] < 0.05 / (len(order) - j); stop = stop or not holm[h]
    L += ["", "## Pre-registered hypotheses (PREREGISTRATION_D1.md)", ""]
    for h, (a, b) in tests.items():
        x, y = sm(a), sm(b)
        L.append(f"- {h}: {x.mean():.1f} vs {y.mean():.1f} ({100 * (x.mean() / y.mean() - 1):+.1f}%), one-sided Wilcoxon p = {ps[h]:.2g}, "
                 f"Holm {'ok' if holm[h] else 'fail'} -> **{'CONFIRMED' if holm[h] else 'NOT CONFIRMED'}**")
    x, y = sm("v5"), sm("v4")
    lo, hi = _boot(x, y)
    L.append(f"- H-L2 the rule within +3% of the retrying rule told q and f: {x.mean():.1f} vs {y.mean():.1f} "
             f"({100 * (x.mean() / y.mean() - 1):+.1f}%, 95% CI {lo:+.1f}% to {hi:+.1f}%) -> **{'CONFIRMED' if hi <= 3 else 'NOT CONFIRMED'}**")
    for k in ("fix_B", "always", "always_x", "cusum", "v5_told"):
        x, y = sm("v5"), sm(k)
        lo, hi = _boot(x, y)
        L.append(f"- Descriptive: the rule vs {k}: {x.mean():.1f} vs {y.mean():.1f} ({100 * (x.mean() / y.mean() - 1):+.1f}%, 95% CI {lo:+.1f}% to {hi:+.1f}%)")
    outdir = os.path.join("results", f"d1_{which}_{time.strftime('%Y%m%d-%H%M%S')}"); os.makedirs(outdir, exist_ok=True)
    json.dump(rows, open(os.path.join(outdir, "rows.json"), "w"))
    rep = "\n".join(L); open(os.path.join(outdir, "report.md"), "w", encoding="utf-8").write(rep)
    print(rep); print("Saved to", outdir)
    return rows


if __name__ == "__main__":
    if sys.argv[1:2] == ["prepare"]:
        prepare()
    elif sys.argv[1:2] == ["run"]:
        run(sys.argv[2] if len(sys.argv) > 2 else "dev")
    else:
        print(__doc__)
