# Backtest run record: 2026-09-30-MAC-MECHANICS-01

Use one copy of this file per backtest run. It records mechanics (Stages 1–2), not evidence of
an edge. For multi-run hypothesis experiments, use `EXPERIMENT_TEMPLATE.md`.

## Run identity

- Date (UTC): 2026-09-30 (run finished 07:34 UTC; Jesse session
  `444f2335-ac6f-4b81-b5a2-2bf53af75d9f`)
- Git commit hash: `c786618` (repository HEAD at run time); strategy file last changed in `535cad2`
- Jesse version: 3.0.7 (Docker image `salehmir/jesse:3.0.7`), run from the dashboard
- Exchange: Binance Spot (spot mode: fees were charged in the bought coin)
- Symbol: BTC-USDT
- Timeframe: 1h (single route, no data routes)
- Strategy: `MovingAverageCrossover` (SMA 20/50, 25% of balance per entry, unoptimized)

## Data

- Date range (start – end): start 2019-01-21, finish 2019-03-11. Jesse treats the finish date as
  exclusive: the last 1m candle used is 2019-03-10 23:59 UTC. Same range as
  `2026-09-29_buy-and-hold-mechanics.md`.
- Data split this range belongs to: research/training
- First and last candle timestamps observed in results: the first 1h candle ran 2019-01-21
  00:00–01:00; the first trade opened 2019-01-22 17:00, the last closed 2019-03-10 22:00. The
  last 1h candle closed 2019-03-11 00:00 with no position open, so Jesse did not force-close
  anything.
- Warm-up candles: 210 (dashboard setting, read from Jesse's saved config), i.e. warm-up data
  from 2019-01-12 06:00 UTC.
- Candle source: the full outage-filled import (`make import-candles START=2019-01-01`,
  completed 2026-09-29).
- Gap check: no window in `data/metadata/binance_spot_btcusdt_1m_gaps.md` (22 gaps and 3 halts,
  read with `analytics.load_gap_windows`) overlaps 2019-01-12 06:00 – 2019-03-11 00:00 UTC, the
  warm-up plus range. The nearest is gap 1, starting 2019-03-12 02:00. Every candle in this run
  is real Binance data.

## Cost and account assumptions

- Starting balance: 10000 USDT
- Fee rate: 0.001 (0.1% per order, charged on both the buy and the sell)
- Slippage: not modeled. Every fill is at the candle close.

## Jesse's reported metrics

Copy the numbers as Jesse reports them. Do not round or reinterpret them here.

| Metric | Value |
| --- | --- |
| Total trades | Total Closed Trades: 13 |
| Net profit | 118.84 |
| Net profit (%) | 1.19% |
| Total fees paid | 65.03 |
| Win rate | 23.08% |
| Max drawdown | -2.24% |
| Sharpe ratio | 0.99 |
| Starting balance | 10000 |
| Finishing balance | 10118.65 |
| Other: | Open Trades: 0; Max Underwater Period: 17 days; Annual Return: 9.18%; Expectancy: 9.14 (0.09%); Avg Win / Avg Loss: 132.27 / 27.8 (ratio 4.76); Avg Holding Time: 49h 50m 46.15s (winners 105h, losers 33h 18m); Sortino 1.55; Calmar 4.1; Omega 1.25; Winning / Losing Streak: 1 / 5; Largest Win / Loss: 218.08 / -117.38; Winning / Losing Trades: 3 / 10 |

13 trades over seven weeks: the ratios and annual return are extrapolated from a tiny sample and
carry no evidential weight.

## Fees as a percentage of gross profit

Gross profit here means the price moves alone, before any fee: the sum over all 13 trades of
`qty × (exit − entry)`, computed from the trade list in Jesse's database.

- Gross profit (before fees): **183.87101 USDT**
- Total fees: **65.03368803793 USDT**
- Fees ÷ gross profit = 65.03368803793 ÷ 183.87101 = **35.37%**

More than a third of what the price moves earned went to the exchange. Each round trip costs
about 0.2% of the position (0.1% per side). With 13 round trips on about 2,500 USDT positions,
fees came to about 5 USDT per trade, while 4 of the 13 trades (2, 3, 8, 11) moved the price by less than that.

Do not confuse this with Jesse's internal `gross_profit` metric (396.80033), which is the sum of
the **winning trades' after-fee PnL**, with `gross_loss` (-277.96301) as the losing trades' sum.
The dashboard summary does not show either.

## One hand-verified trade

- Trade identifier / open time: trade 1 of 13; opened 2019-01-22 17:00 UTC, closed 2019-01-24
  05:00 UTC
- Side: long
- Entry price: 3571.76
- Exit price: 3540
- Quantity: 0.697 BTC bought; 0.696303 BTC held and sold after the entry fee
- Entry fee: 2.48951672 USDT (taken as 0.000697 BTC)
- Exit fee: 2.46491262 USDT
- Total fees: 4.95442934 USDT

### My calculation

Show each step. Balance before the trade: 10000.

1. Quantity: 10000 × 0.25 = 2500; × (1 − 3 × 0.001) = 2492.5; ÷ 3571.76 = 0.69783…; cut to 3
   decimals = **0.697** (matches Jesse). First attempts rounded to nearest (0.698); Jesse always
   rounds down so the order never costs more than the money set aside.
2. Buy: cost = 0.697 × 3571.76 = 2489.51672; buy fee = 2489.51672 × 0.001 = **2.48951672**.
3. BTC held after the buy fee: 0.697 × 0.999 = **0.696303**. Earlier attempts sold the full
   0.697 BTC, then rounded 0.696303 to 0.696 mid-calculation, which cost about 1.07 USDT of
   accuracy.
4. Sell: 0.696303 × 3540 = 2464.91262; sell fee = 2464.91262 × 0.001 = **2.46491262**.
5. Total fee: 2.48951672 + 2.46491262 = **4.95442934** (Jesse: 4.954429340000001, exact match).
6. Jesse's PnL formula: 0.697 × (3540 − 3571.76) − 4.95442934 = −22.13672 − 4.95442934 =
   **−27.09114934** (Jesse: −27.09114934000015, exact match).
7. Real balance change: money in = 2464.91262 − 2.46491262 = 2462.44770738; money out =
   2489.51672; 2462.44770738 − 2489.51672 = **−27.06901262**.

- Gross PnL: 0.697 × (3540 − 3571.76) = −22.13672 (Jesse's formula, before fees)
- Net PnL (after fees): real balance change = **−27.06901262**; Jesse's PnL = −27.09114934

### Jesse's number

- Jesse's reported PnL for this trade: −27.09114934000015

### Mismatch explanation

If my number and Jesse's number differ, explain why (fee basis, rounding, precision,
fill price, other).

- **Fees and Jesse's PnL: no mismatch** once the sell uses the held quantity (0.696303) and no
  intermediate value is rounded.
- **PnL vs balance (same cause as the BuyAndHold run).** Jesse computes PnL with qty = 0.697,
  the quantity bought, so it includes the price move on the 0.000697 BTC paid as the entry fee:
  0.000697 × (3540 − 3571.76) = −0.02213672. Hence −27.09114934 + 0.02213672 = −27.06901262,
  the real balance change. On a losing trade Jesse's PnL **overstates the loss**; on the
  BuyAndHold winning trade it overstated the gain. **The balance change is the true result.**
- **Whole run.** Summing Jesse's 13 trade PnLs gives 118.83732 (the reported net profit), but
  the balance grew by 118.65345 (10118.65345 − 10000). Replaying all 13 trades with
  `held × exit × (1 − fee) − qty × entry` reproduces the finishing balance 10118.65345095
  exactly.

## Observations

- Unlike BuyAndHold, every position was closed by the strategy's own exit signal. No trade was
  open at the end, and the summary shows "Open Trades: 0".
- Each entry used 25% of the **current** balance, so later trades' quantities depend on earlier
  results (trade 1 used 10000, trade 2 used 9972.93…).
- The edge, if any, is concentrated in 3 winners (trades 6, 9, 13). Trades 9 and 6 alone made
  356.05 of Jesse's net 118.84; the other 10 lost 277.96.
- Trades 2, 3, 8 and 11 moved the price by less than their round-trip fees: the
  crossover fires often in a sideways market, and each whipsaw costs about 5 USDT.
- Spot-mode fees make "net profit" a slightly wrong number to quote; use finishing − starting
  balance.

## Open questions

- How does the result change with fees at 0 and with much higher fees? This is the Stage 2
  exercise, and this run is its baseline.
- How does this compare with BuyAndHold over the same range (+990.09 after fees)? One short
  window cannot answer whether either is better; this record documents mechanics only.
