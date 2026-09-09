"""Educational buy-and-hold benchmark; not a claim of profitability."""

from jesse import utils
from jesse.strategies import Strategy


class BuyAndHoldBaseline(Strategy):
    """Enter once and remain invested so active examples have a simple comparator."""

    def should_long(self) -> bool:
        return self.index == 0

    def should_short(self) -> bool:
        return False

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self) -> None:
        # Leave a cash buffer so fees do not make the order exceed the available balance.
        qty = utils.size_to_qty(self.balance * 0.95, self.price, fee_rate=self.fee_rate)
        self.buy = qty, self.price

    def go_short(self) -> None:
        pass
