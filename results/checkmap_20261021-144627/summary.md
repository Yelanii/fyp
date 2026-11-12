# Check-worth map (metric: cost_per_success)

Cells: 126; seeds 200-209; wall time 173 s.

- Checking saves at least 5% in 78 of 126 cells.
- Cheapest non-oracle strategy per cell: Change alarm, CUSUM (B4) 49, Decision rule v2 40, Never check (B2) 22, Always check (B1) 13, Fixed-rate check (B3) 2
- Drop to 95%: median saving from checking -0.4%; rule v2 vs CUSUM median +1.6%
- Drop to 90%: median saving from checking -1.0%; rule v2 vs CUSUM median +0.9%
- Drop to 85%: median saving from checking +5.6%; rule v2 vs CUSUM median +0.3%
- Drop to 80%: median saving from checking +8.7%; rule v2 vs CUSUM median -0.4%
- Drop to 75%: median saving from checking +18.6%; rule v2 vs CUSUM median +0.6%
- Drop to 70%: median saving from checking +9.6%; rule v2 vs CUSUM median +1.7%
- Drop to 60%: median saving from checking +3.6%; rule v2 vs CUSUM median -0.1%
- Leak loss 1 task(s): median saving +7.0%; max +21.2%
- Leak loss 3 task(s): median saving +6.8%; max +21.9%