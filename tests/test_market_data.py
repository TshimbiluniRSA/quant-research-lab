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


def test_backward_returns_are_nan_after_a_missing_candle() -> None:
    # The 02:00 candle is missing, so 03:00 has no one-bar-earlier price.
    index = pd.to_datetime(
        ["2023-06-01 00:00", "2023-06-01 01:00", "2023-06-01 03:00", "2023-06-01 04:00"], utc=True
    )
    close = pd.Series([100.0, 110.0, 121.0, 133.1], index=index)

    simple = simple_returns(close, freq="1h")
    log = log_returns(close, freq="1h")

    assert simple.iloc[1] == pytest.approx(0.1)
    assert np.isnan(simple.iloc[2])  # not 01:00 -> 03:00
    assert simple.iloc[3] == pytest.approx(0.1)
    assert log.iloc[1] == pytest.approx(np.log(1.1))
    assert np.isnan(log.iloc[2])
    assert log.iloc[3] == pytest.approx(np.log(1.1))


def test_backward_returns_require_freq_for_timestamped_prices() -> None:
    close = pd.Series([1.0, 2.0], index=pd.date_range("2023-01-01", periods=2, freq="1h"))

    with pytest.raises(ValueError, match="freq is required"):
        simple_returns(close)
    with pytest.raises(ValueError, match="freq is required"):
        log_returns(close)


def test_forward_returns_align_the_future_result_to_the_current_row() -> None:
    result = forward_returns(pd.Series([100.0, 110.0, 121.0]), periods=2)

    assert result.iloc[0] == pytest.approx(0.21)
    assert result.iloc[1:].isna().all()


def test_forward_returns_measure_the_horizon_in_time_across_a_missing_candle() -> None:
    # The 02:00 candle is missing.
    index = pd.to_datetime(
        ["2023-06-01 00:00", "2023-06-01 01:00", "2023-06-01 03:00", "2023-06-01 04:00"], utc=True
    )
    close = pd.Series([100.0, 110.0, 121.0, 133.1], index=index)

    one_hour = forward_returns(close, periods=1, freq="1h")
    two_hours = forward_returns(close, periods=2, freq="1h")

    assert one_hour.iloc[0] == pytest.approx(0.1)
    assert np.isnan(one_hour.iloc[1])  # 01:00 -> 02:00 has no price
    assert np.isnan(two_hours.iloc[0])  # 00:00 -> 02:00 has no price
    assert two_hours.iloc[1] == pytest.approx(0.1)  # 01:00 -> 03:00, not 01:00 -> 04:00


def test_forward_returns_on_a_sliced_split_do_not_use_the_next_split() -> None:
    index = pd.date_range("2023-12-31 21:00", "2024-01-01 01:00", freq="1h", tz="UTC")
    close = pd.Series([100.0, 101.0, 102.0, 999.0, 999.0], index=index)
    research = close.loc[close.index < pd.Timestamp("2024-01-01", tz="UTC")]

    result = forward_returns(research, periods=2, freq="1h")

    assert result.iloc[0] == pytest.approx(0.02)  # 21:00 -> 23:00, both research
    assert result.iloc[1:].isna().all()  # 22:00 and 23:00 would need validation prices


def test_forward_returns_require_freq_for_timestamped_prices() -> None:
    close = pd.Series([1.0, 2.0], index=pd.date_range("2023-01-01", periods=2, freq="1h"))

    with pytest.raises(ValueError, match="freq is required"):
        forward_returns(close)


def test_forward_returns_reject_timestamps_off_the_grid() -> None:
    index = pd.to_datetime(["2023-01-01 00:00", "2023-01-01 00:30", "2023-01-01 01:00"])
    close = pd.Series([1.0, 2.0, 3.0], index=index)

    with pytest.raises(ValueError, match="do not fall on the 1h grid"):
        forward_returns(close, freq="1h")


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
