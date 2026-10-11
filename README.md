# Daily Trade Summary

A small Python command-line tool that turns a trade-history CSV into a daily
performance report: trades, win rate, net profit, profit factor, best and worst
trade per day, plus overall maximum drawdown.

The CSV can be a local file (for example an export from MetaTrader 5) or a
Google Sheet published to the web as CSV, so it fits automated daily reporting.
It uses only the Python standard library (Python 3.10+).

## Usage

```bash
python daily_summary.py sample_trades.csv
python daily_summary.py sample_trades.csv --out report.md
python daily_summary.py "https://docs.google.com/spreadsheets/d/e/.../pub?output=csv"
```

Input columns (case-insensitive): `close_time`, `symbol`, `profit`.
Rows that cannot be parsed are skipped with a warning.

## Example output

| Day | Trades | Win % | Net | Profit factor | Best | Worst |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-10-05 | 3 | 67 | +26.05 | 4.22 | +21.75 | -8.10 |
| 2026-10-06 | 3 | 33 | -10.50 | 0.47 | +9.30 | -15.20 |

## Tests

```bash
python -m unittest -v
```

`sample_trades.csv` contains made-up example data.
