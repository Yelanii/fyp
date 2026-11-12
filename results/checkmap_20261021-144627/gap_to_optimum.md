# Distance to the perfect-knowledge optimum

Source: results/checkmap_20261021-144627/rows.json. Conditions: 126. Optimum is a lower bound (conditions where some strategy's mean fell >2% below it, from sampling noise: 5).

## Leak loss = 1 task(s)

| Strategy | Median excess loss over optimum | Median share of possible saving captured |
|---|---|---|
| Decision rule v2 | +2.5% | 64% |
| Change alarm, CUSUM (B4) | +2.8% | 61% |
| Always check (B1) | +8.3% | -36% |
| Fixed-rate check (B3) | +8.7% | 1% |
| Never check (B2) | +8.7% | 0% |
| Oracle (knows truth) | +0.4% | 91% |

## Leak loss = 3 task(s)

| Strategy | Median excess loss over optimum | Median share of possible saving captured |
|---|---|---|
| Decision rule v2 | +2.8% | 91% |
| Change alarm, CUSUM (B4) | +11.8% | 58% |
| Always check (B1) | +4.1% | 86% |
| Fixed-rate check (B3) | +26.4% | 16% |
| Never check (B2) | +32.3% | 0% |
| Oracle (knows truth) | +0.0% | 99% |
