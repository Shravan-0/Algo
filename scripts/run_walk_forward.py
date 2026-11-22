"""Run anchored walk-forward validation for the EMA 50/200 strategy."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_backtest import (
    load_config,
    metric,
    resample_complete_ohlcv,
    run_period,
)
from strategies.ema_trend import generate_signals


ROOT = Path(__file__).resolve().parents[1]


def build_walk_forward_folds(
    index,
    oos_start,
    oos_end,
    test_months=6,
    min_train_years=3,
):
    """Build expanding-training, non-overlapping chronological test folds."""
    index = pd.DatetimeIndex(index)

    if index.tz is None:
        raise ValueError("Walk-forward timestamps must be timezone-aware.")
    if test_months <= 0 or min_train_years <= 0:
        raise ValueError("Fold duration and minimum training years must be positive.")

    start = pd.Timestamp(oos_start)
    end = pd.Timestamp(oos_end)

    if start.tzinfo is None or end.tzinfo is None:
        raise ValueError("Configured walk-forward boundaries need UTC offsets.")
    if start > end:
        raise ValueError("OOS start must not be after OOS end.")

    index = index.sort_values()
    folds = []
    current = start
    fold_number = 1

    while current <= end:
        next_start = current + pd.DateOffset(months=test_months)
        test_end = min(next_start - pd.Timedelta(nanoseconds=1), end)
        train_end = current - pd.Timedelta(nanoseconds=1)

        if index.min() + pd.DateOffset(years=min_train_years) > current:
            raise ValueError(
                f"Insufficient training history before {current}. "
                f"At least {min_train_years} years are required."
            )

        training_index = index[index <= train_end]
        testing_index = index[(index >= current) & (index <= test_end)]

        if training_index.empty:
            raise ValueError(f"No training history before {current}.")
        if testing_index.empty:
            raise ValueError(
                f"No test candles found between {current} and {test_end}."
            )

        folds.append({
            "fold": f"fold_{fold_number:02d}",
            "train_start": training_index.min(),
            "train_end": training_index.max(),
            "test_start": testing_index.min(),
            "test_end": testing_index.max(),
            "training_bars": len(training_index),
            "testing_bars": len(testing_index),
        })

        current = next_start
        fold_number += 1

    if not folds:
        raise ValueError("No walk-forward folds could be generated.")

    return folds


def main():
    config = load_config()
    data_config = config["data"]
    bt = config["backtest"]

    source = Path(data_config["output_file"])
    if not source.exists():
        raise FileNotFoundError(f"Dataset not found: {source}")

    timeframe = str(bt["timeframe"])
    source_timeframe = str(bt["source_timeframe"])
    cash = float(bt["initial_cash"])
    fees = float(bt["fees"])
    slippage = float(bt["slippage"])

    m5 = pd.read_parquet(source)

    if not isinstance(m5.index, pd.DatetimeIndex):
        if "time" not in m5.columns:
            raise ValueError("Dataset needs a DatetimeIndex or time column.")
        m5["time"] = pd.to_datetime(m5["time"], utc=True)
        m5 = m5.set_index("time")

    if m5.index.tz is None:
        raise ValueError("Dataset timestamps must be timezone-aware.")

    m5 = m5.sort_index()

    h1, bucket_audit = resample_complete_ohlcv(
        m5,
        timeframe,
        source_timeframe,
    )

    if h1.empty:
        raise ValueError("No complete target-timeframe candles found.")

    # Indicators are calculated chronologically using past observations.
    # The one-bar shift means signals execute at the next bar open.
    all_entries, all_exits, _, _ = generate_signals(h1["close"])
    all_entries = all_entries.shift(1).fillna(False).astype(bool)
    all_exits = all_exits.shift(1).fillna(False).astype(bool)

    folds = build_walk_forward_folds(
        h1.index,
        bt["out_of_sample_start"],
        bt["out_of_sample_end"],
        test_months=6,
        min_train_years=3,
    )

    results_dir = ROOT / "results" / "ema_trend"
    results_dir.mkdir(parents=True, exist_ok=True)

    rows = []

    for fold in folds:
        test_start = fold["test_start"]
        test_end = fold["test_end"]

        test_data = h1.loc[test_start:test_end]
        entries = all_entries.reindex(test_data.index, fill_value=False)
        exits = all_exits.reindex(test_data.index, fill_value=False)

        stats, _ = run_period(
            test_data,
            entries,
            exits,
            fold["fold"],
            cash,
            fees,
            slippage,
            timeframe,
        )

        rows.append({
            **stats,
            "train_start": fold["train_start"],
            "train_end": fold["train_end"],
            "test_start": test_start,
            "test_end": test_end,
            "training_bars": fold["training_bars"],
        })

    results = pd.DataFrame(rows)
    results.to_csv(
        results_dir / "walk_forward_results.csv",
        index=False,
    )

    returns = results["return_pct"].astype(float)
    drawdowns = results["max_drawdown_pct"].astype(float)
    profit_factors = results["profit_factor"].astype(float)

    compounded_return = (
        math.prod(1 + value / 100 for value in returns) - 1
    ) * 100

    positive_folds = int((returns > 0).sum())
    total_trades = int(results["closed_trades"].sum())
    median_pf = metric(profit_factors.median())

    lines = [
        "# EMA 50/200 XAUUSD H1 - Final Walk-Forward Validation",
        "",
        f"Dataset: {source}",
        f"Target timeframe: {timeframe}",
        f"Complete H1 candles retained: {bucket_audit['complete']:,}",
        f"Empty H1 buckets: {bucket_audit['empty']:,}",
        f"Partial H1 buckets excluded: {bucket_audit['partial']:,}",
        f"Malformed H1 buckets excluded: {bucket_audit['malformed']:,}",
        f"Initial cash per fold: {cash:,.2f}",
        f"Fees per order: {fees:.4%}",
        f"Slippage per order: {slippage:.4%}",
        "",
        "## Validation methodology",
        "",
        "- Anchored expanding training history.",
        "- Six-month, non-overlapping out-of-sample test windows.",
        "- Minimum three years of historical training data before each test.",
        "- EMA 50/200 parameters remain fixed; no optimization is performed.",
        "- Indicators use chronological historical data only.",
        "- Signals are shifted one bar and executed at the next bar open.",
        "- Each test fold starts with independent initial cash and a flat position.",
        "- Fold returns are not a continuous broker equity curve.",
        "",
        "## Fold results",
        "",
        "| Fold | Training bars | Test bars | Test period | Return | Max DD | Trades | Win rate | Profit factor |",
        "|---|---:|---:|---|---:|---:|---:|---:|---:|",
    ]

    for row in rows:
        lines.append(
            f"| {row['period']} | {row['training_bars']:,} | "
            f"{row['bars']:,} | "
            f"{pd.Timestamp(row['test_start']).date()} to "
            f"{pd.Timestamp(row['test_end']).date()} | "
            f"{row['return_pct']:.2f}% | "
            f"{row['max_drawdown_pct']:.2f}% | "
            f"{row['closed_trades']} | "
            f"{row['win_rate_pct']:.2f}% | "
            f"{row['profit_factor']:.2f} |"
        )

    lines += [
        "",
        "## Aggregate validation statistics",
        "",
        f"- Number of test folds: {len(results)}",
        f"- Positive-return folds: {positive_folds}/{len(results)}",
        f"- Positive-fold ratio: {positive_folds / len(results):.2%}",
        f"- Mean fold return: {returns.mean():.2f}%",
        f"- Median fold return: {returns.median():.2f}%",
        f"- Geometrically compounded fold return: {compounded_return:.2f}%",
        f"- Worst individual fold drawdown: {drawdowns.min():.2f}%",
        f"- Total closed trades across folds: {total_trades}",
        f"- Median fold profit factor: {median_pf:.2f}",
        "",
        "## Interpretation and limitations",
        "",
        "- These are historical simulation results, not live performance.",
        "- Fold portfolios reset independently; compounded return is diagnostic, not a continuous portfolio result.",
        "- Spread and broker-specific contract specifications are not modelled.",
        "- Fees and slippage remain assumptions from config.yaml.",
        "- The strategy is single-instrument and long-only.",
        "- All-in position sizing is a research assumption, not fixed-risk or broker lot sizing.",
        "- Positive historical folds do not establish a reliable future trading edge.",
        "",
        "The validation evaluates the fixed strategy across chronological unseen periods. "
        "It does not optimize or select strategy parameters.",
        "",
    ]

    report_path = results_dir / "walk_forward_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")

    print("\n".join(lines))
    print(f"\nReport saved: {report_path}")
    print(f"Fold data saved: {results_dir / 'walk_forward_results.csv'}")


if __name__ == "__main__":
    main()

