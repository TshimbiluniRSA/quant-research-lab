# Jesse learning strategies

These examples exist only to teach Jesse mechanics. They are not optimized, validated, safe
for live trading, or evidence of a market edge. Configure realistic fees in the dashboard and
inspect every order and trade.

For a first mechanical run, use one route such as `Binance Spot / BTC-USDT / 1h` after importing
that exchange-symbol's candles. The route is a reproducible smoke test, not a recommendation.

| Strategy | Entry | Exit | Position size | Stop / take profit | Learning objective |
| --- | --- | --- | --- | --- | --- |
| `BuyAndHoldBaseline` | First tradable candle | End of backtest | 95% of balance | None; benchmark exposure stays open | Establish a passive comparator and inspect a market order |
| `MovingAverageCrossover` | 20-SMA crosses above 50-SMA | Reverse cross | 25% of balance | Signal exit; no fixed stop or target | Learn indicators, cross detection, and dynamic exits |
| `RsiMeanReversion` | RSI(14) below 30 | RSI above 50 | 25% of balance | Signal exit; no fixed stop or target | Learn oscillator access and an intentionally simple mean-reversion rule |
| `SimpleBreakout` | Close above prior 20-bar high | Close below prior 10-bar low | 25% of balance | Channel exit; no fixed target | Learn raw candle columns, lookback exclusion, and trend exits |

All four examples are long-only so they can be run in spot mode. Jesse's candle arrays are
ordered `[timestamp, open, close, high, low, volume]`; the breakout deliberately excludes the
current candle from its channel to avoid comparing the close with future or self-derived data.

Fixed protective stops and take-profit orders are deliberately not bolted onto every example:
doing so would add arbitrary parameters without a hypothesis. Learn their mechanics separately
from Jesse's order documentation, then justify them in a versioned experiment before changing a
research strategy.
