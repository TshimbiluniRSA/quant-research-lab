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


def forward_returns(close: pd.Series | Iterable[float], periods: int = 1) -> pd.Series:
    """Calculate the return from each row to ``periods`` rows in the future.

    This is a research label and must never be used as an input available to a strategy at
    that same timestamp.
    """
    if periods < 1:
        raise ValueError("periods must be at least 1")
    prices = _as_float_series(close, name="close")
    return (prices.shift(-periods) / prices - 1).rename(f"forward_return_{periods}")


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
