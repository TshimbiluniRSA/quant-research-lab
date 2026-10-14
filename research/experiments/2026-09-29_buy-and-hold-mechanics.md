# Backtest run record: 2026-09-29-BH-MECHANICS-01

Use one copy of this file per backtest run. It records mechanics (Stages 1–2), not evidence of
an edge. For multi-run hypothesis experiments, use `EXPERIMENT_TEMPLATE.md`.

## Run identity

- Date (UTC): 2026-09-29 (run finished 07:23 UTC)
- Git commit hash: `117f4bf` (repository HEAD at run time); strategy file last changed in `535cad2`
- Jesse version: 3.0.7 (Docker image `salehmir/jesse:3.0.7`), run from the dashboard
- Exchange: Binance Spot (spot mode: fees were charged in the bought coin, see below)
- Symbol: BTC-USDT
- Timeframe: 1h (single route, no data routes)
- Strategy: `BuyAndHoldBaseline`

## Data

- Date range (start – end): start 2019-01-21, finish 2019-03-11. Jesse treats the finish date as
  exclusive: the last 1m candle used is 2019-03-10 23:59 UTC.
- Data split this range belongs to: research/training
- First and last candle timestamps observed in results: the first 1h candle ran 2019-01-21
  00:00–01:00; the strategy acted when it closed, so the buy is timestamped 2019-01-21 01:00.
  The last 1h candle closed 2019-03-11 00:00, when Jesse closed the position.
- Warm-up candles: 210 (dashboard setting), i.e. 210 hours of 1h data before the start date.
- Candle source: imported with the dashboard's Import Candles page before the outage-filling
  import script existed. Local data covered 2019-01-01 00:00 to 2019-03-11 10:39 with every
  minute present; no Binance outage falls inside this run's range or its warm-up (first outage:
  2019-03-12 02:00, see `data/metadata/binance_spot_btcusdt_1m_gaps.md`).

## Cost and account assumptions

- Starting balance: 10000 USDT
- Fee rate: 0.001 (0.1% per order, charged on both the buy and the sell)
- Slippage: not modeled

## Jesse's reported metrics

Copy the numbers as Jesse reports them. Do not round or reinterpret them here.

| Metric | Value |
| --- | --- |
| Total trades | Total Closed Trades: 1 |
| Net profit | 991.11 |
| Net profit (%) | 9.91% |
| Total fees paid | 19.94 |
| Win rate | 100% |
| Max drawdown | -9.28% |
| Sharpe ratio | 1.87 |
| Starting balance | 10000 |
| Finishing balance | 10990.09 |
| Other: | Open Trades: 1; Max Underwater Period: 15 days; Annual Return: 102.03%; Avg Holding Time: 1175h 0m 0s; Sortino 2.92; Calmar 11; Omega 1.42 |

One trade over about seven weeks: the ratios and annual return are extrapolated from a single
observation and carry no evidential weight.

## One hand-verified trade

- Trade identifier / open time: the only trade; opened 2019-01-21 01:00 UTC, closed 2019-03-11
  00:00 UTC
- Side: long
- Entry price: 3539 (stored as 3539.0000000000005, floating-point noise)
- Exit price: 3916.82
- Quantity: 2.676 BTC bought; 2.673324 BTC held and sold after the entry fee
- Entry fee: 9.470364 USDT (taken as 0.002676 BTC)
- Exit fee: 10.47092890968 USDT
- Total fees: 19.94129290968 USDT

### My calculation

Show each step.

1. Quantity: 10000 × 0.95 = 9500; × (1 − 3 × 0.001) = 9471.5; ÷ 3539 = 2.67632…; rounded down to
   3 decimals = **2.676** (matches Jesse).
2. Buy: cost = 2.676 × 3539 = 9470.364; buy fee = 9470.364 × 0.001 = **9.470364**.
3. First attempt at the sell, assuming all 2.676 BTC were sold: 2.676 × 3916.82 = 10481.41032;
   sell fee = 10.48141032; total fee = **19.95177432** (Jesse: 19.94129290968, mismatch).
4. Corrected sell, using the BTC actually held after the entry fee: 2.676 × (1 − 0.001) =
   2.673324 BTC; × 3916.82 = 10470.92890968; sell fee = **10.47092890968**.
5. Corrected total fee: 9.470364 + 10.47092890968 = **19.94129290968** (exact match).
6. Final balance: USDT from the sell after its fee = 10470.92890968 − 10.47092890968 =
   10460.45798077; 10000 − 9470.364 + 10460.45798077 = **10990.09398077** (matches Jesse's
   10990.09).

- Gross PnL: 2.676 × (3916.82 − 3539) = 1011.04632 (Jesse's formula)
- Net PnL (after fees): real balance change = 10990.09398077 − 10000 = **990.09398077**

### Jesse's number

- Jesse's reported PnL for this trade: 991.1050270903193

### Mismatch explanation

If my number and Jesse's number differ, explain why (fee basis, rounding, precision,
fill price, other).

- **Fee basis (resolved).** On a spot exchange the buy fee is taken from the coin received, so
  only 2.673324 BTC were held and sold, not 2.676. My first sell fee assumed 2.676 BTC and was
  0.01048141032 too high. With the held quantity, fees match Jesse exactly.
- **PnL vs balance (explained).** Jesse computes trade PnL as `qty × (exit − entry) − fees`
  with qty = 2.676, the quantity bought. That counts the price rise on the 0.002676 BTC paid as
  the entry fee, which the exchange already owned: 0.002676 × 377.82 = 1.011. Hence
  991.105 − 1.011 = 990.094, the real balance change. Jesse's per-trade PnL overstates gains
  (and would overstate losses) by the price move on the fee coin. **The balance change is the
  true result.**

## Observations

- Jesse decides at candle close: the strategy's first decision was at 01:00, when the first
  1h candle finished, not at the 00:00 start date.
- The strategy invests 95% of the balance and shrinks the order by a further 3 × fee rate
  (`utils.size_to_qty`), leaving cash so fees never exceed the balance.
- The position was never sold by the strategy; Jesse closed it at the end of the backtest.
- Jesse's finish date is exclusive. Finish dates of 2019-03-13 and then 2019-03-12 failed
  because local data ended 2019-03-11 10:39. The error popup was titled "Missing Required
  Warmup Candles" and suggested importing from 2019-01-03, although the start and warm-up were
  fine and the missing data was at the end of the range.
- Summing trade PnLs would slightly misstate results in spot mode; use finishing − starting
  balance.

## Open questions

- Why does the summary report both "Total Closed Trades: 1" and "Open Trades: 1" for a single
  buy-and-sell?
- The dashboard showed no trade list and said the PnL-distribution chart lacked data; the trade
  details above were read from Jesse's `backtestsession` table. Is there a dashboard view that
  shows individual trades?
