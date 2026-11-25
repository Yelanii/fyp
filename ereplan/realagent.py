"""Real-agent validation: a real LLM plans the tool calls and a real LLM judges tool results.

Setting (all runs on a laptop CPU, no paid API):
  * Tasks: GSM8K test word problems (data/raw/gsm8k_test.jsonl, MIT licence).
  * Agent: a local LLM served by Ollama turns each problem into calculator steps ("r1 = 16 - 3 - 4").
    Only problems the agent solves correctly with healthy tools are kept, so later errors come from tools.
  * Tools: three interchangeable calculator services A (price 20), B (24), C (30), real Python code.
    Service A degrades at a random point: its failure rate rises and its silent failures become SUBTLE
    (off by one, rounded) instead of OBVIOUS (x10, sign flip, digit swap). Some failures are loud errors.
  * Check: the same local LLM is asked "is `expr = value` correct?". Its real catch rate is measured per
    fault type by `calibrate`; strategies are told the catch rate measured on OBVIOUS faults (what a team
    would measure before deployment). If the judge misses subtle faults, this is real false reassurance.
  * Strategies: never / always check, CUSUM, rule v2, rule v3 (self-calibrating), unchanged from the study.

Commands (Ollama must be running locally, e.g. `ollama pull qwen2.5:1.5b`):
  python -m ereplan.realagent plan      --model qwen2.5:1.5b --n 300
  python -m ereplan.realagent calibrate --model qwen2.5:1.5b
  python -m ereplan.realagent run       --model qwen2.5:1.5b --seeds 10
Use --model stub to test the whole pipeline without an LLM (gold plans from GSM8K's calculator
annotations, and a SIMULATED judge). Stub results are pipeline checks only, never findings.
"""
import argparse, ast, hashlib, json, math, operator, os, re, time, urllib.request, zlib
from collections import Counter
import numpy as np

from .config import Setting, Tool
from .strategies import REGISTRY
from . import selfcal, fa_rule, litbaselines, crosscheck  # noqa: F401 (registers rules v3, v4, v4_pi and v5)
import glob

DATA = "data/raw/gsm8k_test.jsonl"
OUT = "data/processed"
OLLAMA = os.environ.get("OLLAMA_URL", "http://localhost:11434")

# ----------------------------------------------------------------------------- LLM access (cached)
class LLM:
    def __init__(self, model):
        self.model = model
        self.path = os.path.join(OUT, f"llm_cache_{_safe(model)}.json")
        self.cache = json.load(open(self.path)) if os.path.exists(self.path) else {}
        self.digest = None
        self.replay = os.environ.get("EREPLAN_REPLAY") == "1"   # answer only from the saved cache, no Ollama
        self.misses = 0
        if model != "stub" and not self.replay:
            try:
                info = _post("/api/show", {"name": model}, timeout=300)
                self.digest = info.get("details", {}) | {"modified_at": info.get("modified_at")}
            except Exception as e:  # noqa: BLE001
                raise SystemExit(f"Cannot reach Ollama at {OLLAMA} for model {model}: {e}\n"
                                 f"Install Ollama, run `ollama pull {model}`, and keep `ollama serve` running.")

    def __call__(self, prompt, max_tokens=256, stop=None, temperature=0.0, seed=0):
        tag = prompt if (temperature == 0 and seed == 0) else f"{prompt}|T={temperature}|seed={seed}"
        key = hashlib.sha256(tag.encode()).hexdigest()
        if key in self.cache:
            return self.cache[key]
        if self.replay:
            self.misses += 1
            return ""                     # not in the cache: treated as no answer (logged as a miss)
        body = {"model": self.model, "prompt": prompt, "stream": False,
                "options": {"temperature": temperature, "seed": seed, "num_predict": max_tokens} | ({"stop": stop} if stop else {})}
        try:
            text = _post("/api/generate", body, timeout=900)["response"]
        except Exception:
            self.save()                   # keep every answer obtained so far, then stop
            raise
        self.cache[key] = text
        return text

    def save(self):
        os.makedirs(OUT, exist_ok=True)
        json.dump(self.cache, open(self.path, "w"))


def _safe(s):
    return re.sub(r"[^A-Za-z0-9_.-]", "_", s)


def _post(path, body, timeout, tries=5):
    """POST to Ollama, retrying on timeouts and connection errors (a busy laptop can stall for minutes)."""
    for i in range(tries):
        try:
            req = urllib.request.Request(f"{OLLAMA}{path}", data=json.dumps(body).encode(),
                                         headers={"Content-Type": "application/json"})
            return json.loads(urllib.request.urlopen(req, timeout=timeout).read())
        except Exception as e:  # noqa: BLE001
            if i == tries - 1:
                raise
            wait = 30 * (i + 1)
            print(f"  Ollama did not answer ({type(e).__name__}); retrying in {wait} s ({i + 1}/{tries - 1})", flush=True)
            time.sleep(wait)


def _judge_model(a):
    return a.judge_model or a.model


def _cal_path(a):
    tag = _safe(a.model) if _judge_model(a) == a.model else f"{_safe(a.model)}__judge_{_safe(_judge_model(a))}"
    return os.path.join(OUT, f"judge_calibration_{tag}.json")


def _cal_exprs(P, n):
    exprs = []
    for t in P["tasks"][:n]:
        vals = {}
        for name, expr in t["plan"]["steps"]:
            e = expr
            for ref in sorted(vals, key=len, reverse=True):
                e = re.sub(rf"\b{ref}\b", fmt(vals[ref]), e)
            vals[name] = calc(e)
            exprs.append((e, vals[name]))
    return exprs


# ----------------------------------------------------------------------------- arithmetic (the tool)
_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.Pow: operator.pow, ast.USub: operator.neg, ast.UAdd: operator.pos, ast.Mod: operator.mod}


def calc(expr):
    def ev(n):
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return float(n.value)
        if isinstance(n, ast.BinOp) and type(n.op) in _OPS:
            return _OPS[type(n.op)](ev(n.left), ev(n.right))
        if isinstance(n, ast.UnaryOp) and type(n.op) in _OPS:
            return _OPS[type(n.op)](ev(n.operand))
        raise ValueError("unsupported expression")
    return ev(ast.parse(expr, mode="eval").body)


def clean_expr(e):
    e = e.replace("$", "").replace(",", "").replace("×", "*").replace("x", "*").replace("÷", "/")
    return re.sub(r"(?<=\d)%", "/100", e).strip()


def fmt(v):
    return str(int(round(v))) if abs(v - round(v)) < 1e-9 else f"{v:.4g}"


# ----------------------------------------------------------------------------- plans
PLAN_PROMPT = """Solve the math word problem by writing calculator steps.
Write one step per line in exactly this form:  r1 = <arithmetic expression>
Each expression may use numbers from the problem and earlier results (r1, r2, ...).
Use only numbers, + - * / and parentheses. Do not write the result of a step.
The last line must be:  answer = rK
Write nothing else.

Problem: A shop sells pens for 3 dollars each. Tom buys 4 pens and pays with a 20 dollar note. How much change does he get?
r1 = 3 * 4
r2 = 20 - r1
answer = r2

Problem: A farm has 12 cows. It has 3 times as many sheep as cows, and half as many goats as sheep. How many animals are there in total?
r1 = 12 * 3
r2 = r1 / 2
r3 = 12 + r1 + r2
answer = r3

Problem: {q}
"""
# Version 2 of the planner prompt: two invented worked examples were added after the
# zero-shot prompt solved only 13% of problems in a trial run. Only planner output had been seen; no
# judge or strategy result existed yet. The examples are made up and are not GSM8K problems.


def parse_plan(text):
    """Read 'rK = expression' lines. Tolerates the small model's usual extras: markdown, numbering,
    LaTeX brackets, a trailing '= result' and trailing comments."""
    steps, answer = [], None
    for line in text.splitlines():
        if steps and line.strip().lower().startswith("problem"):
            break                                   # the model started inventing a new problem
        line = re.sub(r"`|\*\*|\\[()\[\]]", "", line).strip()
        line = re.sub(r"^(?:[-•]\s*|\d+[.)]\s*|step\s*\d+\s*[:.]\s*)", "", line, flags=re.I)
        line = line.split("#")[0].strip()
        a = re.match(r"answer\s*[:=]\s*(r\d+)\b", line, re.I)
        m = re.match(r"(r\d+)\s*=\s*([^=]+)", line)
        if a:
            answer = a.group(1)
            break
        elif m:
            steps.append((m.group(1), clean_expr(m.group(2))))
    if not steps:
        return None
    return {"steps": steps, "answer": answer or steps[-1][0]}


def gold_plan(answer_text):
    """Turn GSM8K's <<expr=result>> annotations into a referenced plan (used by --model stub)."""
    steps, results = [], {}
    for i, (expr, res) in enumerate(re.findall(r"<<([^=<>]+)=([^<>]+)>>", answer_text)):
        expr = clean_expr(expr)
        for name, val in sorted(results.items(), key=lambda kv: -len(kv[1])):
            expr = re.sub(rf"(?<![\d.]){re.escape(val)}(?![\d.])", name, expr)
        name = f"r{i + 1}"
        steps.append((name, expr))
        results[name] = clean_expr(res)
    return {"steps": steps, "answer": steps[-1][0]} if steps else None


def execute(plan, tool=lambda e: calc(e)):
    vals = {}
    for name, expr in plan["steps"]:
        e = expr
        for ref in sorted(vals, key=len, reverse=True):
            e = re.sub(rf"\b{ref}\b", f"({vals[ref]!r})", e)
        vals[name] = tool(e)
    return vals[plan["answer"]]


def cmd_plan(a):
    llm = LLM(a.model)
    rows = [json.loads(l) for l in open(DATA)]
    kept, tried = [], 0
    t_start = time.time()
    for i, r in enumerate(rows):
        if len(kept) >= a.n:
            break
        gold = float(r["answer"].split("####")[-1].replace(",", "").strip())
        plan = gold_plan(r["answer"]) if a.model == "stub" else parse_plan(llm(PLAN_PROMPT.format(q=r["question"]), stop=["\nProblem:"]))
        tried += 1
        try:
            ok = plan is not None and abs(execute(plan) - gold) < 1e-6 and len(plan["steps"]) <= 8
        except Exception:  # noqa: BLE001
            ok = False
        if ok:
            kept.append({"idx": i, "gold": gold, "plan": plan})
        if tried % 25 == 0:
            print(f"{tried} tried, {len(kept)} solved with healthy tools ({(time.time() - t_start) / 60:.0f} min so far)", flush=True)
            llm.save()
    llm.save()
    os.makedirs(OUT, exist_ok=True)
    out = dict(model=a.model, model_details=llm.digest, prompt=PLAN_PROMPT, tried=tried, kept=len(kept),
               data_sha256=hashlib.sha256(open(DATA, "rb").read()).hexdigest(), tasks=kept)
    json.dump(out, open(os.path.join(OUT, f"gsm8k_plans_{_safe(a.model)}.json"), "w"), indent=1)
    print(f"Planner solved {len(kept)} of {tried} problems with healthy tools ({len(kept)/tried:.0%}).")


# ----------------------------------------------------------------------------- faults and the judge
OBVIOUS = ("times10", "sign_flip", "digit_swap")
SUBTLE = ("off_by_one", "rounded")


def corrupt(v, kind):
    if kind == "times10":
        return v * 10
    if kind == "sign_flip":
        return -v if v != 0 else 7.0
    if kind == "digit_swap":
        s = str(int(abs(round(v))))
        if len(s) >= 2 and s[0] != s[1]:
            return math.copysign(float(s[1] + s[0] + s[2:]), v)
        return v + 9
    if kind == "off_by_one":
        return v + 1
    if kind == "rounded":
        r = round(v, -1)
        return r if r != v else v + 2
    raise ValueError(kind)


JUDGE_PROMPT = """Check this calculation carefully.
{expr} = {value}
Is the result correct? Reply with exactly one word: correct or wrong.
"""

# Second judge (Amendment 2): the model recomputes the expression itself and the check
# flags a mismatch. Run 1 showed the yes/no judge answering "wrong" to 94% of CORRECT results.
RECOMPUTE_PROMPT = """Calculate: {expr}
Reply with only the final number. No words, no units, no working.
"""
JUDGES = ("yesno", "recompute")
GATE = dict(max_false_alarm=0.30, min_catch_obvious=0.50)


def _first_number(text):
    m = re.search(r"-?\d[\d,]*\.?\d*(?:[eE]-?\d+)?", text.replace("$", ""))
    if not m:
        return None
    try:
        return float(m.group(0).replace(",", ""))
    except ValueError:
        return None


class Judge:
    def __init__(self, llm, kind="yesno", temperature=0.0, seed=0):
        self.llm, self.kind, self.temperature, self.seed = llm, kind, temperature, seed

    def says_wrong(self, expr, shown, truth_kind, attempt=0):
        """attempt (part E3): at temperature > 0 each retry of a step asks with its own seed (seed + attempt), so a
        sampled checker judges afresh; at temperature 0 the seed is unchanged (the greedy answer is the same)."""
        seed = self.seed if self.temperature == 0 else self.seed + attempt
        if self.llm.model == "stub":   # SIMULATED judge for pipeline tests only
            h = zlib.crc32(f"{self.kind}|{expr}|{shown}".encode()) / 2**32
            rate = {"ok": 0.02, "obvious": 0.9, "subtle": 0.25}[truth_kind]
            return h < rate
        if self.kind == "recompute":
            # one call per expression (the shown value is not in the prompt), so it is cached and cheap
            got = _first_number(self.llm(RECOMPUTE_PROMPT.format(expr=expr), max_tokens=24,
                                         temperature=self.temperature, seed=seed))
            if got is None:
                return False            # no usable answer: the check raises no alarm
            return abs(got - shown) > 1e-6 * max(1.0, abs(shown)) + 0.005
        text = self.llm(JUDGE_PROMPT.format(expr=expr, value=fmt(shown)), max_tokens=8,
                        temperature=self.temperature, seed=seed).strip().lower()
        return text.startswith("wrong") or ("wrong" in text and "correct" not in text)


def judge_valid(c):
    return c["false_alarm_rate"] <= GATE["max_false_alarm"] and c["catch_rate_obvious"] >= GATE["min_catch_obvious"]


def fault_class(kind):
    return "ok" if kind is None else ("obvious" if kind in OBVIOUS else "subtle")


def cmd_calibrate(a):
    llm = LLM(_judge_model(a))
    P = json.load(open(os.path.join(OUT, f"gsm8k_plans_{_safe(a.model)}.json")))
    rng = np.random.default_rng(1)
    exprs = []
    for t in P["tasks"][: a.cal_n]:
        vals = {}
        for name, expr in t["plan"]["steps"]:
            e = expr
            for ref in sorted(vals, key=len, reverse=True):
                e = re.sub(rf"\b{ref}\b", fmt(vals[ref]), e)
            vals[name] = calc(e)
            exprs.append((e, vals[name]))
    per_judge = {}
    for jk in JUDGES:
        judge = Judge(llm, jk)
        counts = Counter()
        for e, v in exprs:
            for kind in (None,) + OBVIOUS + SUBTLE:
                shown = v if kind is None else corrupt(v, kind)
                if kind is not None and abs(shown - v) < 1e-9:
                    continue
                cls = fault_class(kind)
                counts[(cls, judge.says_wrong(e, shown, cls))] += 1
        llm.save()
        rate = lambda c: counts[(c, True)] / max(1, counts[(c, True)] + counts[(c, False)])
        per_judge[jk] = dict(catch_rate_obvious=rate("obvious"), catch_rate_subtle=rate("subtle"),
                             false_alarm_rate=rate("ok"))
        per_judge[jk]["valid"] = judge_valid(per_judge[jk])
    # pre-registered choice (Amendment 2): among valid judges, the lowest false-alarm rate
    valid = [jk for jk in JUDGES if per_judge[jk]["valid"]]
    chosen = (a.judge if a.judge != "auto" else
              (min(valid, key=lambda jk: per_judge[jk]["false_alarm_rate"]) if valid else None))
    res = dict(model=a.model, n_expressions=len(exprs), judges=per_judge, gate=GATE, judge=chosen,
               note="stub = simulated judge" if a.model == "stub" else "real LLM judge")
    if chosen:
        res.update({k: per_judge[chosen][k] for k in ("catch_rate_obvious", "catch_rate_subtle", "false_alarm_rate")})
    res["judge_model"] = _judge_model(a)
    json.dump(res, open(_cal_path(a), "w"), indent=1)
    print(json.dumps(res, indent=1))
    if not chosen:
        print("NO JUDGE PASSED THE VALIDITY GATE. Do not run; send this output for advice.")


# ----------------------------------------------------------------------------- closed-loop run
TOOLS = (Tool("calc_A", 20.0, 1.0, 0.95, 0.95), Tool("calc_B", 24.0, 1.0, 0.95, 0.95), Tool("calc_C", 30.0, 1.0, 0.97, 0.95))
STRATS = {"never": ("B2_never", dict(window=30)), "always": ("B1_always", dict(window=30)),
          "cusum": ("B4_cusum", dict(h=6, p1=0.8)),
          "v2": ("Rule_leakaware", dict(window=60, epsilon=0.02, k=3, horizon_mode="session", session_cap=50)),
          "v3": ("Rule_v3_selfcal", dict(window=60, epsilon=0.02, k=3, horizon_mode="session", session_cap=50, q_prior_strength=3.0)),
    "v4": ("Rule_v4_fa", dict(window=60, epsilon=0.02, k=3, horizon_mode="session", session_cap=50, q_prior_strength=3.0))}


def run_one(tasks, judge, strat_key, seed, drop, q_assumed, check_frac, leak_mult, n_tasks=120, rho=0.5, f_assumed=0.0,
            strats=None, rng_alias=None):
    r = np.random.default_rng(zlib.crc32(f"real|{seed}".encode()))
    order = r.integers(0, len(tasks), n_tasks)
    steps_total = sum(len(tasks[i]["plan"]["steps"]) for i in order)
    t0 = int(r.integers(steps_total // 4, steps_total // 2))
    U = r.random((len(TOOLS), steps_total, 3, 4))           # success, loud, fault-type pick, spare
    mean_steps = steps_total / n_tasks
    s = Setting(tools=TOOLS, steps_per_task=int(round(mean_steps)), n_tasks=n_tasks, rho=rho,
                q_true=q_assumed, q_assumed=q_assumed, check_frac=check_frac, leak_mult=leak_mult,
                fa_assumed=f_assumed)   # only rule v4 uses f (told the calibrated false-alarm rate)
    name, params = (strats or STRATS)[strat_key]
    params = dict(params)
    hm, cap = params.pop("horizon_mode", "task"), params.pop("session_cap", 50)
    rkey = (rng_alias or {}).get(strat_key, strat_key)     # part E3: v4_ind shares v4's audit draws (paired)
    st = REGISTRY[name](s, np.random.default_rng(zlib.crc32(f"strat|{rkey}|{seed}".encode())), **params)
    st.horizon_mode, st.session_cap = hm, cap

    def p_of(k, t):
        return drop if (k == 0 and t >= t0) else TOOLS[k].base_p

    spend = leaks = unrec = checks = 0.0
    fa_events = reflag_pairs = reflag_hits = 0                # part E3: false alarms seen inside the loop
    xchecks = fa_resolved = 0                                  # rule v5: cross-checks of flagged steps
    xcheck = bool(getattr(st, "crosscheck", False))
    t = 0
    for i in order:
        task = tasks[i]
        steps = task["plan"]["steps"]
        ctx = {"t": t, "u": len(steps), "cur": None, "left_in_run": steps_total - t}
        cur = st.start_task(ctx)
        vals, failed = {}, False
        for j, (nm, expr) in enumerate(steps):
            e = expr
            for ref in sorted(vals, key=len, reverse=True):
                e = re.sub(rf"\b{ref}\b", fmt(vals[ref]), e)
            ctx = {"t": t, "u": len(steps) - j, "cur": cur, "left_in_run": steps_total - t}
            act = st.decide(ctx, allow_switch=True)
            if act == "switch":
                spend += s.switch_cost
                cur = st.switch_to(ctx)
                ctx = {"t": t, "u": len(steps) - j, "cur": cur, "left_in_run": steps_total - t}
                act = st.decide(ctx, allow_switch=False)
            chk = act == "call_and_check"
            truth = calc(e)
            done = False
            prev_fa = False
            for att in range(3):
                spend += TOOLS[cur].price + (s.check_price if chk else 0.0)
                checks += chk
                u = U[cur, min(t, steps_total - 1), att]
                if u[0] < p_of(cur, t):
                    shown, kind = truth, None
                elif u[1] < rho:
                    st.observe(cur, chk, True, kind="loud")
                    continue
                else:
                    pool = SUBTLE if (cur == 0 and t >= t0) else OBVIOUS
                    kind = pool[int(u[2] * len(pool))]
                    shown = corrupt(truth, kind)
                flagged = chk and judge.says_wrong(e, shown, fault_class(kind), attempt=att)
                if chk and kind is None:                       # a correct value was checked
                    if prev_fa:
                        reflag_pairs += 1
                        reflag_hits += int(flagged)
                    prev_fa = flagged
                    fa_events += int(flagged)
                if flagged and xcheck:
                    # rule v5 / B12: run the step on the alternative tool (its own simulated faults) and compare values.
                    # Two tools with the same fault type can produce the same wrong value: then they agree wrongly.
                    jx = st.crosscheck_tool(ctx)
                    a_hat = st.alt_mean(jx)
                    spend += TOOLS[jx].price
                    xchecks += 1
                    ua = U[jx, min(t, steps_total - 1), att]
                    if ua[0] < p_of(jx, t):
                        alt = truth
                    elif ua[1] < rho:
                        alt = None
                    else:
                        pool_a = SUBTLE if (jx == 0 and t >= t0) else OBVIOUS
                        alt = corrupt(truth, pool_a[int(ua[2] * len(pool_a))])
                    st.observe(jx, False, alt is None, kind="loud" if alt is None else "none")
                    if alt is None:
                        st.observe(cur, chk, True, kind="flag_altloud", a=a_hat)
                        continue
                    if abs(alt - shown) <= 1e-6 * max(1.0, abs(shown)):
                        st.observe(cur, chk, False, kind="flag_agree", a=a_hat)
                        fa_resolved += int(kind is None)
                        vals[nm] = shown
                    else:
                        st.observe(cur, chk, True, kind="flag_disagree", a=a_hat)
                        vals[nm] = alt
                    done = True
                    break
                if flagged:
                    st.observe(cur, chk, True, kind="caught")
                    continue
                st.observe(cur, chk, False, kind="none")
                vals[nm] = shown
                done = True
                break
            t += 1
            if not done:
                failed = True
                t += len(steps) - j - 1
                break
        if failed:
            unrec += 1
        elif abs(vals[task["plan"]["answer"]] - task["gold"]) > 1e-6:
            leaks += 1
    L = leak_mult * mean_steps * np.mean([x.price for x in TOOLS])
    task_cost = mean_steps * np.mean([x.price for x in TOOLS])
    return dict(strategy=strat_key, seed=seed, drop=drop, check_frac=check_frac, leak_mult=leak_mult,
                # Amendment 2: a task that ends in a KNOWN failure costs one task (it must be redone)
                total_loss=(spend + L * leaks + task_cost * unrec) / n_tasks,
                total_loss_prereg=(spend + L * leaks) / n_tasks,
                leak_rate=leaks / n_tasks, fail_rate=unrec / n_tasks, checks_per_task=checks / n_tasks,
                fa_events=fa_events, reflag_pairs=reflag_pairs, reflag_hits=reflag_hits,
                xchecks_per_task=xchecks / n_tasks, fa_resolved=fa_resolved,
                f_hat=(st.cm.f_mean if hasattr(st, "cm") else None), q_hat=(st.cm.q_mean if hasattr(st, "cm") else None))


def cmd_run(a):
    llm = LLM(_judge_model(a))
    P = json.load(open(os.path.join(OUT, f"gsm8k_plans_{_safe(a.model)}.json")))
    cal = json.load(open(_cal_path(a)))
    if not cal.get("judge"):
        raise SystemExit("No judge passed the validity gate in calibration. Not running.")
    judge = Judge(llm, cal["judge"])
    q_assumed = max(0.05, min(0.99, cal["catch_rate_obvious"]))
    tasks = P["tasks"]
    rows = []
    t_start = time.time()
    seeds = range(a.seed_start, a.seed_start + a.seeds)
    f_assumed = cal["false_alarm_rate"]
    for drop in (0.85, 0.75):
        for lm in (1.0, 3.0):
            for sd in seeds:
                for key in STRATS:
                    rows.append(run_one(tasks, judge, key, sd, drop, q_assumed, 0.15, lm, f_assumed=f_assumed))
                llm.save()
            print(f"drop {drop} leak {lm}: done ({time.time() - t_start:.0f}s)", flush=True)
    llm.save()
    jtag = "" if _judge_model(a) == a.model else f"_judge_{_safe(_judge_model(a))}"
    out = os.path.join("results", f"realagent_{_safe(a.model)}{jtag}_{time.strftime('%Y%m%d-%H%M%S')}")
    os.makedirs(out, exist_ok=True)
    json.dump(dict(model=a.model, model_details=llm.digest, calibration=cal, q_assumed=q_assumed, rows=rows),
              open(os.path.join(out, "rows.json"), "w"), indent=1)
    lines = [f"# Real-agent validation ({a.model}{' - STUB, pipeline test only' if a.model == 'stub' else ''})", "",
             f"Tasks kept: {len(tasks)}; judge catch rate obvious {cal['catch_rate_obvious']:.2f}, "
             f"subtle {cal['catch_rate_subtle']:.2f}, false alarms {cal['false_alarm_rate']:.2f}; "
             f"strategies told q = {q_assumed:.2f}. Judge used: {cal['judge']}.", "",
             "Total loss per task (Amendment 2: spend + leak loss x leaks + one task cost x failed tasks):", "",
             "| Drop | Leak loss | " + " | ".join(STRATS) + " |", "|---|---|" + "---|" * len(STRATS)]
    for drop in (0.85, 0.75):
        for lm in (1.0, 3.0):
            m = [np.mean([r["total_loss"] for r in rows if r["strategy"] == k and r["drop"] == drop and r["leak_mult"] == lm]) for k in STRATS]
            lines.append(f"| {int(drop*100)}% | {lm:g} | " + " | ".join(f"{x:.1f}" for x in m) + " |")
    lines += ["", "Same runs, pre-registered metric (failed tasks cost nothing extra):", "",
              "| Drop | Leak loss | " + " | ".join(STRATS) + " |", "|---|---|" + "---|" * len(STRATS)]
    for drop in (0.85, 0.75):
        for lm in (1.0, 3.0):
            m = [np.mean([r["total_loss_prereg"] for r in rows if r["strategy"] == k and r["drop"] == drop and r["leak_mult"] == lm]) for k in STRATS]
            lines.append(f"| {int(drop*100)}% | {lm:g} | " + " | ".join(f"{x:.1f}" for x in m) + " |")
    lines += ["", "Share of tasks: leaked (silent wrong answer) / failed (known failure), pooled:", ""]
    for k in STRATS:
        lines.append(f"- {k}: leaked {np.mean([r['leak_rate'] for r in rows if r['strategy'] == k]):.1%}, "
                     f"failed {np.mean([r['fail_rate'] for r in rows if r['strategy'] == k]):.1%}")
    # pre-registered checks (PREREGISTRATION_realagent.md)
    from scipy.stats import wilcoxon
    key = lambda r: (r["drop"], r["leak_mult"], r["seed"])
    get = lambda k: {key(r): r["total_loss"] for r in rows if r["strategy"] == k}
    v3, v2, al, nv = get("v3"), get("v2"), get("always"), get("never")
    ks = sorted(v3)
    try:
        p2 = float(wilcoxon([v3[k] for k in ks], [v2[k] for k in ks], alternative="less").pvalue)
    except ValueError:
        p2 = 1.0
    m = lambda d: float(np.mean(list(d.values())))
    conds = sorted({k[:2] for k in ks})
    r4 = sum(np.mean([al[k] for k in ks if k[:2] == c]) > np.mean([nv[k] for k in ks if k[:2] == c]) for c in conds)
    lines += ["", "## Pre-registered checks",
              f"- R1 judge catches subtle less than obvious: {cal['catch_rate_subtle']:.2f} vs {cal['catch_rate_obvious']:.2f} -> "
              f"{'met' if cal['catch_rate_subtle'] < cal['catch_rate_obvious'] else 'not met'}",
              f"- R2 v3 < v2: mean {m(v3):.1f} vs {m(v2):.1f}, p = {p2:.3g} -> {'met' if p2 < 0.05 else 'not met'}",
              f"- R3 v3 below always and never: {m(v3):.1f} vs {m(al):.1f} and {m(nv):.1f} -> "
              f"{'met' if m(v3) < min(m(al), m(nv)) else 'not met'}",
              f"- R4 always worse than never in >= 2 of 4 conditions: {r4} of {len(conds)} -> {'met' if r4 >= 2 else 'not met'}"]
    v4 = get("v4")
    lines += ["", "## Pre-registered checks for rule v4 (PREREGISTRATION_falsealarm.md, part C)"]
    r5 = []
    for k in ("never", "always", "cusum", "v2", "v3"):
        o = get(k)
        try:
            pk = float(wilcoxon([v4[x] for x in ks], [o[x] for x in ks], alternative="less").pvalue)
        except ValueError:
            pk = 1.0
        r5.append((k, m(o), pk))
    ok5 = all(m(v4) < mo and pk < 0.05 for _, mo, pk in r5)
    lines.append(f"- R5 v4 ({m(v4):.1f}) below every other strategy: " + "; ".join(f"{k} {mo:.1f} p = {pk:.2g}" for k, mo, pk in r5)
                 + f" -> {'met' if ok5 else 'not met'}")
    r6 = sum(np.mean([v4[x] for x in ks if x[:2] == c]) < np.mean([nv[x] for x in ks if x[:2] == c]) for c in conds)
    lines.append(f"- R6 v4 below never-check in >= 3 of 4 conditions: {r6} of {len(conds)} -> {'met' if r6 >= 3 else 'not met'}")
    lines.append(f"- Seeds {seeds.start}-{seeds.stop - 1}" + (" (Run 3 must use 3000-3009)" if seeds.start != 3000 else ""))
    if a.model == "stub":
        lines.append("- STUB RUN: these checks only test the pipeline and are not findings.")
    open(os.path.join(out, "report.md"), "w").write("\n".join(lines))
    print("\n".join(lines))
    if llm.replay:
        print(f"Replay mode: {llm.misses} LLM calls were not in the cache (treated as no answer).")
    print(f"Saved to {out}")


def cmd_repeat(a):
    """Persistence of checker false alarms (PREREGISTRATION_falsealarm.md, part D): ask the recompute judge
    K times about every CORRECT calibration step, at each temperature, and measure how often a flag repeats."""
    llm = LLM(_judge_model(a))
    P = json.load(open(os.path.join(OUT, f"gsm8k_plans_{_safe(a.model)}.json")))
    exprs = _cal_exprs(P, a.cal_n)
    temps = [float(x) for x in a.temps.split(",")]
    res = dict(planner=a.model, judge_model=_judge_model(a), k=a.k, n_expressions=len(exprs), by_temperature={})
    for T in temps:
        flags = []
        for e, v in exprs:
            row = []
            for j in range(a.k):
                # seeds 1..K, so every call is a fresh model call (seed 0 at T = 0 is the cached Run-2 answer)
                row.append(bool(Judge(llm, "recompute", temperature=T, seed=j + 1).says_wrong(e, v, "ok")))
            flags.append(row)
            if len(flags) % 25 == 0:
                llm.save(); print(f"T={T}: {len(flags)}/{len(exprs)} steps", flush=True)
        llm.save()
        F = np.array(flags, dtype=bool)
        prev, nxt = F[:, :-1].ravel(), F[:, 1:].ravel()
        res["by_temperature"][str(T)] = dict(
            false_alarm_rate=float(F.mean()),
            reflag_given_flag=float(nxt[prev].mean()) if prev.any() else None,
            flag_given_no_flag=float(nxt[~prev].mean()) if (~prev).any() else None,
            share_flagged_every_time=float(F.all(axis=1).mean()),
            share_flagged_at_least_once=float(F.any(axis=1).mean()),
            pairs_after_flag=int(prev.sum()), reflags=int(nxt[prev].sum()),
            pairs_after_no_flag=int((~prev).sum()), flags_after_no_flag=int(nxt[~prev].sum()))
    out = os.path.join("results", f"repeat_{_safe(_judge_model(a))}_{time.strftime('%Y%m%d-%H%M%S')}.json")
    os.makedirs("results", exist_ok=True)
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps(res, indent=1)); print("Saved to", out)


# ----------------------------------------------------------------------------- part E3: persistence with real checkers
E3_STRATS = {"never": STRATS["never"], "always": STRATS["always"], "v4": STRATS["v4"],
             "v4_ind": ("Rule_v4_pi", dict(STRATS["v4"][1], pi_assumed=0.0))}
E3_RNG = {"v4_ind": "v4"}          # same audit draws as v4, so v4 vs v4_ind is fully paired


def _newest(pattern):
    xs = sorted(glob.glob(pattern))
    return xs[-1] if xs else None


def cmd_persist(a):
    """PREREGISTRATION_persistence.md, part E3: rule v4 (assumes false alarms persist) vs v4_ind (assumes they are
    independent) with the REAL recompute checkers, at temperature 0 and 0.7. Plans come from --model."""
    from types import SimpleNamespace
    from scipy.stats import wilcoxon
    P = json.load(open(os.path.join(OUT, f"gsm8k_plans_{_safe(a.model)}.json")))
    tasks = P["tasks"]
    seeds = range(a.seed_start, a.seed_start + a.seeds)
    temps = [float(x) for x in a.temps.split(",")]
    judges = [x.strip() for x in a.judge_models.split(",")]
    rows, setup, t_start = [], {}, time.time()
    for jm in judges:
        a2 = SimpleNamespace(model=a.model, judge_model=jm)
        cal = json.load(open(_cal_path(a2)))
        if cal.get("judge") != "recompute":
            raise SystemExit(f"{jm}: the calibrated judge is {cal.get('judge')!r}, not 'recompute'. Not running.")
        llm = LLM(jm)
        q_assumed = max(0.05, min(0.99, cal["catch_rate_obvious"]))
        for T in temps:
            if T == 0:
                judge, f = Judge(llm, "recompute"), cal["false_alarm_rate"]          # seed 0: the Run 2/3 answers
                f_src = os.path.basename(_cal_path(a2))
            else:
                rp = _newest(os.path.join("results", f"repeat_{_safe(jm)}_*.json"))
                if not rp:
                    raise SystemExit(f"{jm}: no repeat-test file results/repeat_{_safe(jm)}_*.json (part D). Not running.")
                f = json.load(open(rp))["by_temperature"][str(T)]["false_alarm_rate"]
                judge, f_src = Judge(llm, "recompute", temperature=T, seed=1), os.path.basename(rp)
            setup[f"{jm}|T={T:g}"] = dict(f_assumed=f, f_source=f_src, q_assumed=q_assumed)
            for drop in (0.85, 0.75):
                for lm in (1.0, 3.0):
                    for sd in seeds:
                        for key in E3_STRATS:
                            r = run_one(tasks, judge, key, sd, drop, q_assumed, 0.15, lm, f_assumed=f,
                                        strats=E3_STRATS, rng_alias=E3_RNG)
                            r.update(judge_model=jm, T=T)
                            rows.append(r)
                        llm.save()
                    print(f"{jm} T={T:g} drop {drop} leak {lm}: done ({time.time() - t_start:.0f}s)", flush=True)
            llm.save()
            if llm.replay:
                print(f"  replay mode: {llm.misses} LLM calls so far were not in the cache", flush=True)
    out = os.path.join("results", f"realagent_persist_{time.strftime('%Y%m%d-%H%M%S')}")
    os.makedirs(out, exist_ok=True)
    json.dump(dict(planner=a.model, setup=setup, seeds=[seeds.start, seeds.stop - 1], rows=rows),
              open(os.path.join(out, "rows.json"), "w"), indent=1)
    S = list(E3_STRATS)
    L = [f"# Part E3: persistence with real checkers (planner {a.model}; seeds {seeds.start}-{seeds.stop - 1})", "",
         "Total loss per task (spend + leak loss x leaks + one task cost x failed tasks), mean over drop {85, 75}% x leak {1, 3} x seeds:", "",
         "| Checker | T | f told | " + " | ".join(S) + " | always: failed tasks | in-loop re-flag after a false alarm |",
         "|---|---|---|" + "---|" * len(S) + "---|---|"]
    for jm in judges:
        for T in temps:
            rr = [r for r in rows if r["judge_model"] == jm and r["T"] == T]
            m = [np.mean([r["total_loss"] for r in rr if r["strategy"] == k]) for k in S]
            fr = np.mean([r["fail_rate"] for r in rr if r["strategy"] == "always"])
            pairs = sum(r["reflag_pairs"] for r in rr); hits = sum(r["reflag_hits"] for r in rr)
            L.append(f"| {jm} | {T:g} | {setup[f'{jm}|T={T:g}']['f_assumed']:.3f} | " + " | ".join(f"{x:.1f}" for x in m) +
                     f" | {fr:.1%} | {hits / pairs:.3f} ({hits}/{pairs}) |" if pairs else
                     f"| {jm} | {T:g} | {setup[f'{jm}|T={T:g}']['f_assumed']:.3f} | " + " | ".join(f"{x:.1f}" for x in m) + f" | {fr:.1%} | n/a |")
    key = lambda r: (r["judge_model"], r["drop"], r["leak_mult"], r["seed"])
    L += ["", "## Pre-registered checks (PREREGISTRATION_persistence.md, part E3)"]
    for name, T in (("R-E3a", 0.0), ("R-E3b", 0.7)):
        if T not in temps:
            continue
        g = lambda k: {key(r): r["total_loss"] for r in rows if r["strategy"] == k and r["T"] == T}
        v4, vi = g("v4"), g("v4_ind")
        ks = sorted(v4)
        x, y = [v4[k] for k in ks], [vi[k] for k in ks]
        try:
            pv = float(wilcoxon(x, y, alternative="less").pvalue)
        except ValueError:
            pv = 1.0
        ok = np.mean(x) < np.mean(y) and pv < 0.05
        L.append(f"- {name} (T = {T:g}, both checkers pooled, {len(ks)} pairs): v4 {np.mean(x):.1f} vs v4_ind {np.mean(y):.1f} "
                 f"({100 * (np.mean(x) / np.mean(y) - 1):+.1f}%), p = {pv:.2g} -> {'MET' if ok else 'NOT MET'}")
    if a.model == "stub" or any(j == "stub" for j in judges):
        L.append("- STUB RUN: pipeline check only, not findings.")
    open(os.path.join(out, "report.md"), "w").write("\n".join(L))
    print("\n".join(L)); print("Saved to", out)


V5_STRATS = {"never": STRATS["never"], "always_x": ("B12_always_x", dict(window=30)), "v4": STRATS["v4"],
             "v5_told": ("Rule_v5_told", dict(window=60, epsilon=0.02, k=3, horizon_mode="session", session_cap=50)),
             "v5": ("Rule_v5_x", dict(window=60, epsilon=0.02, k=3, horizon_mode="session", session_cap=50))}
V5_RNG = {"v5_told": "v5"}


def cmd_v5(a):
    """PREREGISTRATION_v5.md, real-checker pilot: rule v5 (cross-checks flags, learns q and f without labels) vs rule
    v4 (told the calibrated q and f), with the REAL recompute checkers at temperature 0 and 0.7."""
    from types import SimpleNamespace
    from scipy.stats import wilcoxon
    P = json.load(open(os.path.join(OUT, f"gsm8k_plans_{_safe(a.model)}.json")))
    tasks = P["tasks"]
    seeds = range(a.seed_start, a.seed_start + a.seeds)
    temps = [float(x) for x in a.temps.split(",")]
    judges = [x.strip() for x in a.judge_models.split(",")]
    rows, setup, misses, t_start = [], {}, {}, time.time()
    for jm in judges:
        a2 = SimpleNamespace(model=a.model, judge_model=jm)
        prev = json.load(open(a.setup_from))["setup"] if a.setup_from else None   # q, f as recorded by part E3
        if prev is None:
            cal = json.load(open(_cal_path(a2)))
            if cal.get("judge") != "recompute":
                raise SystemExit(f"{jm}: the calibrated judge is {cal.get('judge')!r}, not 'recompute'. Not running.")
            q_assumed = max(0.05, min(0.99, cal["catch_rate_obvious"]))
        llm = LLM(jm)
        for T in temps:
            m0 = llm.misses
            if prev is not None:
                ps = prev[f"{jm}|T={T:g}"]
                q_assumed, f = ps["q_assumed"], ps["f_assumed"]
                judge = Judge(llm, "recompute") if T == 0 else Judge(llm, "recompute", temperature=T, seed=1)
            elif T == 0:
                judge, f = Judge(llm, "recompute"), cal["false_alarm_rate"]
            else:
                rp = _newest(os.path.join("results", f"repeat_{_safe(jm)}_*.json"))
                if not rp:
                    raise SystemExit(f"{jm}: no repeat-test file results/repeat_{_safe(jm)}_*.json (part D). Not running.")
                f = json.load(open(rp))["by_temperature"][str(T)]["false_alarm_rate"]
                judge = Judge(llm, "recompute", temperature=T, seed=1)
            setup[f"{jm}|T={T:g}"] = dict(f_calibrated=f, q_calibrated=q_assumed)
            for drop in (0.85, 0.75):
                for lm in (1.0, 3.0):
                    for sd in seeds:
                        for key in V5_STRATS:
                            r = run_one(tasks, judge, key, sd, drop, q_assumed, 0.15, lm, f_assumed=f,
                                        strats=V5_STRATS, rng_alias=V5_RNG)
                            r.update(judge_model=jm, T=T)
                            rows.append(r)
                        llm.save()
                    print(f"{jm} T={T:g} drop {drop} leak {lm}: done ({time.time() - t_start:.0f}s)", flush=True)
            llm.save()
            misses[f"{jm}|T={T:g}"] = llm.misses - m0
    out = os.path.join("results", f"realagent_v5_{time.strftime('%Y%m%d-%H%M%S')}")
    os.makedirs(out, exist_ok=True)
    replay = os.environ.get("EREPLAN_REPLAY") == "1"
    json.dump(dict(planner=a.model, setup=setup, seeds=[seeds.start, seeds.stop - 1], replay=replay, cache_misses=misses,
                   rows=rows), open(os.path.join(out, "rows.json"), "w"), indent=1)
    S = list(V5_STRATS)
    L = [f"# Rule v5 with real checkers (planner {a.model}; seeds {seeds.start}-{seeds.stop - 1})", "",
         ("**REPLAY PREVIEW** from saved answers; answers missing from the cache count as no alarm. " if replay else "") +
         f"Cache misses: {misses}", "",
         "Total loss per task, mean over drop {85, 75}% x leak {1, 3} x seeds:", "",
         "| Checker | T | calibrated f | " + " | ".join(S) + " | v5 learned f (median) | v5 failed tasks | v4 failed tasks | v5 leak | v4 leak |",
         "|---|---|---|" + "---|" * len(S) + "---|---|---|---|---|"]
    for jm in judges:
        for T in temps:
            rr = [r for r in rows if r["judge_model"] == jm and r["T"] == T]
            m = [np.mean([r["total_loss"] for r in rr if r["strategy"] == k]) for k in S]
            fh = np.median([r["f_hat"] for r in rr if r["strategy"] == "v5"])
            g = lambda k, fld: np.mean([r[fld] for r in rr if r["strategy"] == k])
            L.append(f"| {jm} | {T:g} | {setup[f'{jm}|T={T:g}']['f_calibrated']:.3f} | " + " | ".join(f"{x:.1f}" for x in m) +
                     f" | {fh:.3f} | {g('v5', 'fail_rate'):.1%} | {g('v4', 'fail_rate'):.1%} | {g('v5', 'leak_rate'):.1%} | {g('v4', 'leak_rate'):.1%} |")
    key = lambda r: (r["judge_model"], r["T"], r["drop"], r["leak_mult"], r["seed"])
    v5 = {key(r): r["total_loss"] for r in rows if r["strategy"] == "v5"}
    v4 = {key(r): r["total_loss"] for r in rows if r["strategy"] == "v4"}
    ks = sorted(v5)
    x, y = np.array([v5[k] for k in ks]), np.array([v4[k] for k in ks])
    p_pairs = float(wilcoxon(x, y, alternative="less").pvalue) if not np.allclose(x, y) else 1.0
    sx = [np.mean([v5[k] for k in ks if k[4] == sd]) for sd in seeds]
    sy = [np.mean([v4[k] for k in ks if k[4] == sd]) for sd in seeds]
    p_seed = float(wilcoxon(sx, sy, alternative="less").pvalue) if not np.allclose(sx, sy) else 1.0
    wins = sum(a_ < b_ for a_, b_ in zip(sx, sy))
    ok1 = p_pairs < 0.05 and p_seed < 0.05
    fe = []
    for r in rows:
        if r["strategy"] == "v5":
            fe.append(abs(r["f_hat"] - setup[f"{r['judge_model']}|T={r['T']:g}"]["f_calibrated"]))
    ok2 = float(np.median(fe)) <= 0.05
    L += ["", "## Pre-registered checks (PREREGISTRATION_v5.md, real-checker pilot)",
          f"- R-V1 v5 below v4: {x.mean():.1f} vs {y.mean():.1f} ({100 * (x.mean() / y.mean() - 1):+.1f}%); {len(ks)} pairs p = {p_pairs:.2g}; "
          f"per seed {wins} of {len(sx)} lower, p = {p_seed:.2g} -> {'MET' if ok1 else 'NOT MET'}",
          f"- R-V2 v5's learned f within 0.05 of the calibrated f: median error {np.median(fe):.3f} -> {'MET' if ok2 else 'NOT MET'}"]
    open(os.path.join(out, "report.md"), "w").write("\n".join(L))
    print("\n".join(L)); print("Saved to", out)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("plan", "calibrate", "run", "repeat", "persist", "v5"))
    ap.add_argument("--model", default="qwen2.5:1.5b")
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--cal-n", dest="cal_n", type=int, default=60, help="tasks used to calibrate the judge")
    ap.add_argument("--judge", default="auto", choices=("auto",) + JUDGES)
    ap.add_argument("--seed-start", dest="seed_start", type=int, default=1000)
    ap.add_argument("--judge-model", dest="judge_model", default=None,
                    help="a different Ollama model for the checker (the plans still come from --model)")
    ap.add_argument("--temps", default="0,0.7", help="repeat: temperatures to test")
    ap.add_argument("--setup-from", dest="setup_from", default=None,
                    help="v5: take the calibrated q and f from a part E3 rows.json instead of the calibration files")
    ap.add_argument("--k", type=int, default=5, help="repeat: questions per step and temperature")
    ap.add_argument("--judge-models", dest="judge_models", default="qwen2.5:1.5b,qwen2.5:3b",
                    help="persist: checker models (comma-separated)")
    a = ap.parse_args(argv)
    {"plan": cmd_plan, "calibrate": cmd_calibrate, "run": cmd_run, "repeat": cmd_repeat, "persist": cmd_persist,
     "v5": cmd_v5}[a.cmd](a)


if __name__ == "__main__":
    main()
