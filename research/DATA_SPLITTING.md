# Data-splitting policy

The calendar ranges remain unset until the chosen provider's coverage and data quality are
verified. Assign every observation one role before strategy iteration begins.

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

| Role | Start (UTC) | End (UTC) | Length | Researcher's regime notes |
| --- | --- | --- | --- | --- |
| Research/training | 2019-01-01 | 2023-12-31 | 5 years | Recovery, March 2020 crash, 2021 bull run, 2022 bear market (LUNA, FTX), 2023 recovery |
| Validation | 2024-01-01 | 2024-12-31 | 1 year | Spot ETF launch, halving, a new regime |
| Final test | 2025-01-01 | 2026-06-30 | 18 months | **Sealed.** Do not backtest, chart, or "just peek" |

Data after 2026-06-30 is unassigned and must not be used until a role is recorded here.

Open decisions (not yet made by the researcher):

- Exchange/dataset the split applies to (e.g. Binance Spot). Unconfirmed.
- Boundary convention: whether end dates include the full final day (through 23:59 UTC).
- Warm-up across boundaries: Jesse warm-up candles are read from before a run's start date, so
  a validation run starting 2024-01-01 would use late-2023 research candles for indicators.
  Decide whether that is acceptable or whether an embargo gap is required.
- Scope: whether this split is shared by every hypothesis on BTC-USDT, and therefore whether
  opening the final test for one hypothesis contaminates it for the others.

Jesse imports candles through the present, so final-test candles will exist in the local
database after import. Storage is not access: do not select, chart, or query that range.
