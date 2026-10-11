"""Daily trade summary: turn a trade-history CSV into a clean daily report.

The CSV can be a local file or a Google Sheet published to the web as CSV
(File > Share > Publish to web > CSV). Only the Python standard library is used.

Expected columns (case-insensitive): close_time, symbol, profit
"""
from __future__ import annotations

import argparse
import csv
import io
import logging
import sys
import urllib.request
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

log = logging.getLogger("daily_summary")

REQUIRED = ("close_time", "symbol", "profit")
TIME_FORMATS = ("%Y-%m-%d %H:%M:%S", "%Y.%m.%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d")


@dataclass(frozen=True)
class Trade:
    closed: datetime
    symbol: str
    profit: float


@dataclass(frozen=True)
class DaySummary:
    day: str
    trades: int
    wins: int
    net: float
    profit_factor: float | None
    best: float
    worst: float

    @property
    def win_rate(self) -> float:
        return 100 * self.wins / self.trades if self.trades else 0.0


def read_text(source: str) -> str:
    """Return CSV text from a file path or an http(s) URL."""
    if source.lower().startswith(("http://", "https://")):
        log.info("Downloading %s", source)
        with urllib.request.urlopen(source, timeout=20) as resp:
            return resp.read().decode("utf-8-sig")
    return Path(source).read_text(encoding="utf-8-sig")


def parse_time(value: str) -> datetime:
    for fmt in TIME_FORMATS:
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    raise ValueError(f"unrecognised time format: {value!r}")


def parse_trades(text: str) -> list[Trade]:
    """Parse CSV text into trades, skipping bad rows with a warning."""
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise ValueError("CSV is empty")
    fields = {name.strip().lower(): name for name in reader.fieldnames}
    missing = [col for col in REQUIRED if col not in fields]
    if missing:
        raise ValueError(f"CSV is missing column(s): {', '.join(missing)}")

    trades: list[Trade] = []
    for line_no, row in enumerate(reader, start=2):
        try:
            trades.append(
                Trade(
                    closed=parse_time(row[fields["close_time"]]),
                    symbol=row[fields["symbol"]].strip(),
                    profit=float(row[fields["profit"]]),
                )
            )
        except (ValueError, TypeError, KeyError) as err:
            log.warning("Skipping line %d: %s", line_no, err)
    return trades


def summarise(trades: list[Trade]) -> list[DaySummary]:
    by_day: dict[str, list[float]] = defaultdict(list)
    for t in trades:
        by_day[t.closed.strftime("%Y-%m-%d")].append(t.profit)

    out = []
    for day in sorted(by_day):
        pnl = by_day[day]
        gains = sum(p for p in pnl if p > 0)
        losses = -sum(p for p in pnl if p < 0)
        out.append(
            DaySummary(
                day=day,
                trades=len(pnl),
                wins=sum(1 for p in pnl if p > 0),
                net=sum(pnl),
                profit_factor=(gains / losses) if losses else None,
                best=max(pnl),
                worst=min(pnl),
            )
        )
    return out


def max_drawdown(trades: list[Trade]) -> float:
    """Largest peak-to-trough fall of cumulative profit, in account currency."""
    equity = peak = worst = 0.0
    for t in sorted(trades, key=lambda x: x.closed):
        equity += t.profit
        peak = max(peak, equity)
        worst = max(worst, peak - equity)
    return worst


def render_markdown(days: list[DaySummary], trades: list[Trade]) -> str:
    lines = [
        "# Daily trade summary",
        "",
        "| Day | Trades | Win % | Net | Profit factor | Best | Worst |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for d in days:
        pf = f"{d.profit_factor:.2f}" if d.profit_factor is not None else "n/a"
        lines.append(
            f"| {d.day} | {d.trades} | {d.win_rate:.0f} | {d.net:+.2f} | {pf} "
            f"| {d.best:+.2f} | {d.worst:+.2f} |"
        )
    total = sum(d.net for d in days)
    lines += [
        "",
        f"**Total:** {len(trades)} trades, net {total:+.2f}, "
        f"max drawdown {max_drawdown(trades):.2f}",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("source", help="CSV file path or published Google Sheet CSV URL")
    parser.add_argument("-o", "--out", help="also write the report to this .md file")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING,
                        format="%(levelname)s: %(message)s")

    try:
        trades = parse_trades(read_text(args.source))
    except (OSError, ValueError) as err:
        log.error("%s", err)
        return 1
    if not trades:
        log.error("No valid trades found")
        return 1

    report = render_markdown(summarise(trades), trades)
    print(report)
    if args.out:
        Path(args.out).write_text(report + "\n", encoding="utf-8")
        log.info("Report written to %s", args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
