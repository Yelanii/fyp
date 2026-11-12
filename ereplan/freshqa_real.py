"""Core 1 (31 October 2026): FreshQA with a REAL LLM judge and REAL answer comparisons.

What is real and what is simulated
  real       questions and answers (FreshQA, Apache-2.0), which answers went stale between 24 Nov 2025 and
             21 Apr 2026, every check verdict (a local LLM judge, temperature 0), and every cross-check comparison
             (exact match after normalising, otherwise the same LLM asked whether the two answers say the same thing)
  simulated  the order of questions, the moment t0 at which tool A stops updating, and loud errors (timeouts):
             5% for tools A and B, 3% for C

Tools. A (price 20) is a live source until a random call t0 in [150, 350); from then on it silently serves its
24 Nov 2025 answers. B (24) and C (30) serve the 21 Apr 2026 answers. An answer is correct when FreshQA's April
2026 snapshot accepts it. Because the judge runs at temperature 0, a retry of the same question gets the same
verdict: false alarms repeat (pi = 1) as they do in practice, nothing is assumed.

Commands
  python -m ereplan.freshqa_real collect --model qwen2.5:1.5b   # on the laptop with Ollama; resumable
  python -m ereplan.freshqa_real measure --model qwen2.5:1.5b   # the judge's catch / false-alarm / comparison rates
  python -m ereplan.freshqa_real run --model qwen2.5:1.5b --seeds dev      # development seeds 2500-2509
  python -m ereplan.freshqa_real run --model qwen2.5:1.5b --seeds confirm  # pre-registered seeds 2510-2529
"""
import argparse, hashlib, json, os, re, time
from multiprocessing import Pool
import numpy as np

from . import runner
from .env import Environment, _rng
from .v5_exp import STRATS as V5_STRATS, setting

DATA = os.path.join("data", "processed", "freshqa_staleness.json")
TODAY = "21 April 2026"
STREAMS = {"fqr_news": lambda r: r["fact"] == "fast-changing", "fqr_mixed": lambda r: True}
BASE_FAIL = (0.05, 0.05, 0.03)
SEEDS = {"dev": tuple(range(2500, 2510)), "confirm": tuple(range(2510, 2530))}

JUDGE_PROMPT = ("Today is {today}.\nQuestion: {q}\nProposed answer: {a}\n"
                "Is the proposed answer correct and up to date as of today? Reply with one word: YES or NO.\nReply:")
# Prompt variants. "dated" (first run, 31 Oct): the judge was told today's date; both Qwen models then said NO to
# almost every answer, including never-changing facts, and gave the same verdict to the old and the new answer
# (573/574 and 574/574 questions), so the verdict did not depend on the answer. "plain" asks only whether the answer is
# correct, from the model's own knowledge. A variant is chosen by suffixing the model name, e.g. qwen2.5:3b@plain.
PLAIN_PROMPT = ("Question: {q}\nProposed answer: {a}\n"
                "Is the proposed answer correct? Reply with one word: YES or NO.\nReply:")


def split_model(model):
    name, _, variant = model.partition("@")
    return name, (variant or "dated")


SAME_PROMPT = ("Question: {q}\nAnswer 1: {a}\nAnswer 2: {b}\n"
               "Do the two answers give the same answer to the question? Reply with one word: YES or NO.\nReply:")

norm = lambda t: re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()


def _safe(s):
    return re.sub(r"[^A-Za-z0-9_.-]", "_", s)


def verdict_path(model):
    return os.path.join("data", "processed", f"freshqa_judge_{_safe(model)}.json")


def _yes(text):
    t = text.strip().lower()
    return t.startswith("yes") or (re.search(r"\byes\b", t) is not None and re.search(r"\bno\b", t) is None)


class StubLLM:
    """For tests without Ollama: a deterministic, imperfect judge (hash of the prompt)."""
    model = "stub"

    def __call__(self, prompt, **kw):
        h = int(hashlib.sha256(prompt.encode()).hexdigest()[:8], 16) / 16 ** 8
        if "Proposed answer" in prompt:
            stale = "STALE" in prompt
            return "NO" if h < (0.6 if stale else 0.15) else "YES"
        return "YES" if h < 0.8 else "NO"

    def save(self):
        pass


# ----------------------------------------------------------------------------- collect verdicts (laptop)
def collect(model, limit=None):
    rows = json.load(open(DATA))["rows"]
    path = verdict_path(model)
    out = json.load(open(path)) if os.path.exists(path) else {"model": model, "today": TODAY, "items": {}}
    if split_model(model)[0] == "stub":
        llm = StubLLM()
    else:
        from .realagent import LLM
        llm = LLM(split_model(model)[0])
        out["model_details"] = llm.digest
    t0, n_new = time.time(), 0
    for i, r in enumerate(rows[:limit] if limit else rows):
        key = norm(r["q"])
        if key in out["items"]:
            continue
        old, new = r["old0"], r["new0"]
        tag = " STALE" if (split_model(model)[0] == "stub" and r["stale_wrong"]) else ""     # only the stub sees this
        jp = PLAIN_PROMPT if split_model(model)[1] == "plain" else JUDGE_PROMPT
        raw_old = llm(jp.format(today=TODAY, q=r["q"], a=old) + tag, max_tokens=4)
        raw_new = llm(jp.format(today=TODAY, q=r["q"], a=new), max_tokens=4)
        if norm(old) == norm(new):
            same, raw_same = True, "(identical after normalising)"
        else:
            raw_same = llm(SAME_PROMPT.format(q=r["q"], a=old, b=new), max_tokens=4)
            same = _yes(raw_same)
        out["items"][key] = dict(flag_old=not _yes(raw_old), flag_new=not _yes(raw_new), same=same,
                                 raw_old=raw_old, raw_new=raw_new, raw_same=raw_same)
        n_new += 1
        if n_new % 25 == 0:
            json.dump(out, open(path, "w"), indent=0)
            if hasattr(llm, "save"):
                llm.save()
            done = len(out["items"])
            print(f"  {done}/{len(rows)} questions judged; {time.time() - t0:.0f} s", flush=True)
    json.dump(out, open(path, "w"), indent=0)
    if hasattr(llm, "save"):
        llm.save()
    print(f"Saved {len(out['items'])} judged questions to {path} ({time.time() - t0:.0f} s)")
    measure(model)


def measure(model, quiet=False):
    rows = json.load(open(DATA))["rows"]
    items = json.load(open(verdict_path(model)))["items"]
    res = {}
    for name, fn in (("news", STREAMS["fqr_news"]), ("mixed", STREAMS["fqr_mixed"])):
        rr = [(r, items[norm(r["q"])]) for r in rows if fn(r) and norm(r["q"]) in items]
        wrong = [v["flag_old"] for r, v in rr if r["stale_wrong"]]                         # stale answers
        right = [v["flag_new"] for r, v in rr] + [v["flag_old"] for r, v in rr if not r["stale_wrong"]]
        same_ok = [v["same"] for r, v in rr if not r["stale_wrong"] and norm(r["old0"]) != norm(r["new0"])]
        same_bad = [v["same"] for r, v in rr if r["stale_wrong"]]
        res[name] = dict(n=len(rr), q=float(np.mean(wrong)) if wrong else float("nan"),
                         f=float(np.mean(right)) if right else float("nan"),
                         n_stale=len(wrong), false_agree=float(np.mean(same_bad)) if same_bad else float("nan"),
                         missed_agree=float(1 - np.mean(same_ok)) if same_ok else float("nan"), n_reworded=len(same_ok))
    if not quiet:
        print(f"Judge {model} on FreshQA (today = {TODAY}):")
        for k, v in res.items():
            print(f"  {k:6s} n={v['n']:3d}  catch rate q = {v['q']:.3f} (on {v['n_stale']} stale answers)  "
                  f"false-alarm rate f = {v['f']:.3f}  | comparison: says 'same' for a stale vs a fresh answer "
                  f"{v['false_agree']:.3f}; says 'different' for two correct answers in other words "
                  f"{v['missed_agree']:.3f} (n={v['n_reworded']})")
    return res


# ----------------------------------------------------------------------------- environment with real verdicts
_ROWS, _ITEMS = None, {}


class FreshQARealEnvironment(Environment):
    def __init__(self, s, scenario, seed):
        global _ROWS
        if not scenario.startswith("fqr_"):
            return super().__init__(s, scenario, seed)
        stream, model = scenario.split("|")
        p_stale = 1.0
        if "@p" in stream:                                       # e.g. fqr_mixed@p50: tool A goes stale in 50% of runs
            stream, pp = stream.split("@p"); p_stale = int(pp) / 100.0
        super().__init__(s, "drop_0.95", seed)
        if _ROWS is None:
            _ROWS = json.load(open(DATA))["rows"]
        if model not in _ITEMS:
            _ITEMS[model] = json.load(open(verdict_path(model)))["items"]
        items = _ITEMS[model]
        self.pool = [(r, items[norm(r["q"])]) for r in _ROWS if STREAMS[stream](r) and norm(r["q"]) in items]
        r = _rng("freshqa_real", stream, seed)
        T = self.p.shape[1]
        self.qs = r.integers(0, len(self.pool), T)
        self.t0 = int(r.integers(150, 350))
        if p_stale < 1.0 and _rng("freshqa_real_pstale", stream, seed).random() >= p_stale:
            self.t0 = 10 ** 9                                    # this run: tool A never stops updating
        self.real_compare = True                                    # the runner then calls agree()
        stale = np.array([self.pool[i][0]["stale_wrong"] for i in self.qs], dtype=bool)
        self.p[:, :] = (1 - np.array(BASE_FAIL))[:, None]
        self.p[0, (np.arange(T) >= self.t0) & stale] = 0.0         # for the runner's reference metrics only

    def _ans(self, k, t):
        return "old" if (k == 0 and t >= self.t0) else "new"

    def call(self, k, t, attempt, checked):
        if not getattr(self, "real_compare", False):               # any other scenario: the normal simulator
            return super().call(k, t, attempt, checked)
        if self.u_success[k, t, attempt] < BASE_FAIL[k]:
            return "loud"                                          # a timeout or error message
        row, v = self.pool[self.qs[t]]
        a = self._ans(k, t)
        correct = a == "new" or not row["stale_wrong"]
        flag = checked and v["flag_" + a]
        if correct:
            return "false_alarm" if flag else "ok"
        return "caught" if flag else "leak"

    def agree(self, cur, j, t, truly_correct, alt):
        a, b = self._ans(cur, t), self._ans(j, t)
        return True if a == b else bool(self.pool[self.qs[t]][1]["same"])


runner.Environment = FreshQARealEnvironment


KEYS = ("never", "always", "cusum", "v4", "v4_nocal", "always_x", "v5")


from .strategies import NeverCheck, REGISTRY as _REG


class UseFreshTool(NeverCheck):
    """Reference (1 Nov 2026): pay for the fresher tool B from the first call and never check. It answers the
    question 'is a monitoring rule worth having at all here, or should one simply buy the dearer tool?'."""
    name = "R_use_B"

    def start_task(self, ctx):
        self.current = 1
        return 1

    def decide(self, ctx, allow_switch=True):
        ctx["trace"] = {}
        return "call"


_REG[UseFreshTool.name] = UseFreshTool


def _strats(model):
    """Strategies; 'true' calibration = the judge's measured q and f on the stream (labelled calibration)."""
    S = {k: V5_STRATS[k] for k in KEYS}
    tuned = os.path.join("data", "processed", "core2_tuned.json")
    if os.path.exists(tuned):
        from .core2_exp import GRIDS
        from . import outside_baselines  # noqa: F401
        t = json.load(open(tuned))
        for b in ("ssv", "rdecusum", "glrklucb"):
            S[b] = (GRIDS[b][0], t[b], "true")
    S["use_B"] = ("R_use_B", dict(window=30), "true")
    return S


def _job(a):
    key, name, params, told, stream, model, cal, seed = a
    q, f = cal
    s = setting(min(max(q, 0.05), 0.99), 3.0, min(max(f, 0.0), 0.95), 1.0, told)
    r = runner.run(name, dict(params), s, f"{stream}|{model}", seed)
    return dict(strategy=key, stream=stream, seed=seed, loss=r["total_loss_fail"], leak_rate=r["leak_rate"],
                fail_rate=r["fail_rate"], checks=r["checks_per_task"], crosschecks=r["crosschecks_per_task"],
                switches=r["switches"], f_hat=r.get("f_hat"), q_hat=r.get("q_hat_cm"))


def run_exp(model, which, procs):
    cal = measure(model)
    S = _strats(model)
    seeds = SEEDS[which]
    jobs = [(k, *S[k], st, model, (cal[st[4:]]["q"], cal[st[4:]]["f"]), sd) for k in S for st in STREAMS for sd in seeds]
    t0 = time.time()
    with Pool(procs) as pool:
        rows = pool.map(_job, jobs, chunksize=4)
    g = lambda k, st, fld="loss": float(np.mean([x[fld] for x in rows if x["strategy"] == k and x["stream"] == st]))
    L = [f"# FreshQA with a real judge ({model}), {which} seeds {seeds[0]}-{seeds[-1]}", "",
         f"Judge rates (measured with labels): " + "; ".join(f"{k}: q {v['q']:.2f}, f {v['f']:.2f}, false 'same' "
                                                          f"{v['false_agree']:.2f}" for k, v in cal.items()),
         f"{len(rows)} runs; {time.time() - t0:.0f} s. Wrong answer = 3 tasks. Verdicts repeat on retries (temperature 0).", "",
         "| Strategy | told | news loss | news vs never | mixed loss | mixed vs never | wrong kept (news) | failed (news) | checks (news) | cross-checks (news) |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for k in S:
        L.append(f"| {k} | {S[k][2]} | {g(k, 'fqr_news'):.1f} | {100 * (g(k, 'fqr_news') / g('never', 'fqr_news') - 1):+.1f}% | "
                 f"{g(k, 'fqr_mixed'):.1f} | {100 * (g(k, 'fqr_mixed') / g('never', 'fqr_mixed') - 1):+.1f}% | "
                 f"{g(k, 'fqr_news', 'leak_rate'):.1%} | {g(k, 'fqr_news', 'fail_rate'):.1%} | "
                 f"{g(k, 'fqr_news', 'checks'):.2f} | {g(k, 'fqr_news', 'crosschecks'):.2f} |")
    out = os.path.join("results", f"freshqa_real_{_safe(model)}_{which}_{time.strftime('%Y%m%d-%H%M%S')}")
    os.makedirs(out, exist_ok=True)
    json.dump(dict(rows=rows, calibration=cal), open(os.path.join(out, "rows.json"), "w"))
    open(os.path.join(out, "report.md"), "w").write("\n".join(L))
    print("\n".join(L)); print("Saved to", out)
    return rows, cal


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("collect", "measure", "run"))
    ap.add_argument("--model", default="qwen2.5:1.5b")
    ap.add_argument("--seeds", default="dev", choices=tuple(SEEDS))
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--procs", type=int, default=os.cpu_count() or 2)
    a = ap.parse_args()
    if a.cmd == "collect":
        collect(a.model, a.limit)
    elif a.cmd == "measure":
        measure(a.model)
    else:
        run_exp(a.model, a.seeds, a.procs)
