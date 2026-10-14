"""Import Binance Spot 1m candles for one pair into Jesse, filling exchange outages visibly.

Jesse builds larger timeframes by counting 1m rows (every 60 rows is one 1h candle), so its
database must hold exactly one row per minute. Jesse's importer downloads 1000-minute blocks and
fills missing minutes with synthetic zero-volume candles, with two problems for research:

1. It stops when a gap longer than MAX_MISSING_EDGE_MINUTES reaches the end of a block, so
   whether an outage stops the import depends only on where block boundaries fall.
2. Missing minutes at the start of a block are filled with the open of the first real candle
   after the gap, the reopening price. A strategy would see that price before it existed.

This script raises the limit to a bounded value and fills leading gaps flat at the previous
stored close, so every outage is filled the same way: flat at the last price before it. A
trailing gap longer than the limit still stops the import, because it is more likely a bad
provider response than a real outage and must be investigated by hand.

Filled candles are not market data. Each pair's outages are listed in its own gap file,
data/metadata/binance_spot_<base><quote>_1m_gaps.md (for example binance_spot_btcusdt_1m_gaps.md);
check that list before trusting any result whose date range spans one. Declare a pair in
research/DATA_SPLITTING.md before importing it.

Run inside the Jesse container (Postgres and Redis hostnames resolve only there):

    make import-candles START=2019-01-01                  # BTC-USDT
    make import-candles START=2019-01-01 SYMBOL=ETH-USDT

Blocks already in the database are skipped, so re-running after an interruption is cheap.
"""

import argparse
import re
import uuid
from collections.abc import Callable
from typing import Any

EXCHANGE = "Binance Spot"
DEFAULT_SYMBOL = "BTC-USDT"
MINUTE_MS = 60_000
_SYMBOL = re.compile(r"^[A-Z0-9]+-[A-Z0-9]+$")

# Longest Binance Spot BTC-USDT 1m outage found when scanning 2019-01-01 to 2026-09-29
# (2019-05-15, 600 minutes). See data/metadata/binance_spot_btcusdt_1m_gaps.md. Binance outages
# are exchange-wide: on 2026-10-14 all 25 BTC-USDT windows were found at the same minutes in
# ETH, BNB, XRP, ADA and LTC (XRP and LTC reopened one minute earlier after gap 19). A
# pair-specific gap longer than this, such as a delisting, still stops the import.
MAX_FILLED_OUTAGE_MINUTES = 600

Candle = dict[str, Any]


def parse_symbol(value: str) -> str:
    """Return a Jesse symbol such as ``ETH-USDT``, rejecting Binance's ``ETHUSDT`` form."""
    if not _SYMBOL.match(value):
        raise argparse.ArgumentTypeError(
            f"{value!r} is not a Jesse symbol; use BASE-QUOTE in capitals, e.g. ETH-USDT"
        )
    return value


def gap_file_name(symbol: str) -> str:
    """Return the gap file name for a Binance Spot pair, e.g. binance_spot_ethusdt_1m_gaps.md."""
    return f"binance_spot_{symbol.replace('-', '').lower()}_1m_gaps.md"


def leading_fill(
    candles: list[Candle], start_timestamp: int, previous_close: float
) -> list[Candle]:
    """Return flat, zero-volume candles at ``previous_close`` for each minute from
    ``start_timestamp`` up to the first real candle in ``candles``."""
    first_real = min(int(c["timestamp"]) for c in candles)
    template = candles[0]
    return [
        {
            "id": str(uuid.uuid4()),
            "exchange": template["exchange"],
            "symbol": template["symbol"],
            "timeframe": "1m",
            "timestamp": timestamp,
            "open": previous_close,
            "high": previous_close,
            "low": previous_close,
            "close": previous_close,
            "volume": 0,
        }
        for timestamp in range(start_timestamp, first_real, MINUTE_MS)
    ]


def _fill_from_previous_close(original: Callable[..., list[Candle]]) -> Callable[..., list[Candle]]:
    from jesse.models.Candle import Candle as CandleModel

    def fill(candles: list[Candle], start_timestamp: int, end_timestamp: int) -> list[Candle]:
        if candles and min(int(c["timestamp"]) for c in candles) > start_timestamp:
            previous = (
                CandleModel.select(CandleModel.timestamp, CandleModel.close)
                .where(
                    CandleModel.exchange == candles[0]["exchange"],
                    CandleModel.symbol == candles[0]["symbol"],
                    CandleModel.timeframe == "1m",
                    CandleModel.timestamp == start_timestamp - MINUTE_MS,
                )
                .first()
            )
            # Without the immediately preceding minute there is no honest price to carry
            # forward; Jesse's own behaviour applies and the gap list must flag it.
            if previous is not None:
                candles = leading_fill(candles, start_timestamp, previous.close) + candles
        return original(candles, start_timestamp, end_timestamp)

    return fill


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--start", required=True, help="first UTC date to import, YYYY-MM-DD")
    parser.add_argument(
        "--symbol", type=parse_symbol, default=DEFAULT_SYMBOL, help="Jesse symbol, e.g. ETH-USDT"
    )
    args = parser.parse_args()

    # Jesse connects to Postgres and Redis on import, so it is imported only when running.
    import jesse.modes.import_candles_mode as import_mode
    from jesse.research import import_candles

    # run() looks both names up as module globals at call time.
    import_mode.MAX_MISSING_EDGE_MINUTES = MAX_FILLED_OUTAGE_MINUTES
    import_mode._fill_absent_candles = _fill_from_previous_close(import_mode._fill_absent_candles)
    print(import_candles(EXCHANGE, args.symbol, args.start, show_progressbar=True))
    print(f"Document this pair's outages in data/metadata/{gap_file_name(args.symbol)}.")


if __name__ == "__main__":
    main()
