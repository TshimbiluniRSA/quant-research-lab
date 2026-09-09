"""Educational RSI mean-reversion example; not a claim of profitability."""

import jesse.indicators as ta
from jesse import utils
from jesse.strategies import Strategy


class RsiMeanReversion(Strategy):
    """Enter an oversold reading and exit when RSI returns toward neutral."""

    rsi_period = 14
    entry_threshold = 30
    exit_threshold = 50

    @property
    def rsi(self) -> float:
        return float(ta.rsi(self.candles, period=self.rsi_period))

    def should_long(self) -> bool:
        return self.rsi < self.entry_threshold

    def should_short(self) -> bool:
        return False

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self) -> None:
        qty = utils.size_to_qty(self.balance * 0.25, self.price, fee_rate=self.fee_rate)
        self.buy = qty, self.price

    def go_short(self) -> None:
        pass

    def update_position(self) -> None:
        if self.rsi > self.exit_threshold:
            self.liquidate()
