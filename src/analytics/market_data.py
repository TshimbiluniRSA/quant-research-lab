"""Transparent market-data transformations used by the learning notebooks."""

import re
from collections.abc import Iterable
from pathlib import Path

import numpy as np
import pandas as pd

OHLCV_COLUMNS = ("open", "high", "low", "close", "volume")
ONE_MINUTE = pd.Timedelta(minutes=1)

# A data row of the gap table in data/metadata/*_1m_gaps.md:
# | # | Split | First missing | Last missing | Minutes |
_GAP_ROW = re.compile(
    r"^\|\s*\d+\s*\|[^|]*\|\s*(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\s*\|"
    r"\s*(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\s*\|\s*(\d+)\s*\|\s*$"
)


def clean_ohlcv(
    candles: pd.DataFrame,
    *,
    timestamp_column: str = "timestamp",
    duplicate_keep: str | bool = "last",
) -> pd.DataFrame:
    """Return UTC-indexed, time-sorted OHLCV candles with duplicate timestamps removed.

    The input is copied so notebook exploration cannot silently mutate the source data.
    Timestamps may be ISO strings or integer Unix values in milliseconds.
    """
    missing = set(OHLCV_COLUMNS).difference(candles.columns)
    if missing:
        missing_names = ", ".join(sorted(missing))
        raise ValueError(f"Missing required OHLCV columns: {missing_names}")

    cleaned = candles.copy()
    if timestamp_column in cleaned.columns:
        timestamps = cleaned.pop(timestamp_column)
        numeric = pd.api.types.is_numeric_dtype(timestamps)
        cleaned.index = pd.to_datetime(
            timestamps,
            unit="ms" if numeric else None,
            utc=True,
            errors="raise",
        )
    elif not isinstance(cleaned.index, pd.DatetimeIndex):
        raise ValueError(
            f"Provide a '{timestamp_column}' column or a pandas DatetimeIndex."
        )
    else:
        cleaned.index = pd.to_datetime(cleaned.index, utc=True, errors="raise")

    cleaned.index.name = "timestamp"
    cleaned = cleaned.sort_index()
    cleaned = cleaned.loc[~cleaned.index.duplicated(keep=duplicate_keep)]
    return cleaned.loc[:, list(OHLCV_COLUMNS)]


def load_gap_windows(path: str | Path) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    """Read ``(first_missing, last_missing)`` UTC minutes from a documented 1m gap table.

    Each row's minute count must equal its inclusive window length, so a typo in the source of
    truth fails loudly instead of silently keeping or dropping the wrong minutes.
    """
    windows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        match = _GAP_ROW.match(line.strip())
        if match is None:
            continue
        first = pd.Timestamp(match.group(1), tz="UTC")
        last = pd.Timestamp(match.group(2), tz="UTC")
        expected = int(match.group(3))
        if (last - first) // ONE_MINUTE + 1 != expected:
            raise ValueError(f"Gap {first} to {last} does not span {expected} minutes.")
        windows.append((first, last))
    if not windows:
        raise ValueError(f"No gap rows found in {path}.")
    return windows


def drop_synthetic_minutes(
    candles: pd.DataFrame, gaps: Iterable[tuple[pd.Timestamp, pd.Timestamp]]
) -> pd.DataFrame:
    """Remove 1m candles whose open time falls inside a documented exchange gap.

    Jesse fills exchange outages with flat, zero-volume candles, so data loaded from Jesse has
    no missing timestamps and gap-aware functions cannot see the outage. Removing those minutes
    restores the gaps. The windows are the source of truth rather than a ``volume == 0`` test,
    because real minutes with no trades also exist. Windows are inclusive at both ends.
    """
    if not isinstance(candles.index, pd.DatetimeIndex) or candles.index.tz is None:
        raise ValueError("candles need a timezone-aware DatetimeIndex; use clean_ohlcv first")
    synthetic = np.zeros(len(candles), dtype=bool)
    for first, last in gaps:
        synthetic |= (candles.index >= first) & (candles.index <= last)
    return candles.loc[~synthetic].copy()


def resample_ohlcv(candles: pd.DataFrame, freq: str | pd.Timedelta) -> pd.DataFrame:
    """Aggregate 1m candles into ``freq`` bars, keeping only bars with every minute present.

    Bars are labelled by their open time, matching Jesse. A bar missing any minute, whether
    removed as synthetic or never recorded, is dropped rather than built from partial data:
    its range, volume, and close time would not describe a full bar. Freq-aware return
    functions then yield NaN for returns that would span it.
    """
    if not isinstance(candles.index, pd.DatetimeIndex):
        raise ValueError("candles need a DatetimeIndex; use clean_ohlcv first")
    if (candles.index != candles.index.floor(ONE_MINUTE)).any():
        raise ValueError("resample_ohlcv expects 1m candles on whole-minute timestamps")

    minutes_per_bar = pd.Timedelta(freq) // ONE_MINUTE
    grouped = candles.resample(freq, label="left", closed="left")
    bars = grouped.agg(
        {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
    )
    complete = grouped["close"].count() == minutes_per_bar
    return bars.loc[complete, list(OHLCV_COLUMNS)]


def _as_float_series(values: pd.Series | Iterable[float], *, name: str) -> pd.Series:
    series = values.copy() if isinstance(values, pd.Series) else pd.Series(values)
    return series.astype(float).rename(name)


def _shift_bars(
    prices: pd.Series, periods: int, freq: str | pd.Timedelta | None
) -> pd.Series:
    """Shift prices by ``periods`` bars, measured in time when the index holds timestamps.

    With a DatetimeIndex, ``freq`` is required: prices are reindexed to a complete ``freq`` grid
    before shifting, so a missing candle yields NaN instead of silently pairing prices that are
    further apart than one bar. Timestamps that do not fall on the grid raise an error. Without a
    DatetimeIndex, rows are assumed to be consecutive, evenly spaced bars.
    """
    if not isinstance(prices.index, pd.DatetimeIndex) or prices.empty:
        return prices.shift(periods)

    if freq is None:
        raise ValueError("freq is required for a DatetimeIndex so the horizon is measured in time")
    if not prices.index.is_monotonic_increasing or prices.index.has_duplicates:
        raise ValueError("timestamps must be sorted and unique")
    grid = pd.date_range(prices.index[0], prices.index[-1], freq=freq)
    off_grid = prices.index.difference(grid)
    if len(off_grid) > 0:
        raise ValueError(f"{len(off_grid)} timestamps do not fall on the {freq} grid")

    return prices.reindex(grid).shift(periods).reindex(prices.index)


def simple_returns(
    close: pd.Series | Iterable[float], *, freq: str | pd.Timedelta | None = None
) -> pd.Series:
    """Calculate close-to-close arithmetic returns without filling missing observations.

    With a DatetimeIndex, ``freq`` is required and a bar whose previous candle is missing gets
    NaN rather than a return spanning the gap (see ``_shift_bars``).
    """
    prices = _as_float_series(close, name="close")
    return (prices / _shift_bars(prices, 1, freq) - 1).rename("simple_return")


def log_returns(
    close: pd.Series | Iterable[float], *, freq: str | pd.Timedelta | None = None
) -> pd.Series:
    """Calculate close-to-close log returns; prices must be strictly positive.

    With a DatetimeIndex, ``freq`` is required and a bar whose previous candle is missing gets
    NaN rather than a return spanning the gap (see ``_shift_bars``).
    """
    prices = _as_float_series(close, name="close")
    if (prices.dropna() <= 0).any():
        raise ValueError("Log returns require strictly positive prices.")
    return np.log(prices / _shift_bars(prices, 1, freq)).rename("log_return")


def forward_returns(
    close: pd.Series | Iterable[float],
    periods: int = 1,
    *,
    freq: str | pd.Timedelta | None = None,
) -> pd.Series:
    """Calculate the return from each bar to ``periods`` bars in the future.

    With a DatetimeIndex, ``freq`` is required and the horizon is measured in time, so a missing
    candle yields NaN instead of silently stretching the horizon (see ``_shift_bars``).

    The grid ends at the last timestamp supplied, so slicing to one data split before calling
    this function leaves NaN wherever a label would need prices from the next split.

    This is a research label and must never be used as an input available to a strategy at
    that same timestamp.
    """
    if periods < 1:
        raise ValueError("periods must be at least 1")
    prices = _as_float_series(close, name="close")
    future = _shift_bars(prices, -periods, freq)
    return (future / prices - 1).rename(f"forward_return_{periods}")


def rolling_volatility(
    returns: pd.Series | Iterable[float],
    window: int,
    *,
    periods_per_year: int | None = None,
) -> pd.Series:
    """Calculate rolling sample volatility, optionally annualized."""
    if window < 2:
        raise ValueError("window must be at least 2")
    if periods_per_year is not None and periods_per_year < 1:
        raise ValueError("periods_per_year must be positive")

    return_series = _as_float_series(returns, name="return")
    volatility = return_series.rolling(window=window, min_periods=window).std(ddof=1)
    if periods_per_year is not None:
        volatility = volatility * np.sqrt(periods_per_year)
    return volatility.rename("rolling_volatility")
