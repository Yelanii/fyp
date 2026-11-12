# Running the real AI agent test on your laptop

**What it does:** a small free AI model, running on your own computer, solves real maths word problems
(GSM8K) by calling calculator tools. One calculator service quietly starts giving wrong answers. The same
AI model is used as the checker ("is this result correct?"). We measure whether the earlier findings
also happen with a real AI model.

**What you need:** about 4 GB of free disk space, 8 GB of RAM, and an internet connection once to
download the model. No GPU and no API key are needed, and it costs nothing.

## Step 1: Install Ollama (once)

Download it from https://ollama.com and install it. On Windows and Mac it runs in the background
automatically.

## Step 2: Download the AI model (once, about 1 GB)

Open a terminal and run:

```
ollama pull qwen2.5:1.5b
```

If your laptop is slow, use `llama3.2:1b` instead, and use that name in every command below.

## Step 3: Set up the project (once)

Open a terminal in the `ereplan` folder, then:

```
python -m venv .venv
.venv\Scripts\activate          (Windows)   or   source .venv/bin/activate   (Mac/Linux)
pip install numpy scipy matplotlib pytest
python -m pytest -q             (should say "15 passed")
```

## Step 4: Run the three stages (keep Ollama running)

The times below are rough estimates for a laptop CPU.

```
python -m ereplan.realagent plan      --model qwen2.5:1.5b --n 300     (about 1 hour)
python -m ereplan.realagent calibrate --model qwen2.5:1.5b             (about 30-60 minutes)
python -m ereplan.realagent run       --model qwen2.5:1.5b --seeds 10  (about 1-3 hours)
```

- **plan:** the AI model writes calculator steps for each problem. Only problems it solves correctly
  with healthy tools are kept.
- **calibrate:** measures how often the AI checker catches obvious and subtle wrong answers, and how
  often it raises false alarms.
- **run:** runs all five strategies on the same problems and the same tool failures, then writes
  `results/realagent_.../report.md`.

Every AI answer is saved in `data/processed/llm_cache_*.json`. If you stop and restart, finished work
is not repeated, and anyone can re-check your results from the cache. You can leave it running
overnight.

## Step 5: Read the result

Open `report.md` and look at its last section, "Pre-registered checks". It says met or not met for
each of the four predictions in `PREREGISTRATION_realagent.md`. Those predictions were written before
any real data existed, so report all four, whatever they say.

## Testing without the AI model

```
python -m ereplan.realagent plan --model stub
python -m ereplan.realagent calibrate --model stub
python -m ereplan.realagent run --model stub --seeds 2
```

This uses fake plans and a simulated checker. It only shows that the code works. Never report these
numbers as results.

## Run 3: the test of rule v4 (fresh seeds, PREREGISTRATION_falsealarm.md part C)

Your plans and the judge calibration from Run 2 are reused, so only one command is needed:

```
python -m ereplan.realagent run --model qwen2.5:1.5b --seeds 10 --seed-start 3000
```

Read the last section of the report, "Pre-registered checks for rule v4" (R5 and R6).

## Replaying a run without the AI model

Every AI answer is saved in `data/processed/llm_cache_<model>.json`. With that file, anyone can repeat a
finished run exactly, without installing Ollama:

```
set EREPLAN_REPLAY=1            (Windows)   or   export EREPLAN_REPLAY=1   (Mac/Linux)
python -m ereplan.realagent run --model qwen2.5:1.5b --seeds 10
```

Any answer not in the cache is counted and treated as "no answer", so only replay seeds that were run live.

## Part D: second checker model and repeat test (about 2–3 hours, can run overnight)

```
ollama pull qwen2.5:3b
python -m ereplan.realagent repeat --model qwen2.5:1.5b --k 5 --temps 0,0.7
python -m ereplan.realagent repeat --model qwen2.5:1.5b --judge-model qwen2.5:3b --k 5 --temps 0,0.7
python -m ereplan.realagent calibrate --model qwen2.5:1.5b --judge-model qwen2.5:3b
python -m ereplan.realagent run --model qwen2.5:1.5b --judge-model qwen2.5:3b --seeds 10 --seed-start 3000
```
