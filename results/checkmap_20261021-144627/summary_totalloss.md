# Check-worth map (metric: total_loss)

Cells: 126; seeds 200-209; wall time 173 s.

- Checking saves at least 5% in 90 of 126 cells.
- Cheapest non-oracle strategy per cell: Decision rule v2 56, Change alarm, CUSUM (B4) 32, Always check (B1) 25, Never check (B2) 12, Fixed-rate check (B3) 1
- Drop to 95%: median saving from checking +1.8%; rule v2 vs CUSUM median -0.4%
- Drop to 90%: median saving from checking +6.6%; rule v2 vs CUSUM median -5.0%
- Drop to 85%: median saving from checking +13.1%; rule v2 vs CUSUM median -2.0%
- Drop to 80%: median saving from checking +16.0%; rule v2 vs CUSUM median -5.3%
- Drop to 75%: median saving from checking +20.8%; rule v2 vs CUSUM median -0.7%
- Drop to 70%: median saving from checking +13.5%; rule v2 vs CUSUM median -1.8%
- Drop to 60%: median saving from checking +7.1%; rule v2 vs CUSUM median -1.7%
- Leak loss 1 task(s): median saving +5.1%; max +14.5%
- Leak loss 3 task(s): median saving +21.9%; max +43.7%