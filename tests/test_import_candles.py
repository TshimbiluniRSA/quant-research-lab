import argparse
import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "import_candles.py"
_spec = importlib.util.spec_from_file_location("import_candles_script", SCRIPT)
assert _spec is not None and _spec.loader is not None
import_candles_script = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(import_candles_script)

START = 1_552_356_000_000  # 2019-03-12 02:00 UTC
MINUTE = 60_000


def _real_candle(
    timestamp: int, open_price: float, symbol: str = "BTC-USDT"
) -> dict[str, object]:
    return {
        "id": "real",
        "exchange": "Binance Spot",
        "symbol": symbol,
        "timeframe": "1m",
        "timestamp": timestamp,
        "open": open_price,
        "close": open_price + 1,
        "high": open_price + 2,
        "low": open_price - 1,
        "volume": 5.0,
    }


def test_leading_fill_carries_the_previous_close_not_the_reopening_price() -> None:
    reopening = _real_candle(START + 3 * MINUTE, open_price=4000.0)

    filled = import_candles_script.leading_fill([reopening], START, previous_close=3900.0)

    assert [c["timestamp"] for c in filled] == [START, START + MINUTE, START + 2 * MINUTE]
    for candle in filled:
        assert candle["open"] == candle["high"] == candle["low"] == candle["close"] == 3900.0
        assert candle["volume"] == 0
        assert candle["exchange"] == "Binance Spot"
        assert candle["symbol"] == "BTC-USDT"


def test_leading_fill_is_empty_when_the_block_starts_with_a_real_candle() -> None:
    assert import_candles_script.leading_fill([_real_candle(START, 4000.0)], START, 3900.0) == []


def test_leading_fill_keeps_the_symbol_of_the_block_it_fills() -> None:
    reopening = _real_candle(START + MINUTE, open_price=150.0, symbol="ETH-USDT")

    filled = import_candles_script.leading_fill([reopening], START, previous_close=140.0)

    assert [c["symbol"] for c in filled] == ["ETH-USDT"]


def test_parse_symbol_accepts_jesse_form_and_rejects_binance_form() -> None:
    assert import_candles_script.parse_symbol("ETH-USDT") == "ETH-USDT"
    for bad in ("ETHUSDT", "eth-usdt", "ETH/USDT", ""):
        with pytest.raises(argparse.ArgumentTypeError):
            import_candles_script.parse_symbol(bad)


def test_script_and_notebooks_agree_on_gap_file_names() -> None:
    from analytics import gap_file_path

    for symbol in ("BTC-USDT", "ETH-USDT", "1000SATS-USDT"):
        assert import_candles_script.gap_file_name(symbol) == gap_file_path(symbol).name
