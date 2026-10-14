# Strategy registry

The research status of every strategy in this folder. `README.md` describes how each example
works; this file records where each one stands as research. Strategy folders stay flat
(`strategies/<ClassName>/`) because Jesse loads them by folder name; this registry is the only
grouping by family.

Every strategy gets a row here when it is created. Its status changes only with a linked run
record (`research/experiments/`) or report (`research/reports/`) that justifies the change.

## Family coverage

Each family has one of three coverage values, judged from its strategies' statuses:

| Coverage | Rule |
| --- | --- |
| Not researched | No strategy in the family is Rejected, Validated or Market-specific. Learning, Hypothesis and Testing strategies do not count: nothing has been concluded yet. |
| Researched, nothing survived | Every concluded strategy in the family is Rejected. |
| Covered | At least one strategy in the family is Validated or Market-specific. |

Learning examples teach mechanics and say nothing about whether a family works. "Covered" by a
Market-specific strategy means it worked on one market only; check the strategy's status before
treating the family as validated.

| Family | Coverage | Strategies in family |
| --- | --- | --- |
| Trend following | Not researched | `MovingAverageCrossover` (Learning) |
| Mean reversion | Not researched | `RsiMeanReversion` (Learning) |
| Breakout | Not researched | `SimpleBreakout` (Learning) |
| Session breakout | Not researched | none |
| Opening momentum | Not researched | none |
| Carry | Not researched | none |
| Seasonality | Not researched | none |
| Pairs / relative value | Not researched | none |
| Event / news | Not researched | none |
| Volatility | Not researched | none |

Family labels organize ideas. They are not evidence of diversification: two strategies in
different families can still have highly correlated returns. Diversification claims require
measured return correlations.

## Statuses

| Status | Meaning |
| --- | --- |
| Learning | Educational example for Jesse mechanics. No hypothesis; makes no market claim. |
| Hypothesis | A hypothesis is written in `research/hypotheses/`, with family, primary market and confirmation markets declared, before any data is examined. |
| Testing | Being backtested on research data and checked against validation data (roadmap Stage 5). |
| Validated | Passed on the primary market and, unchanged, on the declared confirmation markets, including the placebo and cost stress tests, with a report in `research/reports/`. |
| Market-specific | Passed on the primary market only. Not validated. |
| Rejected | Failed its decision criteria. Keep the row: failed research is useful research. |

## Strategies

| Strategy | Family | Status | Primary market | Confirmation markets | Direction | Hypothesis ID | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `BuyAndHoldBaseline` | Benchmark (not a family) | Learning | — | — | Long only | — | Passive comparator for active strategies; invests 95% once and holds. Mechanics run: `research/experiments/2026-09-29_buy-and-hold-mechanics.md`. |
| `MovingAverageCrossover` | Trend following | Learning | — | — | Long only | — | SMA 20/50 cross, 25% of balance. Mechanics run: `research/experiments/2026-09-30_ma-crossover-mechanics.md`. |
| `RsiMeanReversion` | Mean reversion | Learning | — | — | Long only | — | RSI(14) below 30 entry, above 50 exit, 25% of balance. Not yet run. |
| `SimpleBreakout` | Breakout | Learning | — | — | Long only | — | Close above prior 20-bar high, exit below prior 10-bar low, 25% of balance. Not yet run. |

Learning examples have no primary or confirmation market. The mechanics runs used Binance Spot
BTC-USDT 1h only to exercise Jesse; they are not market choices.
