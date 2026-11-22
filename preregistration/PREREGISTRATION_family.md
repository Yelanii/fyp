# Pre-registration: Study F, model family or accuracy of the second tool?

**Written:** 21 November 2026, before the confirmatory run. Run once, on the author's laptop.

## Why
Studies M and M2 found that for a flagged qwen2.5:1.5b answer, phi4-mini (another family) was the better guess on
disagreement, but qwen2.5:3b (same family) was not reliably so. A review of draft v1.0 noted that phi4-mini is also
much more accurate, so family and accuracy are confounded.

## Design (`measure_family.py`)
- **Problems:** GSM8K problems 201-500 of the subset-seed-11 shuffle (Study M2's problems), temperature 0.
- **New solver:** llama3.2:3b (a different family from Qwen, with accuracy expected to be close to qwen2.5:3b),
  through the same solver service. The answers of qwen2.5:1.5b, qwen2.5:3b, phi4-mini and the llama3.1:8b checker's
  flags on qwen2.5:1.5b are taken unchanged from Study M2.
- **Measure:** the error lift of each alternative X relative to qwen2.5:1.5b,
  lift(X) = P(X wrong | qwen2.5:1.5b wrong) / P(X wrong), which does not depend on X's accuracy.

## Hypotheses
- **H-F1.** Same-family errors are more related: lift(qwen2.5:3b) - lift(llama3.2:3b) > 0, with the 95% problem-level
  paired bootstrap CI (10,000 resamples, seed 7) above 0.
- **H-F2.** llama3.2:3b is the better guess on flagged disagreements with qwen2.5:1.5b (one-sided binomial test
  against 0.5, alpha = 0.05).
- **Reported regardless of outcome:** accuracy, P(wrong | 1.5B wrong), P(wrong), lift and the A2 rate for all three
  alternatives.

## What the outcomes would mean
- **H-F1 confirmed:** a same-family alternative shares more mistakes than a different-family one of similar accuracy;
  the paper's "different family" advice stands on its own, not only through accuracy.
- **H-F1 not confirmed:** the data do not separate family from accuracy (with about 120 problems on which qwen2.5:1.5b
  is wrong, a small difference may not be detectable); the paper narrows the advice to "a second tool that is more
  accurate and does not share the flagged tool's mistakes".
- **H-F2:** whether a matched-accuracy, different-family alternative satisfies A2.

## Disclosure
The accuracies of the four existing models on these problems are known from Study M2. llama3.2:3b has not been run
on them. The code was tested on the cloud machine with a fake model only.
