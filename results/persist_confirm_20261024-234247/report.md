# Part E: cost of persistent false alarms and baselines from the closest works (pre-registered)

Seeds 1400-1419; 25920 rows (18880 runs, the rest copied where results cannot differ); 4882 s. Metric: total loss per task incl. one task cost per failed task.
Tuned baselines (dev seeds 1500-1505): {"b9_vrr": {"window": 30, "reverify_k": 1}, "b10_pb": {"gamma": 0.98, "check_rate": 0.5}, "b11_btm": {"n_off": 20.0, "horizon_mode": "session", "session_cap": 50}}

## Mean total loss by false-alarm rate f and persistence pi (pooled over drop, q, leak)

| f | pi | never | always | cusum | v4 | v4_ind | v4_match | b9_vrr | b10_pb | b11_btm |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | - | 160.7 | 140.9 | 143.6 | 137.2 | 137.2 | 137.2 | 140.9 | 156.1 | 175.7 |
| 0.05 | 0 | 160.7 | 147.4 | 144.6 | 142.7 | 141.3 | 141.3 | 146.2 | 160.6 | 175.7 |
| 0.05 | 0.5 | 160.7 | 154.8 | 146.1 | 144.6 | 148.1 | 145.9 | 152.2 | 164.9 | 175.7 |
| 0.05 | 0.8 | 160.7 | 164.0 | 148.2 | 146.8 | 154.7 | 148.7 | 162.4 | 168.5 | 175.7 |
| 0.05 | 1 | 160.7 | 172.4 | 150.6 | 148.5 | 159.9 | 148.5 | 174.7 | 171.5 | 175.7 |
| 0.15 | 0 | 160.7 | 167.5 | 150.1 | 144.4 | 146.5 | 146.5 | 154.0 | 171.0 | 175.7 |
| 0.15 | 0.5 | 160.7 | 195.6 | 154.3 | 144.8 | 153.9 | 147.0 | 173.9 | 180.6 | 175.7 |
| 0.15 | 0.8 | 160.7 | 202.3 | 158.6 | 145.0 | 160.2 | 145.3 | 190.9 | 188.6 | 175.7 |
| 0.15 | 1 | 160.7 | 205.9 | 161.5 | 145.5 | 163.4 | 145.5 | 195.5 | 195.6 | 175.7 |

## Cost of false alarms (loss at f minus loss at f = 0, same seeds), pooled over f = 0.05 and 0.15

| Strategy | pi = 0 | pi = 0.5 | pi = 0.8 | pi = 1 |
|---|---|---|---|---|
| never | +0.0 | +0.0 | +0.0 | +0.0 |
| always | +16.6 | +34.4 | +42.3 | +48.3 |
| cusum | +3.7 | +6.6 | +9.7 | +12.4 |
| v4 | +6.3 | +7.4 | +8.7 | +9.8 |
| v4_ind | +6.6 | +13.8 | +20.2 | +24.4 |
| v4_match | +6.6 | +9.2 | +9.8 | +9.8 |
| b9_vrr | +9.3 | +22.2 | +35.8 | +44.2 |
| b10_pb | +9.7 | +16.7 | +22.5 | +27.5 |
| b11_btm | +0.0 | +0.0 | +0.0 | +0.0 |

## Where the false-alarm cost goes (pooled over f > 0; per task)

| Strategy | pi | failed-task cost | leak cost | tool + check spend | switch spend | tasks failed with a false alarm | false switches /1000 |
|---|---|---|---|---|---|---|---|
| always | 0 | +2.4 | -1.0 | +15.3 | +0.0 | 2.4% | +2.6 |
| always | 1 | +46.6 | -0.7 | +2.2 | +0.1 | 38.2% | +8.5 |
| v4 | 0 | -0.1 | +17.5 | -11.1 | -0.0 | 0.1% | -0.2 |
| v4 | 1 | +2.4 | +16.2 | -8.8 | +0.0 | 2.1% | +1.3 |
| v4_ind | 0 | +0.8 | +5.8 | -0.1 | +0.0 | 0.7% | -0.0 |
| v4_ind | 1 | +16.3 | +3.2 | +4.9 | +0.0 | 13.5% | +3.6 |
| b9_vrr | 0 | +0.5 | +3.1 | +5.7 | +0.0 | 0.8% | +1.0 |
| b9_vrr | 1 | +32.6 | +0.9 | +10.7 | +0.1 | 27.0% | +8.5 |

## Pre-registered hypotheses
- H-E1 always-check: false-alarm cost at pi = 1 (48.3) > at pi = 0 (16.6), ratio 2.9 (need >= 3), p = 9.4e-107 -> NOT CONFIRMED. By pi (descriptive): 0: 16.6, 0.5: 34.4, 0.8: 42.3, 1: 48.3; monotone: True
- H-E3 at pi = 1, v4 < v4_ind by >= 5%: 147.0 vs 161.7 (-9.0%), p = 6.7e-83 -> CONFIRMED
- H-E4 at pi = 0, v4_ind < v4: 143.9 vs 143.6 (+0.2%), p = 1 -> NOT CONFIRMED
- H-E5 at pi in {0.5, 0.8}, v4_match below v4 and v4_ind: 146.7 vs 145.3 (p = 1) and 154.2 (p = 2.5e-114) -> NOT CONFIRMED
- H-E6 f > 0, all pi: v4_match (146.1) below each literature baseline by >= 5% (Holm): b9_vrr 168.7 (p = 3.2e-297, Holm ok, 5% ok); b10_pb 175.2 (p = 0, Holm ok, 5% ok); b11_btm 175.7 (p = 3.3e-269, Holm ok, 5% ok) -> CONFIRMED
- H-E7 f = 0: v4_match 137.2 within 2% of the best literature baseline 140.9 -> CONFIRMED
- H-E8a pi = 1: re-verification raises the false-alarm cost (B9 44.2 vs always 48.3), p = 0.018 -> CONFIRMED
- H-E8b pi = 0: re-verification lowers the false-alarm cost (B9 9.3 vs always 16.6), p = 1.4e-61 -> CONFIRMED

## Per drop at f = 0.15 (mean loss)

| drop | pi | never | always | cusum | v4 | v4_ind | v4_match | b9_vrr | b10_pb | b11_btm |
|---|---|---|---|---|---|---|---|---|---|---|
| 95% | 0.8 | 132.0 | 188.0 | 153.6 | 134.6 | 153.6 | 135.7 | 180.9 | 166.6 | 132.0 |
| 95% | 1 | 132.0 | 196.4 | 154.2 | 134.9 | 157.0 | 134.9 | 188.9 | 173.7 | 132.0 |
| 85% | 0.8 | 165.9 | 199.2 | 159.5 | 146.0 | 161.3 | 146.4 | 189.5 | 184.7 | 166.1 |
| 85% | 1 | 165.9 | 203.8 | 160.6 | 146.8 | 164.6 | 146.8 | 194.7 | 189.6 | 166.1 |
| 75% | 0.8 | 177.2 | 208.9 | 160.7 | 149.1 | 163.5 | 148.9 | 197.1 | 198.7 | 195.3 |
| 75% | 1 | 177.2 | 210.4 | 165.0 | 149.5 | 166.5 | 149.5 | 198.9 | 203.7 | 195.3 |
| 60% | 0.8 | 167.6 | 213.1 | 160.5 | 150.3 | 162.4 | 150.4 | 196.0 | 204.3 | 209.3 |
| 60% | 1 | 167.6 | 212.9 | 166.1 | 150.9 | 165.6 | 150.9 | 199.6 | 215.2 | 209.3 |