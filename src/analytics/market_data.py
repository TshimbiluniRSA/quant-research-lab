"""Transparent market-data transformations used by the learning notebooks."""

from collections.abc import Iterable

import numpy as np
import pandas as pd

OHLCV_COLUMNS = ("open", "high", "low", "close", "volume")


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


def _as_float_series(values: pd.Series | Iterable[float], *, name: str) -> pd.Series:
    series = values.copy() if isinstance(values, pd.Series) else pd.Series(values)
    return series.astype(float).rename(name)


def simple_returns(close: pd.Series | Iterable[float]) -> pd.Series:
    """Calculate close-to-close arithmetic returns without filling missing observations."""
    prices = _as_float_series(close, name="close")
    return prices.pct_change(fill_method=None).rename("simple_return")


def log_returns(close: pd.Series | Iterable[float]) -> pd.Series:
    """Calculate close-to-close log returns; prices must be strictly positive."""
    prices = _as_float_series(close, name="close")
    if (prices.dropna() <= 0).any():
        raise ValueError("Log returns require strictly positive prices.")
    return np.log(prices / prices.shift(1)).rename("log_return")


def forward_returns(
    close: pd.Series | Iterable[float],
    periods: int = 1,
    *,
    freq: str | pd.Timedelta | None = None,
) -> pd.Series:
    """Calculate the return from each bar to ``periods`` bars in the future.

    With a DatetimeIndex, ``freq`` is required and the horizon is measured in time: prices are
    reindexed to a complete ``freq`` grid, so a missing candle yields NaN instead of silently
    stretching the horizon. Timestamps that do not fall on the grid raise an error. Without a
    DatetimeIndex, rows are assumed to be consecutive, evenly spaced bars.

    The grid ends at the last timestamp supplied, so slicing to one data split before calling
    this function leaves NaN wherever a label would need prices from the next split.

    This is a research label and must never be used as an input available to a strategy at
    that same timestamp.
    """
    if periods < 1:
        raise ValueError("periods must be at least 1")
    prices = _as_float_series(close, name="close")
    name = f"forward_return_{periods}"

    if not isinstance(prices.index, pd.DatetimeIndex) or prices.empty:
        return (prices.shift(-periods) / prices - 1).rename(name)

    if freq is None:
        raise ValueError("freq is required for a DatetimeIndex so the horizon is measured in time")
    if not prices.index.is_monotonic_increasing or prices.index.has_duplicates:
        raise ValueError("timestamps must be sorted and unique")
    grid = pd.date_range(prices.index[0], prices.index[-1], freq=freq)
    off_grid = prices.index.difference(grid)
    if len(off_grid) > 0:
        raise ValueError(f"{len(off_grid)} timestamps do not fall on the {freq} grid")

    future = prices.reindex(grid).shift(-periods).reindex(prices.index)
    return (future / prices - 1).rename(name)


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
