# FreshQA with a real judge (llama3.1:8b@plain), dev seeds 2500-2509

Judge rates (measured with labels): news: q 0.79, f 0.76, false 'same' 0.08; mixed: q 0.76, f 0.52, false 'same' 0.10
200 runs; 39 s. Wrong answer = 3 tasks. Verdicts repeat on retries (temperature 0).

| Strategy | told | news loss | news vs never | mixed loss | mixed vs never | wrong kept (news) | failed (news) | checks (news) | cross-checks (news) |
|---|---|---|---|---|---|---|---|---|---|
| never | true | 295.0 | +0.0% | 201.6 | +0.0% | 51.0% | 0.0% | 0.00 | 0.00 |
| always | true | 216.5 | -26.6% | 228.4 | +13.3% | 1.4% | 98.4% | 3.33 | 0.00 |
| cusum | true | 244.5 | -17.1% | 187.8 | -6.8% | 26.3% | 25.5% | 0.95 | 0.00 |
| v4 | true | 160.7 | -45.5% | 142.9 | -29.1% | 6.7% | 6.7% | 0.24 | 0.00 |
| v4_nocal | none | 221.1 | -25.0% | 229.4 | +13.8% | 1.3% | 98.5% | 3.34 | 0.00 |
| always_x | true | 266.7 | -9.6% | 232.0 | +15.1% | 5.3% | 0.1% | 5.40 | 3.95 |
| v5 | none | 164.3 | -44.3% | 147.7 | -26.7% | 9.3% | 0.0% | 0.11 | 0.08 |
| ssv | true | 277.8 | -5.8% | 238.5 | +18.3% | 15.2% | 47.2% | 4.39 | 1.69 |
| rdecusum | true | 219.1 | -25.7% | 212.8 | +5.6% | 2.2% | 93.4% | 3.18 | 0.00 |
| glrklucb | true | 223.5 | -24.2% | 224.5 | +11.4% | 4.2% | 95.7% | 3.34 | 0.00 |