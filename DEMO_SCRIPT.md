# Five-minute demo for the supervisor

Run (inside the inner `ereplan` folder, with `(.venv)` showing):
```
python -m ereplan.showcase
```
It takes about 10 seconds and needs no internet or Ollama. Then open `results\showcase_v4.png`.

## What to say (about 1 minute per part)

1. **The problem.**
   - "The agent pays for a cheap tool that quietly gets worse. Some of its mistakes are visible errors,
     others are wrong answers."
   - "It can pay to check an answer, but the checker itself makes mistakes. Like the real AI checkers I
     tested, it rejects some correct answers, and it rejects them again every time."
2. **Part 1 (decisions).**
   - "My rule v4 decides on every call whether a check is worth its price, counting the risk that the
     check wrongly blocks a good answer."
   - "Here it noticed the drop mostly from free visible errors, and switched tools."
   - Show the plot: the dotted line is the hidden drop, and the green line is the switch.
3. **Part 2 (same world, all strategies).**
   - "Always-check fails over half the tasks because of false alarms. Never-check lets a third of the
     wrong answers through."
   - "In this one run CUSUM was slightly lower. That is why the claims rest on the planned tests, not on
     one example."
4. **Part 3 (real AI).** "This replays my laptop run with a real AI, from its saved answers. Over all 10
   test seeds, v4 had the lowest loss: 73.8 against 81.0 for the best existing method."
5. **Part 4 (findings).**
   - RQ1: checking pays most at moderate degradation.
   - RQ2: checking backfires in two ways.
   - RQ3: v4 beats the baselines in simulation and with two real AI checkers.
   - Limits: one model family, maths tasks only.

## Recording it (optional)
- Windows 11: open the **Snipping Tool**, choose **Record**, select the VS Code window, and press Start.
- Or press **Win + Alt + R** (Xbox Game Bar) while VS Code is in front.
- Run the command, scroll through the output, and open the plot.
