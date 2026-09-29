# Binance Spot BTC-USDT 1m gaps

Minutes for which Binance's public klines API (`/api/v3/klines`, interval `1m`) returns no
candle. Most are exchange maintenance or trading halts. `scripts/import_candles.py` fills each
missing minute in Jesse's database with a synthetic, zero-volume candle flat at the last real
close before the gap. **Filled candles are not market data.**

## How this list was produced

- Scanned 2026-09-29, covering 2019-01-01 00:00 to 2026-09-28 23:59 UTC.
- Only candle open timestamps were read; prices and volumes were discarded. The final-test and
  reserved periods were scanned the same way. This is a data-coverage check, not final-test
  access, and is not recorded in the final-test access log.
- Times are UTC. "First missing" and "last missing" are the open times of the first and last
  absent 1m candles, inclusive.

## Gaps

| # | Split | First missing | Last missing | Minutes |
| ---: | --- | --- | --- | ---: |
| 1 | Research | 2019-03-12 02:00 | 2019-03-12 07:59 | 360 |
| 2 | Research | 2019-05-15 03:00 | 2019-05-15 12:59 | 600 |
| 3 | Research | 2019-06-07 21:14 | 2019-06-07 22:14 | 61 |
| 4 | Research | 2019-08-15 02:00 | 2019-08-15 09:59 | 480 |
| 5 | Research | 2019-11-13 02:00 | 2019-11-13 04:19 | 140 |
| 6 | Research | 2019-11-13 05:30 | 2019-11-13 05:32 | 3 |
| 7 | Research | 2019-11-25 02:00 | 2019-11-25 03:59 | 120 |
| 8 | Research | 2020-02-09 02:00 | 2020-02-09 02:59 | 60 |
| 9 | Research | 2020-02-19 11:36 | 2020-02-19 17:29 | 354 |
| 10 | Research | 2020-03-04 09:22 | 2020-03-04 11:29 | 128 |
| 11 | Research | 2020-04-25 02:00 | 2020-04-25 04:29 | 150 |
| 12 | Research | 2020-06-28 02:00 | 2020-06-28 05:29 | 210 |
| 13 | Research | 2020-11-30 06:00 | 2020-11-30 06:59 | 60 |
| 14 | Research | 2020-12-21 13:48 | 2020-12-21 17:59 | 252 |
| 15 | Research | 2020-12-25 02:00 | 2020-12-25 02:59 | 60 |
| 16 | Research | 2021-02-11 03:41 | 2021-02-11 04:59 | 79 |
| 17 | Research | 2021-03-06 02:00 | 2021-03-06 03:29 | 90 |
| 18 | Research | 2021-04-20 02:00 | 2021-04-20 04:29 | 150 |
| 19 | Research | 2021-04-25 04:01 | 2021-04-25 08:44 | 284 |
| 20 | Research | 2021-08-13 02:00 | 2021-08-13 06:29 | 270 |
| 21 | Research | 2021-09-29 07:00 | 2021-09-29 08:59 | 120 |
| 22 | Research | 2023-03-24 12:40 | 2023-03-24 13:59 | 80 |

Totals: 22 gaps, 4,111 minutes (about 68.5 hours), all in the research split. No gaps in
validation, final test, or reserved data up to 2026-09-28 23:59.

## Research implications

- An exchange that is down cannot fill orders. A backtest can still "fill" at the flat price
  during a gap, then see the whole outage move as one jump at reopening.
- A 1h candle overlapping a gap is partly or wholly synthetic: its range and volume understate
  the real market, and rolling volatility over it is biased low.
- Before trusting a result, check whether any trade opened, closed, or was held across a gap.
- In notebooks, synthetic minutes look like `volume == 0` with open = high = low = close.
