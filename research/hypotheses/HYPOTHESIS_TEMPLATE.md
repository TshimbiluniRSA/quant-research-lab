# Hypothesis [HYPOTHESIS-ID]: [Title]

Status: Draft

Fill in every section **before any data is examined**, and commit the filled template before
the first backtest or analysis: the commit is the record that these choices came first. Once
data has been seen, do not edit the classification, markets, costs, placebo, variants or
decision criteria; write a new hypothesis version instead.

## Classification

- Strategy family: (one family from the coverage list in `strategies/REGISTRY.md`)
- Direction: long only | both

## Markets and timeframe

- Primary market: (exchange and pair, e.g. Binance Spot BTC-USDT)
- Timeframe:
- Confirmation markets: (declared now, tested later with the rules and parameters unchanged)
- Why these confirmation markets:

Every market must be declared in the pair table of `research/DATA_SPLITTING.md` and have a gap
file before its data is used. Markets chosen after seeing results do not count as confirmation.

## Rationale

Why might this effect exist? State the proposed market mechanism, not an indicator recipe.

## Expected effect

State the direction, horizon, and conditions precisely enough to be falsified.

## Null hypothesis

State what the observations should look like if the proposed effect does not exist.

## Data period and split role

- Source:
- Data split version: (e.g. v2, from `research/DATA_SPLITTING.md`)
- Research date range: [start, end) UTC
- Validation date range: [start, end) UTC
- Role of this work: research/training | validation | final test
- Known data limitations: (listing dates inside the range, documented gaps, symbol changes)

Do not inspect or record final-test outcomes during development.

## Cost assumptions

| Market | Fee per order | Slippage | Source of the assumption |
| --- | --- | --- | --- |
| | | | |

- Cost stress level: (e.g. fees and slippage doubled) The result must survive this to count.

If slippage is not modeled, write "not modeled" in its column and treat the result as optimistic.

## Placebo test

- Design: random entries with the same trade count and holding-period distribution as the
  strategy, on the same market, period and costs.
- Number of placebo runs:
- Random seed(s):
- Comparison: (e.g. the strategy's net result must beat the 95th percentile of placebo runs)

## Metrics

- Primary metric:
- Secondary metrics:
- Uncertainty/significance method:

## Variants and trials

- Number of variants planned:
- Variants: (list each one, e.g. timeframe or parameter choices)

Every variant run counts as a trial and must be recorded, including the ones that fail. A
variant added after seeing results is a new trial and needs a written reason.

## Decision criteria

Fill every cell with a measurable threshold before testing. This replaces a single failure
criterion: a result is classified, not just passed or failed.

| Outcome | Primary market | Confirmation markets | Placebo | Cost stress | Validation period |
| --- | --- | --- | --- | --- | --- |
| Validated | | | | | |
| Market-specific | | | | | |
| Rejected | | | | | |

A result on the primary market only is market-specific, not validated.

## Potential confounders

- Market regime:
- Time-of-day or session effects:
- Corporate actions or contract changes:
- Other:

## Known biases to note in the report

- Survivorship: (e.g. only pairs still trading today were considered)
- Market and timeframe selection:
- Look-ahead or leakage risks:
- Other:

## Next step

Describe the smallest experiment capable of testing the hypothesis.
