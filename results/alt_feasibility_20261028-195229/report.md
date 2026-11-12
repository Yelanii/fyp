# Feasibility: the alternative tool can degrade too (EXPLORATORY, not pre-registered)

Seeds 2100-2109; q 0.95, f 0.15, pi 1, leak 3; 300 runs; 127 s.

## Mean total loss per task

| Strategy | S1 only A | S2 B fails after switch | S3 independent | S4 shared cause | S5 A recovers |
|---|---|---|---|---|---|
| never | 186.3 | 217.2 | 212.9 | 208.9 | 177.4 |
| always | 216.4 | 229.4 | 233.8 | 227.2 | 211.1 |
| cusum | 187.1 | 225.2 | 217.0 | 265.5 | 176.6 |
| v4 | 171.4 | 177.9 | 182.8 | 187.9 | 166.1 |
| always_x | 175.8 | 206.8 | 215.2 | 221.5 | 173.2 |
| v5 | 164.5 | 176.6 | 189.6 | 185.6 | 166.8 |

## Loss compared with never checking

| Strategy | S1 only A | S2 B fails after switch | S3 independent | S4 shared cause | S5 A recovers |
|---|---|---|---|---|---|
| never | +0.0% | +0.0% | +0.0% | +0.0% | +0.0% |
| always | +16.1% | +5.6% | +9.8% | +8.8% | +19.0% |
| cusum | +0.4% | +3.7% | +1.9% | +27.1% | -0.4% |
| v4 | -8.0% | -18.1% | -14.2% | -10.1% | -6.3% |
| always_x | -5.7% | -4.8% | +1.1% | +6.0% | -2.4% |
| v5 | -11.7% | -18.7% | -10.9% | -11.2% | -6.0% |

## Mean tool switches per run

| Strategy | S1 only A | S2 B fails after switch | S3 independent | S4 shared cause | S5 A recovers |
|---|---|---|---|---|---|
| never | 1.0 | 2.0 | 1.9 | 2.0 | 1.0 |
| always | 4.1 | 4.5 | 4.3 | 4.3 | 3.8 |
| cusum | 5.9 | 11.1 | 9.7 | 17.2 | 4.6 |
| v4 | 1.3 | 2.0 | 2.0 | 2.0 | 1.3 |
| always_x | 1.0 | 2.4 | 2.2 | 1.4 | 1.2 |
| v5 | 1.3 | 1.9 | 1.6 | 1.6 | 1.2 |