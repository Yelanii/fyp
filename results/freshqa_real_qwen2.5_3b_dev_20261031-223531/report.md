# FreshQA with a real judge (qwen2.5:3b), dev seeds 2500-2509

Judge rates (measured with labels): news: q 1.00, f 1.00, false 'same' 0.00; mixed: q 1.00, f 0.99, false 'same' 0.01
200 runs; 85 s. Wrong answer = 3 tasks. Verdicts repeat on retries (temperature 0).

| Strategy | told | news loss | news vs never | mixed loss | mixed vs never | wrong kept (news) | failed (news) | checks (news) | cross-checks (news) |
|---|---|---|---|---|---|---|---|---|---|
| never | true | 295.0 | +0.0% | 201.6 | +0.0% | 51.0% | 0.0% | 0.00 | 0.00 |
| always | true | 207.1 | -29.8% | 208.8 | +3.6% | 0.0% | 100.0% | 3.00 | 0.00 |
| cusum | true | 230.6 | -21.8% | 192.6 | -4.4% | 20.8% | 32.0% | 1.05 | 0.00 |
| v4 | true | 157.1 | -46.8% | 145.6 | -27.8% | 4.4% | 8.9% | 0.28 | 0.00 |
| v4_nocal | none | 201.7 | -31.6% | 203.6 | +1.0% | 0.0% | 100.0% | 3.00 | 0.00 |
| always_x | true | 286.5 | -2.9% | 267.2 | +32.6% | 0.3% | 0.2% | 5.43 | 5.16 |
| v5 | none | 164.3 | -44.3% | 163.0 | -19.2% | 7.9% | 0.0% | 0.22 | 0.21 |
| ssv | true | 262.7 | -10.9% | 248.3 | +23.2% | 9.5% | 51.8% | 4.14 | 1.94 |
| rdecusum | true | 202.2 | -31.4% | 202.8 | +0.6% | 0.0% | 100.0% | 3.00 | 0.00 |
| glrklucb | true | 211.1 | -28.4% | 210.3 | +4.3% | 0.0% | 100.0% | 3.00 | 0.00 |