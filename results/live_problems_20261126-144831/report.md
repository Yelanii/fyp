# Live tools: problem-level bootstrap (follow-up, not pre-registered)

100 replicates, each 300 problems drawn with replacement from problems 201-500; per replicate 10 seeds (7700-7709) x 4 conditions per policy. 3097 s.

| Comparison | median difference | 95% interval over problems | share of replicates below 0 |
|---|---|---|---|
| label-light rule vs never check | -0.35% | -3.16% to +1.90% | 0.60 |
| label-light rule vs retrying rule told q, f | -1.53% | -4.30% to +2.37% | 0.80 |
| cross-check every call vs never check | -1.99% | -7.29% to +2.44% | 0.82 |
| cross-check every call vs retrying rule told q, f | -3.12% | -8.34% to +1.76% | 0.88 |
| rule (no labels) vs never check | +1.14% | -1.58% to +4.17% | 0.16 |
| label-light rule vs cross-check every call | +1.65% | -1.69% to +6.25% | 0.18 |
