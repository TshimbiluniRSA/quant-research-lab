import numpy as np
import pandas as pd
import pytest

from analytics import clean_ohlcv, forward_returns, log_returns, rolling_volatility, simple_returns


def test_simple_returns_do_not_fill_missing_values() -> None:
    close = pd.Series([100.0, 110.0, np.nan, 121.0])

    result = simple_returns(close)

    assert np.isnan(result.iloc[0])
    assert result.iloc[1] == pytest.approx(0.1)
    assert result.iloc[2:].isna().all()


def test_log_returns_match_price_ratio() -> None:
    result = log_returns(pd.Series([100.0, 110.0]))

    assert result.iloc[1] == pytest.approx(np.log(1.1))


def test_log_returns_reject_non_positive_prices() -> None:
    with pytest.raises(ValueError, match="strictly positive"):
        log_returns(pd.Series([100.0, 0.0]))


def test_forward_returns_align_the_future_result_to_the_current_row() -> None:
    result = forward_returns(pd.Series([100.0, 110.0, 121.0]), periods=2)

    assert result.iloc[0] == pytest.approx(0.21)
    assert result.iloc[1:].isna().all()


def test_rolling_volatility_uses_complete_windows() -> None:
    returns = pd.Series([0.01, -0.01, 0.02])

    result = rolling_volatility(returns, window=2)

    assert np.isnan(result.iloc[0])
    assert result.iloc[1] == pytest.approx(np.std([0.01, -0.01], ddof=1))


def test_clean_ohlcv_sorts_and_keeps_last_duplicate() -> None:
    candles = pd.DataFrame(
        {
            "timestamp": [1_700_000_060_000, 1_700_000_000_000, 1_700_000_000_000],
            "open": [2.0, 1.0, 10.0],
            "high": [2.2, 1.2, 10.2],
            "low": [1.8, 0.8, 9.8],
            "close": [2.1, 1.1, 10.1],
            "volume": [20.0, 10.0, 100.0],
        }
    )

    result = clean_ohlcv(candles)

    assert result.index.is_monotonic_increasing
    assert result.index.tz is not None
    assert not result.index.has_duplicates
    assert result.iloc[0]["open"] == 10.0


def test_clean_ohlcv_requires_all_price_and_volume_columns() -> None:
    with pytest.raises(ValueError, match="volume"):
        clean_ohlcv(pd.DataFrame({"timestamp": [1], "open": [1]}))
