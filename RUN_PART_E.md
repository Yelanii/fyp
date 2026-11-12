# Part E on your laptop: the cost of persistent false alarms + baselines from the closest papers

No Ollama is needed. This is pure simulation on the CPU. Pre-registration: `PREREGISTRATION_persistence.md`.

## Step 1: Add the update (once)
1. Extract `ereplan-update-E.zip` into your **inner** project folder (the one that contains `ereplan`,
   `tests` and `README.md`).
2. Choose **Replace** when Windows asks. Only code files and two new documents are replaced. Your
   `data/` and `results/` folders are not touched.

## Step 2: Check everything still works (1 minute)
Open the terminal in the inner folder, with `(.venv)` showing, and run:

```
python -m pytest -q
```

You should see **20 passed**.

## Step 3: Re-run the tuning (under 1 minute)

```
python -m ereplan.persistence_exp dev
```

It should choose:
- **B9:** K = 1;
- **B10:** gamma 0.98, check rate 0.5;
- **B11:** n_off 20.

These are the same as in the pre-registration, because the simulation is deterministic.

## Step 4: Run the pre-registered test (about 1–2 hours; you can leave it running)

```
python -m ereplan.persistence_exp confirm --tuned results/persist_dev_20261024-222106/tuned.json
```

Keep the laptop plugged in and stop it from sleeping, as before.

At the end, the program prints the report and saves it to `results/persist_confirm_<time>/report.md`. The
numbers should match `results/persist_confirm_20261024-234247/report.md` (included in the zip) **exactly**. If they do, write "reproduced on laptop"
in your decision log.
