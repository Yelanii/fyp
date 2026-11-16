"""D1 step 1: live tool services backed by real local models (see claude/D1_Design_2026-11-16.md).

What this file is
-----------------
In the earlier real-agent test the "tools" were Python calculators and their wrong answers were injected by us.
Here each tool is a *service backed by a real model*, like a paid API that runs an LLM behind the scenes:

  E1 (maths, GSM8K)      SolverService   - returns a worked solution and a final number.
                                          Service A silently changes its backend model partway through a run
                                          (a provider-side downgrade). Its wrong answers are the model's own.
  E2 (questions, FreshQA) QAService      - answers a question from a knowledge-base entry.
                                          Tool A reads the OLD snapshot (goes stale), tool B the NEW one.

A Checker judges an answer (paid, imperfect), and a Comparator decides whether two answers agree (used by the
cross-check). Nothing here decides *when* to check or switch; that is the rule's job (step 2).

Every model call goes through realagent.LLM, which caches answers by (model, prompt, temperature, seed).
The first run calls Ollama live; any later run with the same inputs replays the identical answer.

Quick test without Ollama:   python -m ereplan.tools_live smoke --stub
Quick test on the laptop:    python -m ereplan.tools_live smoke --n 3
"""
import argparse, json, os, random, re, time

from .realagent import LLM as _BaseLLM, DATA, OUT, _safe


def LLM(model):
    """realagent.LLM, but with its own cache file (d1_cache_<model>.json), so the cache files of the
    earlier experiments are never changed (check_local.py verifies those files byte for byte)."""
    llm = _BaseLLM(model)
    llm.path = os.path.join(OUT, f"d1_cache_{_safe(model)}.json")
    llm.cache = json.load(open(llm.path)) if os.path.exists(llm.path) else {}
    return llm

FRESHQA = "data/processed/freshqa_staleness.json"


# ----------------------------------------------------------------------------- reading answers
_NUM = r"-?\d[\d,]*\.?\d*"


def parse_final_number(text):
    """The number after the LAST 'Answer:' in a solution, or None (None = a loud failure: no usable answer)."""
    hits = re.findall(rf"answer\s*[:=]\s*\$?\s*({_NUM})", text, flags=re.I)
    if not hits:
        return None
    try:
        return float(hits[-1].replace(",", ""))
    except ValueError:
        return None


def gsm8k_truth(answer_field):
    """GSM8K stores the correct final answer after '####'."""
    return float(answer_field.split("####")[-1].strip().replace(",", ""))


def same_number(a, b):
    return a is not None and b is not None and abs(a - b) < 1e-6


def load_gsm8k(n, seed=0):
    rows = [json.loads(line) for line in open(DATA, encoding="utf-8")]
    random.Random(seed).shuffle(rows)
    return [{"id": f"gsm{i}", "question": r["question"], "truth": gsm8k_truth(r["answer"])} for i, r in enumerate(rows[:n])]


def load_freshqa():
    rows = json.load(open(FRESHQA, encoding="utf-8"))["rows"]
    return [{"id": f"fq{i}", "question": r["q"], "old": r["old0"], "new": r["new0"], "changed": r["changed"]}
            for i, r in enumerate(rows)]


# ----------------------------------------------------------------------------- the tools
SOLVE_PROMPT = ("Solve the maths word problem. Think step by step, then finish with one line of the form\n"
                "Answer: <number>\n\nProblem: {q}\n\nSolution:")


class SolverService:
    """E1 tool. `backend` answers until call number `switch_at`; after that `degraded` answers, silently."""

    def __init__(self, name, price, backend, degraded=None, switch_at=None, llms=None):
        self.name, self.price, self.backend, self.degraded, self.switch_at = name, price, backend, degraded, switch_at
        self.llms = llms if llms is not None else {}
        self.calls = 0

    def model_now(self):
        if self.degraded and self.switch_at is not None and self.calls >= self.switch_at:
            return self.degraded
        return self.backend

    def __call__(self, task):
        model = self.model_now()
        self.calls += 1
        llm = self.llms.setdefault(model, LLM(model))
        t0 = time.time()
        text = llm(SOLVE_PROMPT.format(q=task["question"]), max_tokens=400)
        value = parse_final_number(text)
        return {"tool": self.name, "model": model, "price": self.price, "text": text, "value": value,
                "loud": value is None, "correct": same_number(value, task["truth"]),
                "seconds": round(time.time() - t0, 2)}


QA_PROMPT = ("Use the knowledge-base entry to answer the question in one short sentence.\n"
             "Knowledge-base entry: {kb}\nQuestion: {q}\nAnswer:")


class QAService:
    """E2 tool. Answers from the OLD or NEW FreshQA snapshot entry; the old one is stale for changed facts."""

    def __init__(self, name, price, snapshot, model, llms=None):
        assert snapshot in ("old", "new")
        self.name, self.price, self.snapshot, self.model = name, price, snapshot, model
        self.llms = llms if llms is not None else {}

    def __call__(self, task):
        llm = self.llms.setdefault(self.model, LLM(self.model))
        t0 = time.time()
        text = llm(QA_PROMPT.format(kb=task[self.snapshot], q=task["question"]), max_tokens=80).strip()
        return {"tool": self.name, "model": self.model, "price": self.price, "text": text,
                "loud": text == "", "seconds": round(time.time() - t0, 2)}


# ----------------------------------------------------------------------------- checker and comparator
JUDGE_SOLUTION = ("Here is a maths word problem and a proposed solution.\nProblem: {q}\nProposed solution: {s}\n"
                  "Is the final answer correct? Reply with one word: YES or NO.\nReply:")
JUDGE_CURRENT = ("Question: {q}\nProposed answer: {a}\n"
                 "Is this answer correct and up to date as of 2026? Reply with one word: YES or NO.\nReply:")
SAME_ANSWER = ("Question: {q}\nAnswer 1: {a}\nAnswer 2: {b}\n"
               "Do the two answers give the same answer to the question? Reply with one word: YES or NO.\nReply:")


def _yes(text):
    t = text.strip().lower()
    return t.startswith("yes") or (re.search(r"\byes\b", t) is not None and re.search(r"\bno\b", t) is None)


class Checker:
    """A paid, imperfect judge. flag=True means 'this answer looks wrong'."""

    def __init__(self, model, price, llms=None, temperature=0.0):
        self.model, self.price, self.temperature = model, price, temperature
        self.llms = llms if llms is not None else {}

    def __call__(self, task, out, kind, seed=0):
        llm = self.llms.setdefault(self.model, LLM(self.model))
        prompt = (JUDGE_SOLUTION.format(q=task["question"], s=out["text"]) if kind == "maths"
                  else JUDGE_CURRENT.format(q=task["question"], a=out["text"]))
        reply = llm(prompt, max_tokens=5, temperature=self.temperature, seed=seed)
        return {"flag": not _yes(reply), "reply": reply.strip()[:20]}


class Comparator:
    """Do two answers agree? E1 compares numbers exactly (cannot be wrong); E2 asks a model (can be wrong)."""

    def __init__(self, model=None, llms=None):
        self.model = model
        self.llms = llms if llms is not None else {}

    def __call__(self, task, a, b, kind):
        if kind == "maths":
            return same_number(a["value"], b["value"])
        llm = self.llms.setdefault(self.model, LLM(self.model))
        return _yes(llm(SAME_ANSWER.format(q=task["question"], a=a["text"], b=b["text"]), max_tokens=5))


# ----------------------------------------------------------------------------- smoke test
def smoke(n, stub):
    """Call every tool, the checker and the comparator on n tasks per environment and print what came back.
    This is a pipeline check, not an experiment: no numbers from it go into the paper."""
    m = (lambda x: "stub") if stub else (lambda x: x)
    llms = {}
    if stub:
        from .freshqa_real import StubLLM
        llms["stub"] = StubLLM()
    print("E1 maths: service A degrades after 1 call")
    A = SolverService("A", 20, m("qwen2.5:3b"), degraded=m("qwen2.5:1.5b"), switch_at=1, llms=llms)
    B = SolverService("B", 24, m("phi4-mini"), llms=llms)
    chk = Checker(m("llama3.1:8b"), price=3.7, llms=llms)
    cmp_ = Comparator(llms=llms)
    for task in load_gsm8k(n):
        a, b = A(task), B(task)
        f = chk(task, a, "maths")
        print(f"  {task['id']}: truth={task['truth']:g} | A[{a['model']}]={a['value']} correct={a['correct']} "
              f"({a['seconds']}s) | B={b['value']} correct={b['correct']} ({b['seconds']}s) | "
              f"checker flags A: {f['flag']} | A and B agree: {cmp_(task, a, b, 'maths')}")
    print("E2 questions: tool A reads the old snapshot, tool B the new one")
    QA = QAService("A", 20, "old", m("phi4-mini"), llms=llms)
    QB = QAService("B", 24, "new", m("phi4-mini"), llms=llms)
    chk2 = Checker(m("llama3.1:8b"), price=3.7, llms=llms)
    cmp2 = Comparator(m("phi4-mini"), llms=llms)
    changed = [t for t in load_freshqa() if t["changed"]][:n]
    for task in changed:
        a, b = QA(task), QB(task)
        print(f"  {task['id']}: {task['question'][:60]}\n     A(old): {a['text'][:70]}\n     B(new): {b['text'][:70]}\n"
              f"     checker flags A: {chk2(task, a, 'questions')['flag']} | agree: {cmp2(task, a, b, 'questions')}")
    for llm in llms.values():
        llm.save()
    print("Smoke test finished. Model answers were saved to the cache in data/processed.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["smoke"])
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--stub", action="store_true", help="no Ollama: a fake model, for checking the pipeline only")
    a = ap.parse_args()
    smoke(a.n, a.stub)
