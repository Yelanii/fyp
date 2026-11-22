# Results

Each folder is one run, named `<experiment>_<mode>_<run id>`:

- `mode` is `confirm` for a pre-registered confirmatory run and `dev` for a development run on separate seeds;
- the run id is the date and time at which the run started (`YYYYMMDD-HHMMSS`); a suffix `_netpv` marks a run of the
  corrected-rule suite, which used the corrected check criterion;
- `report.md` holds the tables and the verdict on every pre-registered hypothesis, and `rows.json` holds one row per
  run, which `reproduce_paper.py` replays.

The folders behind each result in the paper are listed in [docs/REPRODUCING.md](../docs/REPRODUCING.md).

Three confirmatory runs were made twice with identical rows; only the run time differs. The folder listed in
`docs/REPRODUCING.md` is the one reported:

| Reported | Identical repeat |
|---|---|
| `detect_confirm_20261120-230307` | `detect_confirm_20261120-235201` |
| `priorfix_live_confirm_20261121-151854` | `priorfix_live_confirm_20261121-150522` |
| `realagent_v5_20261119-175229` | `realagent_v5_20261118-112712` |

The other folders come from earlier stages of the project (rules v2 to v4, development runs and exploratory checks)
and are kept for completeness. `superseded/` holds the first pilot run, which used a prior that was later corrected.
