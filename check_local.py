"""Check this machine before running anything.

    python check_local.py            # data files, Python packages, Ollama models
    python check_local.py --live 20  # also re-judge 20 FreshQA questions per judge with YOUR Ollama models and
                                     # compare with the saved verdicts the experiments use

Nothing is downloaded and no saved file is changed.
"""
import argparse, hashlib, json, os, sys, urllib.request

MODELS = ("qwen2.5:1.5b", "qwen2.5:3b", "phi4-mini", "llama3.1:8b", "llama3.2:3b")
JUDGES = ("phi4-mini@plain", "llama3.1:8b@plain")
OLLAMA = os.environ.get("OLLAMA_URL", "http://localhost:11434")
ok = True


def say(good, text):
    global ok
    ok = ok and good
    print(("  OK    " if good else "  FAIL  ") + text)


def data():
    print("1. Data files (already inside this folder; nothing to download)")
    man = json.load(open("data/MANIFEST.json"))
    for p, m in man.items():
        if not os.path.exists(p):
            say(False, f"{p} is missing"); continue
        same = hashlib.sha256(open(p, "rb").read()).hexdigest() == m["sha256"]
        # the LLM answer caches grow when you run models locally, so a different hash there is not an error
        if not same and "llm_cache_" in p:
            print(f"  NOTE  {p} differs from the packaged copy (normal if you have run the models since)")
        else:
            say(same, f"{p}" + ("" if same else " has changed (hash differs from data/MANIFEST.json)"))


def packages():
    print("2. Python packages")
    say(sys.version_info >= (3, 11), f"Python {sys.version.split()[0]} (needs 3.11 or newer)")
    for name in ("numpy", "scipy", "matplotlib", "pytest"):
        try:
            mod = __import__(name); say(True, f"{name} {mod.__version__}")
        except ImportError:
            say(False, f"{name} is not installed: pip install {name}")


def ollama():
    print("3. Ollama models (needed only for --live and for collecting new verdicts)")
    try:
        tags = json.load(urllib.request.urlopen(OLLAMA + "/api/tags", timeout=10))
    except Exception as e:  # noqa: BLE001
        print(f"  NOTE  Ollama is not reachable at {OLLAMA} ({e}). Start it with: ollama serve"); return False
    have = {m["name"] for m in tags.get("models", [])}
    have |= {n.removesuffix(":latest") for n in have}
    for m in MODELS:
        if m in have:
            say(True, m)
        else:
            print(f"  NOTE  {m} is not pulled: ollama pull {m}")
    return True


def live(n):
    print(f"4. Live check: {n} questions per judge, your model's verdict vs the saved verdict")
    from ereplan import freshqa_real as fr
    from ereplan.realagent import LLM
    rows = json.load(open(fr.DATA))["rows"]
    for judge in JUDGES:
        name = fr.split_model(judge)[0]
        saved = json.load(open(fr.verdict_path(judge)))["items"]
        llm = LLM(name); llm.cache = {}                         # force real calls; nothing is saved
        same = total = 0
        for r in rows[:n]:
            v = saved[fr.norm(r["q"])]
            for ans, key in ((r["old0"], "flag_old"), (r["new0"], "flag_new")):
                flag = not fr._yes(llm(fr.PLAIN_PROMPT.format(q=r["q"], a=ans), max_tokens=4))
                same += flag == v[key]; total += 1
        say(same == total, f"{judge}: {same}/{total} verdicts identical to the saved file"
            + ("" if same == total else " (a different Ollama or model version can change a few verdicts; record this)"))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--live", type=int, default=0)
    a = ap.parse_args()
    data(); packages(); up = ollama()
    if a.live:
        if up:
            live(a.live)
        else:
            say(False, "--live needs Ollama running")
    print("\nAll checks passed." if ok else "\nSome checks failed: see FAIL lines above.")
    sys.exit(0 if ok else 1)
