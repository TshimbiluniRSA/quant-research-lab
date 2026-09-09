"""Educational price-channel breakout; not a claim of profitability."""

import numpy as np
from jesse import utils
from jesse.strategies import Strategy


class SimpleBreakout(Strategy):
    """Enter above a prior high channel and exit below a shorter prior low channel."""

    entry_lookback = 20
    exit_lookback = 10

    @property
    def prior_entry_high(self) -> float:
        return float(np.max(self.candles[-self.entry_lookback - 1 : -1, 3]))

    @property
    def prior_exit_low(self) -> float:
        return float(np.min(self.candles[-self.exit_lookback - 1 : -1, 4]))

    def should_long(self) -> bool:
        return self.price > self.prior_entry_high

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
        if self.price < self.prior_exit_low:
            self.liquidate()
