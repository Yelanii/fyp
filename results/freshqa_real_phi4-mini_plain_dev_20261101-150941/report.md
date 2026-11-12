# FreshQA with a real judge (phi4-mini@plain), dev seeds 2500-2509

Judge rates (measured with labels): news: q 0.83, f 0.77, false 'same' 0.06; mixed: q 0.81, f 0.56, false 'same' 0.08
220 runs; 40 s. Wrong answer = 3 tasks. Verdicts repeat on retries (temperature 0).

| Strategy | told | news loss | news vs never | mixed loss | mixed vs never | wrong kept (news) | failed (news) | checks (news) | cross-checks (news) |
|---|---|---|---|---|---|---|---|---|---|
| never | true | 295.0 | +0.0% | 201.6 | +0.0% | 51.0% | 0.0% | 0.00 | 0.00 |
| always | true | 216.2 | -26.7% | 224.9 | +11.6% | 1.4% | 98.6% | 3.31 | 0.00 |
| cusum | true | 234.5 | -20.5% | 195.4 | -3.0% | 22.7% | 27.2% | 1.01 | 0.00 |
| v4 | true | 160.9 | -45.5% | 146.8 | -27.1% | 6.7% | 6.7% | 0.24 | 0.00 |
| v4_nocal | none | 221.1 | -25.1% | 226.2 | +12.2% | 1.8% | 98.2% | 3.31 | 0.00 |
| always_x | true | 262.2 | -11.1% | 235.5 | +16.8% | 3.0% | 0.2% | 5.39 | 3.96 |
| v5 | none | 161.4 | -45.3% | 140.6 | -30.2% | 9.0% | 0.0% | 0.11 | 0.08 |
| ssv | true | 263.0 | -10.8% | 234.7 | +16.5% | 9.1% | 48.5% | 4.35 | 1.92 |
| rdecusum | true | 213.5 | -27.6% | 211.2 | +4.8% | 1.2% | 93.9% | 3.15 | 0.00 |
| glrklucb | true | 219.3 | -25.7% | 225.2 | +11.7% | 2.3% | 97.7% | 3.31 | 0.00 |
| use_B | true | 125.9 | -57.3% | 125.9 | -37.5% | 0.0% | 0.0% | 0.00 | 0.00 |