# Data-splitting policy

Calendar ranges are unset for each dataset until they are declared in a dataset section of this
file; see [Crypto boundaries (v2)](#crypto-boundaries-v2) for the current definition. A declared
range stays pending until the chosen provider's coverage and data quality are verified. Assign
every observation one role before strategy iteration begins.

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

## Crypto boundaries (v2)

Proposed and adopted by the researcher on 2026-10-14 to extend v1 from BTC-USDT to every
Binance Spot crypto pair. Status: **adopted 2026-10-14.** The calendar boundaries are unchanged
from v1. Only the dataset scope and the seal scope change.

- Split definition version: **v2** (adopted 2026-10-14; supersedes
  [v1](#v1-btc-usdt-boundaries-superseded)). Any change to the boundaries, seal scope, or
  candle-assignment rule creates a new version.
- Dataset scope: **every Binance Spot crypto pair** declared in the
  [pair table](#declared-pairs). A pair is not research data until it is declared there.
- Seal scope: the final-test and reserved periods apply to **all crypto assets on any exchange
  or quote currency**, including pairs that are not declared. Crypto prices are highly
  correlated with BTC, so viewing final-test-period data for any coin leaks information about
  BTC and every other declared pair.
- All times are UTC. Intervals are half-open, `[start, end)`: the start is included, the end is
  excluded and equals the next period's start.
- A candle belongs to the split containing its **open** timestamp (Jesse's timestamp
  convention). The 1h candle opening 2023-12-31 23:00 UTC is research, even though it closes at
  the 2024-01-01 00:00 boundary.

| Role | Start (inclusive, UTC) | End (exclusive, UTC) | Length | Researcher's regime notes |
| --- | --- | --- | --- | --- |
| Research/training | 2019-01-01 00:00 | 2024-01-01 00:00 | 5 years | Recovery, March 2020 crash, 2021 bull run, 2022 bear market (LUNA, FTX), 2023 recovery |
| Validation | 2024-01-01 00:00 | 2025-01-01 00:00 | 1 year | Spot ETF launch, halving, a new regime |
| Final test | 2025-01-01 00:00 | 2026-07-01 00:00 | 18 months | **Sealed for all crypto.** Do not backtest, chart, or "just peek" |
| Reserved | 2026-07-01 00:00 | open | — | Unused; reserved as future out-of-sample data |

Jesse imports candles through the present, so final-test and reserved candles will exist in the
local database after import. Storage is not access: do not select, chart, or query those ranges.

### Declared pairs

The researcher declares pairs here before importing or analysing them. A pair listed after
2019-01-01 has a shorter research period. Declare that before looking at its data, not after.

| Pair | Declared (UTC) | First Binance 1m candle (UTC) | Research coverage | Gap file | Coverage status |
| --- | --- | --- | --- | --- | --- |
| BTC-USDT | 2026-09-28 (v1) | before 2019-01-01 | 100% | [`binance_spot_btcusdt_1m_gaps.md`](../data/metadata/binance_spot_btcusdt_1m_gaps.md) | Timestamps verified 2026-09-29; quality checks pending |

Each pair needs its own gap file, `data/metadata/binance_spot_<base><quote>_1m_gaps.md`, from a
timestamp-only scan of that pair (`scripts/scan_gaps.py`), before its data is used. Binance
outages are mostly exchange-wide, but edges can differ by a minute between pairs, and listings,
delistings and symbol reuse are pair-specific.

### Pair-selection hazards

- **Survivorship bias.** Choosing only pairs that trade today, or that are large today, uses
  information from after the research period. Coins that collapsed or were delisted, such as
  LUNA (2022), FTT (2022) and MATIC (migrated to POL in 2024), are part of the history.
- **Symbol reuse.** One symbol can cover two assets. `LUNAUSDT` holds the original Terra coin
  until 2022-05-12 and Terra 2.0 from 2022-05-31. Treat such a series as two pairs, or exclude it.
- **Pairs ending inside a split.** A pair whose trading ends during validation or final test
  (for example `MATICUSDT` on 2024-09-10, `EOSUSDT` on 2025-05-26) cannot be evaluated over the
  full later periods.

## v1: BTC-USDT boundaries (superseded)

Superseded by [v2](#crypto-boundaries-v2) on 2026-10-14. Kept for the record: run records
made before that date used v1. v2 keeps every v1 boundary, so v1 research and validation
results remain valid.

Declared by the researcher on 2026-09-28, before any BTC-USDT backtest or analysis in this
repository.

- Split definition version: **v1** (2026-09-28).
- Primary dataset: **Binance Spot BTC-USDT**.
- Seal scope: the periods apply to **BTC on any exchange or quote currency**. BTC prices are
  highly correlated across venues, so viewing final-test-period BTC data from another exchange
  is final-test access.
- Boundaries, interval convention, and candle-assignment rule: identical to v2.

Coverage: Binance has 22 gaps (4,111 minutes) and 3 halts published as zero-volume candles
(226 minutes), all in research, listed in
[`data/metadata/binance_spot_btcusdt_1m_gaps.md`](../data/metadata/binance_spot_btcusdt_1m_gaps.md).
`scripts/import_candles.py` fills them with synthetic flat candles; check that list before
trusting a result whose range spans a gap. Quality checks beyond timestamp coverage are pending.

## Warm-up and purging

- **Backtests:** Jesse warm-up candles may come from the preceding period. Indicators computed
  from past data are not leakage, so no gap is required between periods.
- **Notebook research:** any row whose forward-return window extends past the end of its split
  must be dropped (purged). A label that uses a later period's prices leaks that period into the
  earlier one. Purging means the last rows of each split, one horizon's worth, have no label.

## Scope and contamination

- One split is shared by **all** crypto hypotheses (v1: all BTC-USDT hypotheses).
- Opening the final test for any hypothesis contaminates it for **every** crypto hypothesis,
  on every pair. Record every opening in the access log below.
- The final test is opened **only for a fully frozen hypothesis**: hypothesis document,
  strategy code, parameters, cost assumptions, and decision criteria all committed, with the
  commit hash, Jesse version, and split definition version recorded below *before* the test is
  run. A Jesse upgrade can change fills or fees, so results are tied to the recorded version.

## Final-test access log

Append one row per opening. An empty table means the final test is still sealed.

| Date opened (UTC) | Hypothesis ID | Frozen commit hash | Jesse version | Split version | Outcome |
| --- | --- | --- | --- | --- | --- |
