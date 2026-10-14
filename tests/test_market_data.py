from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from analytics import (
    clean_ohlcv,
    drop_synthetic_minutes,
    forward_returns,
    load_gap_windows,
    log_returns,
    resample_ohlcv,
    rolling_volatility,
    simple_returns,
)

GAPS_FILE = Path(__file__).resolve().parents[1] / "data/metadata/binance_spot_btcusdt_1m_gaps.md"


def _window(first: str, last: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    return pd.Timestamp(first, tz="UTC"), pd.Timestamp(last, tz="UTC")


def _minute_candles(start: str, periods: int) -> pd.DataFrame:
    index = pd.date_range(start, periods=periods, freq="1min", tz="UTC", name="timestamp")
    close = 100.0 + np.arange(periods, dtype=float)
    return pd.DataFrame(
        {"open": close - 0.5, "high": close + 1, "low": close - 1, "close": close, "volume": 1.0},
        index=index,
    )


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


def test_rolling_volatility_windows_never_span_a_missing_candle() -> None:
    # The 03:00 candle is missing, so the 04:00 return is NaN and poisons every window over it.
    index = pd.to_datetime(
        [f"2023-06-01 {hour:02d}:00" for hour in (0, 1, 2, 4, 5, 6)], utc=True
    )
    close = pd.Series([100.0, 101.0, 99.0, 102.0, 104.0, 101.0], index=index)
    returns = log_returns(close, freq="1h")

    result = rolling_volatility(returns, window=2)

    assert result.iloc[2] == pytest.approx(np.std(returns.iloc[1:3], ddof=1))  # 01:00-02:00
    assert result.iloc[3:5].isna().all()  # 04:00 and 05:00 windows include the gap
    assert result.iloc[5] == pytest.approx(np.std(returns.iloc[4:6], ddof=1))  # 05:00-06:00


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


def test_load_gap_windows_reads_the_documented_binance_gaps() -> None:
    windows = load_gap_windows(GAPS_FILE)

    assert len(windows) == 25  # 22 gaps plus 3 halts published as zero-volume candles
    assert windows[0] == (
        pd.Timestamp("2019-03-12 02:00", tz="UTC"),
        pd.Timestamp("2019-03-12 07:59", tz="UTC"),
    )
    assert sum((last - first) // pd.Timedelta(minutes=1) + 1 for first, last in windows) == 4337


def test_load_gap_windows_rejects_a_row_whose_minutes_do_not_match(tmp_path: Path) -> None:
    table = tmp_path / "gaps.md"
    table.write_text("| 1 | Research | 2019-03-12 02:00 | 2019-03-12 07:59 | 359 |\n")

    with pytest.raises(ValueError, match="does not span 359 minutes"):
        load_gap_windows(table)


def test_drop_synthetic_minutes_uses_windows_not_zero_volume() -> None:
    candles = _minute_candles("2019-03-12 01:57", periods=8)  # 01:57 to 02:04
    candles.loc[pd.Timestamp("2019-03-12 01:57", tz="UTC"), "volume"] = 0.0  # real, no trades
    gaps = [_window("2019-03-12 01:59", "2019-03-12 02:01")]

    result = drop_synthetic_minutes(candles, gaps)

    kept = list(result.index.strftime("%H:%M"))
    assert kept == ["01:57", "01:58", "02:02", "02:03", "02:04"]  # both window ends removed


def test_returns_are_nan_across_a_removed_outage() -> None:
    candles = _minute_candles("2019-03-12 01:58", periods=5)  # 01:58 to 02:02
    gaps = [_window("2019-03-12 02:00", "2019-03-12 02:00")]

    returns = simple_returns(drop_synthetic_minutes(candles, gaps)["close"], freq="1min")

    assert returns.loc["2019-03-12 01:59"] == pytest.approx(101.0 / 100.0 - 1)
    assert np.isnan(returns.loc["2019-03-12 02:01"])  # previous minute was synthetic


def test_resample_ohlcv_builds_complete_bars_labelled_by_open_time() -> None:
    bars = resample_ohlcv(_minute_candles("2019-01-01 00:00", periods=120), "1h")

    assert list(bars.index.strftime("%H:%M")) == ["00:00", "01:00"]
    first = bars.iloc[0]
    assert first["open"] == 99.5  # first minute's open
    assert first["high"] == 160.0  # max of close + 1 over minutes 0-59
    assert first["low"] == 99.0
    assert first["close"] == 159.0  # last minute's close
    assert first["volume"] == 60.0


def test_resample_ohlcv_drops_hours_with_a_removed_minute_and_returns_skip_them() -> None:
    candles = _minute_candles("2019-01-01 00:00", periods=180)  # three full hours
    gaps = [_window("2019-01-01 01:30", "2019-01-01 01:30")]

    bars = resample_ohlcv(drop_synthetic_minutes(candles, gaps), "1h")
    returns = simple_returns(bars["close"], freq="1h")

    assert list(bars.index.strftime("%H:%M")) == ["00:00", "02:00"]
    assert np.isnan(returns.loc["2019-01-01 02:00"])  # would otherwise span the dropped hour


def test_resample_ohlcv_rejects_timestamps_off_the_minute() -> None:
    candles = _minute_candles("2019-01-01 00:00", periods=2)
    candles.index = candles.index + pd.Timedelta(seconds=30)

    with pytest.raises(ValueError, match="whole-minute"):
        resample_ohlcv(candles, "1h")
