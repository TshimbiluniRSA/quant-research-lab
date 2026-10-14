"""Scan Binance Spot 1m klines for one pair and print its gap file.

A gap is a run of minutes for which Binance's public klines API returns no candle. A halt is a
run of flat (open = high = low = close), zero-volume candles that ends exactly where a gap
begins: Binance stopped trading but kept publishing empty candles. Both go into the pair's gap
file, which scripts/import_candles.py, analytics.load_gap_windows and the notebooks rely on.

What the scan reads, and why it is not final-test access:

- Each kline is reduced to its open timestamp and one flag (flat with zero volume) as soon as
  it arrives. Prices and volumes are discarded and never printed or stored.
- Gaps are reported in every split; they are a data-coverage fact, like BTC-USDT's list.
- Halts are reported only in the research split. Elsewhere only the count of flat zero-volume
  minutes per split is printed, as was done for BTC-USDT.

Runs on the host; it needs internet access but not Jesse:

    .venv/bin/python scripts/scan_gaps.py --symbol ETH-USDT          # print to the terminal
    .venv/bin/python scripts/scan_gaps.py --symbol ETH-USDT --write  # save the gap file

Declare the pair in research/DATA_SPLITTING.md before scanning it. Read the output before
saving it: an unexpected gap (a listing break, a reused symbol) is a research decision.
"""

import argparse
import http.client
import json
import sys
import threading
import time
from collections.abc import Callable, Iterable, Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from import_candles import MAX_FILLED_OUTAGE_MINUTES, gap_file_name, parse_symbol

BINANCE_HOST = "api.binance.com"
MINUTE_MS = 60_000
# A dropped or stalled connection is retried after 2, 4, 8 and 16 seconds, then the scan stops.
NETWORK_ATTEMPTS = 5
NETWORK_ERRORS = (OSError, http.client.HTTPException)  # OSError includes timeouts
# Each page is a fixed 1000-minute window, Binance's maximum per request. Fixed windows do not
# depend on each other, so WORKERS of them are fetched at once. A klines request costs 2 of
# Binance's 6000 weight per minute; 8 workers at about 1.6 s per page use roughly 600.
PAGE_MINUTES = 1000
WORKERS = 8
METADATA_DIR = Path(__file__).resolve().parents[1] / "data" / "metadata"
RESEARCH = "Research"


def _ms(day: str) -> int:
    return int(datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=UTC).timestamp() * 1000)


# Split definition v3 in research/DATA_SPLITTING.md: half-open UTC intervals [start, end).
# tests/test_scan_gaps.py checks these against the document's table.
SPLITS: tuple[tuple[str, int, int | None], ...] = (
    (RESEARCH, _ms("2019-01-01"), _ms("2024-01-01")),
    ("Validation", _ms("2024-01-01"), _ms("2025-01-01")),
    ("Final test", _ms("2025-01-01"), _ms("2026-07-01")),
    ("Reserved", _ms("2026-07-01"), None),
)

# (open timestamp in ms, True if the candle is flat with zero volume)
Minute = tuple[int, bool]
Window = tuple[int, int]


def split_of(timestamp: int) -> str:
    """Return the split containing ``timestamp``, judged by the candle's open time."""
    for name, start, end in SPLITS:
        if start <= timestamp and (end is None or timestamp < end):
            return name
    return "Before research"


def to_minute(kline: list) -> Minute:
    """Reduce a Binance kline to its open time and flat-zero-volume flag; drop the prices."""
    open_, high, low, close, volume = kline[1:6]
    return int(kline[0]), float(volume) == 0 and open_ == high == low == close


@dataclass
class Scan:
    first: int | None = None
    last: int | None = None
    gaps: list[Window] = field(default_factory=list)
    research_flat_runs: list[Window] = field(default_factory=list)
    flat_counts_outside_research: dict[str, int] = field(default_factory=dict)

    def halts(self) -> list[Window]:
        """Research flat runs that end exactly where a gap begins."""
        gap_starts = {first for first, _ in self.gaps}
        return [run for run in self.research_flat_runs if run[1] + MINUTE_MS in gap_starts]


def scan(minutes: Iterable[Minute]) -> Scan:
    """Find gaps and flat zero-volume runs in time-ordered minutes.

    Minutes before the first candle are not a gap: the pair was not listed yet. A flat run is
    broken by a traded minute, a gap, or a split boundary.
    """
    result = Scan()
    run: list[int] | None = None
    for timestamp, flat in minutes:
        if result.last is not None and timestamp - result.last > MINUTE_MS:
            result.gaps.append((result.last + MINUTE_MS, timestamp - MINUTE_MS))
        contiguous = result.last is not None and timestamp - result.last == MINUTE_MS
        same_split = result.last is not None and split_of(result.last) == split_of(timestamp)
        if run is not None and not (flat and contiguous and same_split):
            result.research_flat_runs.append((run[0], run[1]))
            run = None
        if flat:
            where = split_of(timestamp)
            if where == RESEARCH:
                run = [timestamp, timestamp] if run is None else [run[0], timestamp]
            else:
                counts = result.flat_counts_outside_research
                counts[where] = counts.get(where, 0) + 1
        if result.first is None:
            result.first = timestamp
        result.last = timestamp
    if run is not None:
        result.research_flat_runs.append((run[0], run[1]))
    return result


Fetch = Callable[[int, int], list[list]]


class RateLimited(Exception):
    """Binance answered 418 or 429 and asked the client to wait ``retry_after`` seconds."""

    def __init__(self, retry_after: int) -> None:
        super().__init__(f"rate limited; retry after {retry_after} s")
        self.retry_after = retry_after


def binance_fetch(symbol: str) -> Fetch:
    """Return a function fetching up to 1000 raw klines from ``start`` to ``end`` (ms).

    Each worker thread keeps one HTTPS connection open and reuses it; connections are not
    shared between threads. After a network error the connection is closed and the next
    request reopens it.
    """
    pair = symbol.replace("-", "")
    local = threading.local()

    def fetch(start: int, end: int) -> list[list]:
        if not hasattr(local, "connection"):
            local.connection = http.client.HTTPSConnection(BINANCE_HOST, timeout=30)
        connection = local.connection
        path = (
            f"/api/v3/klines?symbol={pair}&interval=1m"
            f"&startTime={start}&endTime={end}&limit=1000"
        )
        try:
            connection.request("GET", path)
            response = connection.getresponse()
            body = response.read()
        except NETWORK_ERRORS:
            connection.close()
            raise
        if response.status in (418, 429):
            raise RateLimited(int(response.getheader("Retry-After", "60")))
        if response.status != 200:
            raise RuntimeError(f"Binance answered {response.status}: {body[:200]!r}")
        return json.loads(body)

    return fetch


def fetch_with_retries(
    fetch: Fetch, start: int, end: int, sleep: Callable[[float], None] = time.sleep
) -> list[list]:
    """Call ``fetch``, waiting out rate limits and retrying network errors with backoff.

    Rate-limit waits do not use up attempts: Binance asks clients to back off, and ignoring
    it gets the IP banned. Any other error, such as an unknown symbol, is not retried.
    """
    attempt = 0
    while True:
        try:
            return fetch(start, end)
        except RateLimited as limited:
            sleep(limited.retry_after)
        except NETWORK_ERRORS as error:
            attempt += 1
            if attempt == NETWORK_ATTEMPTS:
                raise RuntimeError(
                    f"Network failed {NETWORK_ATTEMPTS} times fetching from {_fmt(start)}; "
                    f"nothing was saved. Rerun the scan. Last error: {error!r}"
                ) from error
            print(
                f"  network error at {_fmt(start)} ({error!r}); retry {attempt} of "
                f"{NETWORK_ATTEMPTS - 1} in {2**attempt} s",
                file=sys.stderr,
            )
            sleep(2**attempt)


def page_windows(start: int, end: int, page_minutes: int = PAGE_MINUTES) -> list[Window]:
    """Split ``[start, end)`` into inclusive ``(first, last)`` minute windows of at most
    ``page_minutes``, so a page can never hold more candles than one request returns."""
    step = page_minutes * MINUTE_MS
    return [(first, min(first + step, end) - MINUTE_MS) for first in range(start, end, step)]


def iter_minutes(
    fetch: Fetch,
    start: int,
    end: int,
    sleep: Callable[[float], None] = time.sleep,
    *,
    workers: int = WORKERS,
    page_minutes: int = PAGE_MINUTES,
) -> Iterator[Minute]:
    """Yield minutes from ``start`` up to, but excluding, ``end``, in time order.

    Pages are fetched ``workers`` at a time but yielded in order, so ``scan`` sees the same
    sequence as a one-page-at-a-time scan. If a page fails for good, pages not yet started are
    cancelled and the error is raised.
    """
    windows = page_windows(start, end, page_minutes)
    pool = ThreadPoolExecutor(max_workers=workers)
    try:
        pages = pool.map(lambda w: fetch_with_retries(fetch, w[0], w[1], sleep), windows)
        for number, page in enumerate(pages, start=1):
            for kline in page:
                yield to_minute(kline)
            if number % 200 == 0:
                print(f"  scanned to {_fmt(windows[number - 1][1])}", file=sys.stderr)
    finally:
        pool.shutdown(cancel_futures=True)


def _fmt(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp / 1000, UTC).strftime("%Y-%m-%d %H:%M")


def _minutes(window: Window) -> int:
    return (window[1] - window[0]) // MINUTE_MS + 1


def _split_label(window: Window) -> str:
    first, last = split_of(window[0]), split_of(window[1])
    return first if first == last else f"{first} / {last}"


def _rows(windows: list[Window], start_number: int) -> list[str]:
    return [
        f"| {number} | {_split_label(w)} | {_fmt(w[0])} | {_fmt(w[1])} | {_minutes(w)} |"
        for number, w in enumerate(windows, start=start_number)
    ]


def render(symbol: str, result: Scan, start: int, end: int, scanned_on: str) -> str:
    """Return the gap file in the format analytics.load_gap_windows reads."""
    if result.first is None or result.last is None:
        raise ValueError(
            f"Binance returned no {symbol} candles between {_fmt(start)} and {_fmt(end)}"
        )
    gaps, halts = result.gaps, result.halts()
    unlisted = [run for run in result.research_flat_runs if run not in halts]
    limit = MAX_FILLED_OUTAGE_MINUTES
    long_gaps = [n for n, gap in enumerate(gaps, start=1) if _minutes(gap) > limit]
    counts = result.flat_counts_outside_research
    outside = ", ".join(f"{name} {counts.get(name, 0)}" for name, _, _ in SPLITS[1:])
    ended = result.last < end - MINUTE_MS

    lines = [
        f"# Binance Spot {symbol} 1m gaps",
        "",
        "Minutes for which Binance's public klines API (`/api/v3/klines`, interval `1m`) returns",
        "no candle, and halts where Binance published flat zero-volume candles before a gap.",
        "`scripts/import_candles.py` fills each missing minute with a synthetic, zero-volume",
        "candle flat at the last real close. **Filled candles are not market data.** Notebooks",
        "remove every minute in both tables (`analytics.load_gap_windows`).",
        "",
        "## How this list was produced",
        "",
        f"- Generated by `scripts/scan_gaps.py` on {scanned_on}, covering {_fmt(start)} up to",
        f"  {_fmt(end)} UTC (exclusive).",
        f"- First candle returned: {_fmt(result.first)}. Last candle returned: {_fmt(result.last)}"
        + (" (**the pair stopped trading before the scan end**)." if ended else "."),
        "- Each kline was reduced to its open timestamp and a flat-zero-volume flag on arrival;",
        "  prices and volumes were discarded. Halts are reported only in the research split.",
        "  This is a data-coverage check, not final-test access.",
        "- Times are UTC. \"First missing\" and \"last missing\" are inclusive open times.",
        "",
        "## Gaps",
        "",
        "| # | Split | First missing | Last missing | Minutes |",
        "| ---: | --- | --- | --- | ---: |",
        *_rows(gaps, 1),
        "",
        f"Totals: {len(gaps)} gaps, {sum(map(_minutes, gaps)):,} minutes.",
    ]
    if long_gaps:
        lines += [
            "",
            f"Gaps longer than the import limit ({limit} minutes), which stop "
            f"`scripts/import_candles.py`: {', '.join(map(str, long_gaps))}.",
            "Investigate them before importing.",
        ]
    lines += [
        "",
        "## Halts published as zero-volume candles",
        "",
        "Research-split runs of flat, zero-volume candles that end exactly where a gap begins.",
        "Row numbers continue from the gap table.",
        "",
        "| # | Split | First missing | Last missing | Minutes |",
        "| ---: | --- | --- | --- | ---: |",
        *_rows(halts, len(gaps) + 1),
        "",
        f"Totals: {len(halts)} halts, {sum(map(_minutes, halts)):,} minutes.",
        "",
        "Not listed: research flat zero-volume runs that do not end at a gap, treated as real",
        f"quiet trading: {len(unlisted)} runs, {sum(map(_minutes, unlisted)):,} minutes.",
        f"Outside research, flat zero-volume minutes (counts only): {outside}.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--symbol", type=parse_symbol, required=True, help="e.g. ETH-USDT")
    parser.add_argument("--start", default="2019-01-01", help="first UTC date, YYYY-MM-DD")
    parser.add_argument("--end", help="UTC date to stop before, YYYY-MM-DD (default: today)")
    parser.add_argument("--write", action="store_true", help="save to data/metadata/")
    args = parser.parse_args()

    today = datetime.now(UTC).strftime("%Y-%m-%d")
    start, end = _ms(args.start), _ms(args.end or today)
    target = METADATA_DIR / gap_file_name(args.symbol)
    if args.write and target.exists():
        sys.exit(f"{target} exists; move it aside first so the old list is not lost by accident.")

    print(f"Scanning {args.symbol} from {args.start} (timestamps only)...", file=sys.stderr)
    result = scan(iter_minutes(binance_fetch(args.symbol), start, end))
    text = render(args.symbol, result, start, end, scanned_on=today)
    if args.write:
        target.write_text(text, encoding="utf-8")
        print(f"Wrote {target}", file=sys.stderr)
    else:
        print(text)


if __name__ == "__main__":
    main()
