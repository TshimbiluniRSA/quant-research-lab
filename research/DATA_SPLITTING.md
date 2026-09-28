# Data-splitting policy

Calendar ranges are unset for each dataset until they are declared in a dataset section of this
file; see [BTC-USDT boundaries](#btc-usdt-boundaries) for the first. A declared range stays
pending until the chosen provider's coverage and data quality are verified. Assign every
observation one role before strategy iteration begins.

## Research/training data

Use this partition freely for exploratory analysis, hypothesis development, implementation,
and initial parameter choices. Findings made here are hypotheses, not confirmation.

## Validation data

Use this partition to compare a limited number of documented strategy versions and to test
robustness. Every access is another opportunity to overfit, so record what was compared and
why. Repeated validation-driven revisions eventually contaminate this partition.

## Final test data

Keep this partition sealed throughout development. Open it once only after the hypothesis,
strategy version, parameters, costs, and decision criteria are frozen. Do not tune or repair a
strategy after observing final-test results. Any later change creates a new research version,
and the old final test must be recorded as contaminated for that new version.

The final test is not part of a routine notebook run, dashboard workflow, parameter search, or
automated campaign.

## BTC-USDT boundaries

Declared by the researcher on 2026-09-28, before any BTC-USDT backtest or analysis in this
repository. Status: **declared; pending coverage and quality verification** after import.

- Split definition version: **v1** (2026-09-28). Any change to the boundaries, seal scope, or
  candle-assignment rule creates a new version.
- Primary dataset: **Binance Spot BTC-USDT**.
- Seal scope: the periods below apply to **BTC on any exchange or quote currency**. BTC prices
  are highly correlated across venues, so viewing final-test-period BTC data from another
  exchange is final-test access.
- All times are UTC. Intervals are half-open, `[start, end)`: the start is included, the end is
  excluded and equals the next period's start.
- A candle belongs to the split containing its **open** timestamp (Jesse's timestamp
  convention). The 1h candle opening 2023-12-31 23:00 UTC is research, even though it closes at
  the 2024-01-01 00:00 boundary.

| Role | Start (inclusive, UTC) | End (exclusive, UTC) | Length | Researcher's regime notes |
| --- | --- | --- | --- | --- |
| Research/training | 2019-01-01 00:00 | 2024-01-01 00:00 | 5 years | Recovery, March 2020 crash, 2021 bull run, 2022 bear market (LUNA, FTX), 2023 recovery |
| Validation | 2024-01-01 00:00 | 2025-01-01 00:00 | 1 year | Spot ETF launch, halving, a new regime |
| Final test | 2025-01-01 00:00 | 2026-07-01 00:00 | 18 months | **Sealed.** Do not backtest, chart, or "just peek" |
| Reserved | 2026-07-01 00:00 | open | — | Unused; reserved as future out-of-sample data |

Jesse imports candles through the present, so final-test and reserved candles will exist in the
local database after import. Storage is not access: do not select, chart, or query those ranges.

### Warm-up and purging

- **Backtests:** Jesse warm-up candles may come from the preceding period. Indicators computed
  from past data are not leakage, so no gap is required between periods.
- **Notebook research:** any row whose forward-return window extends past the end of its split
  must be dropped (purged). A label that uses a later period's prices leaks that period into the
  earlier one. Purging means the last rows of each split, one horizon's worth, have no label.

### Scope and contamination

- One split is shared by **all** BTC-USDT hypotheses.
- Opening the final test for any hypothesis contaminates it for **every** BTC-USDT hypothesis.
  Record every opening in the access log below.
- The final test is opened **only for a fully frozen hypothesis**: hypothesis document,
  strategy code, parameters, cost assumptions, and decision criteria all committed, with the
  commit hash, Jesse version, and split definition version recorded below *before* the test is
  run. A Jesse upgrade can change fills or fees, so results are tied to the recorded version.

### Final-test access log

Append one row per opening. An empty table means the final test is still sealed.

| Date opened (UTC) | Hypothesis ID | Frozen commit hash | Jesse version | Split version | Outcome |
| --- | --- | --- | --- | --- | --- |
