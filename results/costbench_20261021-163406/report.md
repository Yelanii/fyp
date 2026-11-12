# CostBench-derived evaluation

Seeds 500-511; 96 conditions; wall time 60 s; routes from data/processed/costbench_routes.json.

## Leak loss = 1: median extra loss over the perfect-knowledge optimum

| Strategy | All price gaps | Native CostBench prices | Gap 10% | Gap 20% |
|---|---|---|---|---|
| Never check (B2) | +1.5% | +1.7% | +1.5% | -0.0% |
| Always check (B1) | +12.2% | +13.9% | +13.8% | +10.3% |
| Fixed-rate check (B3) | +4.5% | +3.9% | +4.6% | +4.4% |
| Change alarm, CUSUM (B4) | +2.4% | +3.8% | +1.2% | +2.5% |
| Decision rule v2 | +0.9% | +1.9% | +0.6% | +0.0% |
| Oracle (knows truth) | -0.2% | -0.1% | -0.4% | -0.5% |

Lowest non-oracle: Decision rule v2. H-cb part for leak 1: met.

## Leak loss = 3: median extra loss over the perfect-knowledge optimum

| Strategy | All price gaps | Native CostBench prices | Gap 10% | Gap 20% |
|---|---|---|---|---|
| Never check (B2) | +8.5% | +5.7% | +13.3% | +11.1% |
| Always check (B1) | +8.0% | +8.2% | +9.5% | +7.9% |
| Fixed-rate check (B3) | +8.6% | +7.0% | +13.7% | +9.4% |
| Change alarm, CUSUM (B4) | +7.3% | +10.4% | +6.6% | +5.8% |
| Decision rule v2 | +1.4% | +2.3% | +0.8% | +0.5% |
| Oracle (knows truth) | -0.4% | -0.5% | -0.3% | -0.2% |

Lowest non-oracle: Decision rule v2. H-cb part for leak 3: met.

**H-cb: CONFIRMED**