# Review: `AAPLHourlyAnchorTrend`

Status: unvalidated learning artifact; not an approved research strategy

## What the code is trying to teach

The supplied strategy combines an hourly trading route with four-hour anchor candles. It uses
the side of a four-hour Supertrend line as its trend direction, requires ADX above 20, and tries
to enter after a one-bar pullback. It exits when the anchor direction reverses or hourly ATR
rises above four times entry ATR.

## Why it is not included as a runnable baseline

- The description says AAPL candles were unavailable and website metrics used BTC-USDT.
  Results from a different asset cannot establish an AAPL effect.
- The label `V107`, a fixed Sharpe target, optimization, and a 200-attempt search imply repeated
  outcome-guided iteration. Without a strict split and experiment history, this is overfitting
  risk rather than evidence.
- Jesse's official candle importers currently list crypto exchanges, not an AAPL equity source.
- The strategy assumes futures trading and short selling, which must be configured outside the
  class and are not equivalent to trading AAPL shares.
- It does not specify the tested data range, provider, fees, slippage, or validation boundary.

## Code-level questions to resolve before any experiment

1. `_entry_size()` calculates a 3% risk budget and then returns `qty * 2`. That multiplier can
   make realized stop risk exceed 3%; it must be proven with unit examples rather than assumed
   to represent leverage.
2. `leverage = 2` does not configure Jesse's exchange leverage. Exchange mode and leverage are
   backtest configuration, so code and run settings can disagree.
3. The sizing cap is expressed indirectly through a minimum stop distance. There is no explicit
   maximum notional or margin check after fees and exchange precision are applied.
4. `should_cancel_entry()` always returns true. Market-at-current-price entries may fill first,
   but the behavior should be inspected rather than accepted blindly.
5. The volatility exit and thresholds need a pre-registered rationale and sensitivity analysis.
6. The code needs a minimum-candle/warm-up assumption for Supertrend, ADX, and ATR.

## Safe learning exercise

First trace the four-hour candles, anchor value, signal booleans, proposed stop distance,
quantity, and monetary loss at the stop on a tiny synthetic dataset. Do not optimize it or use
the sealed final test. If its calculations are understood, create a new hypothesis and a new
strategy version with an independently sourced dataset and explicit costs.
