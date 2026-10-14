import importlib.util
import re
import sys
import threading
from pathlib import Path

import pandas as pd
import pytest

from analytics import load_gap_windows

ROOT = Path(__file__).resolve().parents[1]
# scan_gaps imports helpers from import_candles, as it does when run from scripts/.
sys.path.insert(0, str(ROOT / "scripts"))
_spec = importlib.util.spec_from_file_location("scan_gaps", ROOT / "scripts" / "scan_gaps.py")
assert _spec is not None and _spec.loader is not None
scan_gaps = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(scan_gaps)

MINUTE = 60_000


def _ms(text: str) -> int:
    return int(pd.Timestamp(text, tz="UTC").value // 1_000_000)


def _kline(timestamp: int, *, flat: bool = False) -> list:
    """A raw Binance kline: [open time, open, high, low, close, volume, ...] as strings."""
    if flat:
        return [timestamp, "100.0", "100.0", "100.0", "100.0", "0.0", timestamp + MINUTE - 1]
    return [timestamp, "100.0", "101.0", "99.0", "100.5", "3.2", timestamp + MINUTE - 1]


def _minutes(start: str, count: int, *, flat: bool = False) -> list:
    first = _ms(start)
    return [_kline(first + i * MINUTE, flat=flat) for i in range(count)]


def _scan(klines: list) -> object:
    return scan_gaps.scan(scan_gaps.to_minute(k) for k in klines)


def test_to_minute_keeps_only_the_timestamp_and_flat_flag() -> None:
    assert scan_gaps.to_minute(_kline(1_000, flat=True)) == (1_000, True)
    assert scan_gaps.to_minute(_kline(1_000)) == (1_000, False)


def test_scan_finds_missing_minutes_between_candles() -> None:
    klines = _minutes("2019-03-12 01:58", 2) + _minutes("2019-03-12 08:00", 2)

    result = _scan(klines)

    assert result.gaps == [(_ms("2019-03-12 02:00"), _ms("2019-03-12 07:59"))]


def test_scan_does_not_treat_the_time_before_listing_as_a_gap() -> None:
    result = _scan(_minutes("2020-08-11 06:00", 3))

    assert result.gaps == []
    assert result.first == _ms("2020-08-11 06:00")


def test_halt_is_a_flat_run_ending_where_a_gap_begins() -> None:
    klines = (
        _minutes("2019-06-07 19:59", 2)
        + _minutes("2019-06-07 20:01", 3, flat=True)  # halt: 20:01-20:03
        + _minutes("2019-06-07 21:00", 1)  # gap: 20:04-20:59
        + _minutes("2019-06-07 21:01", 2, flat=True)  # quiet minutes, then trading resumes
        + _minutes("2019-06-07 21:03", 1)
    )

    result = _scan(klines)

    assert result.halts() == [(_ms("2019-06-07 20:01"), _ms("2019-06-07 20:03"))]
    assert len(result.research_flat_runs) == 2  # the quiet run is found but is not a halt


def test_flat_minutes_outside_research_are_only_counted() -> None:
    klines = _minutes("2025-03-01 00:00", 1) + _minutes("2025-03-01 00:01", 4, flat=True)

    result = _scan(klines)

    assert result.research_flat_runs == []
    assert result.flat_counts_outside_research == {"Final test": 4}


def test_a_flat_run_stops_at_a_split_boundary() -> None:
    result = _scan(_minutes("2023-12-31 23:58", 4, flat=True))

    assert result.research_flat_runs == [(_ms("2023-12-31 23:58"), _ms("2023-12-31 23:59"))]
    assert result.flat_counts_outside_research == {"Validation": 2}


def test_page_windows_cover_the_range_without_overlap() -> None:
    windows = scan_gaps.page_windows(_ms("2019-01-01 00:00"), _ms("2019-01-01 00:05"), 2)

    assert windows == [
        (_ms("2019-01-01 00:00"), _ms("2019-01-01 00:01")),
        (_ms("2019-01-01 00:02"), _ms("2019-01-01 00:03")),
        (_ms("2019-01-01 00:04"), _ms("2019-01-01 00:04")),
    ]


def test_iter_minutes_yields_in_time_order_when_pages_finish_out_of_order() -> None:
    klines = _minutes("2019-01-01 00:00", 3) + _minutes("2019-01-01 00:07", 3)
    started = threading.Event()

    def fetch(start: int, end: int) -> list:
        if start == _ms("2019-01-01 00:00"):
            started.wait(timeout=5)  # the first page finishes last
        else:
            started.set()
        return [k for k in klines if start <= k[0] <= end]

    minutes = scan_gaps.iter_minutes(
        fetch, _ms("2019-01-01 00:00"), _ms("2019-01-01 00:10"), workers=4, page_minutes=2
    )

    assert [m[0] for m in minutes] == [k[0] for k in klines]


def test_an_empty_page_inside_the_range_is_a_gap_not_the_end() -> None:
    klines = _minutes("2019-01-01 00:00", 2) + _minutes("2019-01-01 00:06", 2)

    def fetch(start: int, end: int) -> list:
        return [k for k in klines if start <= k[0] <= end]

    minutes = scan_gaps.iter_minutes(
        fetch, _ms("2019-01-01 00:00"), _ms("2019-01-01 00:08"), workers=2, page_minutes=2
    )
    result = scan_gaps.scan(minutes)

    assert result.gaps == [(_ms("2019-01-01 00:02"), _ms("2019-01-01 00:05"))]


def test_network_errors_are_retried_with_growing_waits() -> None:
    klines = _minutes("2019-01-01 00:00", 2)
    failures = [TimeoutError("timed out"), ConnectionResetError("reset")]
    waits: list[float] = []

    def fetch(start: int, end: int) -> list:
        if failures:
            raise failures.pop(0)
        return [k for k in klines if start <= k[0] <= end]

    minutes = list(
        scan_gaps.iter_minutes(  # one page, so both failures hit the same request
            fetch, _ms("2019-01-01 00:00"), _ms("2019-01-01 00:10"), sleep=waits.append
        )
    )

    assert [m[0] for m in minutes] == [k[0] for k in klines]
    assert waits == [2, 4]


def test_the_scan_stops_after_five_network_failures_and_names_the_minute() -> None:
    waits: list[float] = []

    def fetch(start: int, end: int) -> list:
        raise TimeoutError("timed out")

    with pytest.raises(RuntimeError, match="5 times fetching from 2019-10-06 19:41"):
        list(
            scan_gaps.iter_minutes(
                fetch, _ms("2019-10-06 19:41"), _ms("2019-10-07"), sleep=waits.append
            )
        )
    assert waits == [2, 4, 8, 16]


def test_rate_limits_are_waited_out_without_using_up_attempts() -> None:
    limits = [scan_gaps.RateLimited(7)] * 6
    waits: list[float] = []

    def fetch(start: int, end: int) -> list:
        if limits:
            raise limits.pop(0)
        return []

    assert scan_gaps.fetch_with_retries(fetch, 0, MINUTE, sleep=waits.append) == []
    assert waits == [7] * 6


def test_other_errors_are_not_retried() -> None:
    waits: list[float] = []

    def fetch(start: int, end: int) -> list:
        raise RuntimeError("Binance answered 400: invalid symbol")

    with pytest.raises(RuntimeError, match="400"):
        scan_gaps.fetch_with_retries(fetch, 0, MINUTE, sleep=waits.append)
    assert waits == []


def test_rendered_file_reads_back_with_load_gap_windows(tmp_path: Path) -> None:
    klines = (
        _minutes("2019-06-07 19:59", 2)
        + _minutes("2019-06-07 20:01", 3, flat=True)
        + _minutes("2019-06-07 21:00", 1)
    )
    result = _scan(klines)
    path = tmp_path / "gaps.md"

    path.write_text(
        scan_gaps.render("ETH-USDT", result, _ms("2019-01-01"), _ms("2019-06-08"), "2026-10-14")
    )

    windows = load_gap_windows(path, symbol="ETH-USDT")
    assert windows == [
        (pd.Timestamp("2019-06-07 20:04", tz="UTC"), pd.Timestamp("2019-06-07 20:59", tz="UTC")),
        (pd.Timestamp("2019-06-07 20:01", tz="UTC"), pd.Timestamp("2019-06-07 20:03", tz="UTC")),
    ]


def test_render_flags_gaps_longer_than_the_import_limit() -> None:
    klines = _minutes("2022-05-12 16:38", 2) + _minutes("2022-05-31 06:00", 1)

    text = scan_gaps.render(
        "LUNA-USDT", _scan(klines), _ms("2022-05-01"), _ms("2022-06-01"), "2026-10-14"
    )

    assert "stop `scripts/import_candles.py`: 1." in text
    assert "| 1 | Research | 2022-05-12 16:40 | 2022-05-31 05:59 | 26720 |" in text


def test_render_refuses_an_empty_scan() -> None:
    with pytest.raises(ValueError, match="no XYZ-USDT candles"):
        scan_gaps.render("XYZ-USDT", scan_gaps.scan([]), 0, MINUTE, "2026-10-14")


def test_split_boundaries_match_data_splitting_md() -> None:
    text = (ROOT / "research/DATA_SPLITTING.md").read_text(encoding="utf-8")
    current = text.split("## Crypto boundaries (v3)")[1].split("\n## ")[0]
    rows = re.findall(r"^\| (Research/training|Validation|Final test|Reserved) \| ([\d-]+) 00:00 \|"
                      r" ([\d-]+ 00:00|open) \|", current, re.M)
    documented = [(start, end.removesuffix(" 00:00")) for _, start, end in rows]

    in_script = [
        (scan_gaps._fmt(start)[:10], "open" if end is None else scan_gaps._fmt(end)[:10])
        for _, start, end in scan_gaps.SPLITS
    ]
    assert documented == in_script
