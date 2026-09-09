"""Educational moving-average crossover; not a claim of profitability."""

import jesse.indicators as ta
from jesse import utils
from jesse.strategies import Strategy


class MovingAverageCrossover(Strategy):
    """Enter when a fast SMA crosses above a slow SMA and exit on the reverse cross."""

    fast_period = 20
    slow_period = 50

    @property
    def fast_sma(self):
        return ta.sma(self.candles, period=self.fast_period, sequential=True)

    @property
    def slow_sma(self):
        return ta.sma(self.candles, period=self.slow_period, sequential=True)

    def should_long(self) -> bool:
        return bool(utils.crossed(self.fast_sma, self.slow_sma, "above"))

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
        if utils.crossed(self.fast_sma, self.slow_sma, "below"):
            self.liquidate()
