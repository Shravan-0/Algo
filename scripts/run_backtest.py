"""Run an EMA 50/200 XAUUSD H1 backtest with historical indicator warm-up."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import pandas as pd
import vectorbt as vbt
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from strategies.ema_trend import generate_signals

CONFIG_PATH = ROOT / "config.yaml"


def load_config():
    with CONFIG_PATH.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def resample_complete_ohlcv(frame, timeframe, source_timeframe="5min"):
    """Keep only target bars containing every expected source candle."""
    target_delta = pd.Timedelta(timeframe)
    source_delta = pd.Timedelta(source_timeframe)

    if target_delta <= source_delta or target_delta % source_delta:
        raise ValueError("Target timeframe must be a multiple of source timeframe.")

    expected = int(target_delta / source_delta)

    grouped = frame.resample(
        timeframe,
        label="left",
        closed="left",
    )

    result = grouped.agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum",
    })

    counts = grouped["close"].count()
    complete = counts == expected

    excluded = int((~complete).sum())
    result = result.loc[complete]
    result = result.dropna(subset=["open", "high", "low", "close"])

    return result, excluded


def metric(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def run_period(data, entries, exits, label, cash, fees, slippage, timeframe):
    portfolio = vbt.Portfolio.from_signals(
        close=data["close"],
        entries=entries,
        exits=exits,
        price=data["open"],
        init_cash=cash,
        fees=fees,
        slippage=slippage,
        freq=timeframe,
    )

    closed = portfolio.trades.closed

    stats = {
        "period": label,
        "bars": len(data),
        "return_pct": metric(portfolio.total_return()) * 100,
        "max_drawdown_pct": metric(portfolio.max_drawdown()) * 100,
        "closed_trades": int(closed.count()),
        "win_rate_pct": metric(closed.win_rate()) * 100,
        "profit_factor": metric(closed.profit_factor()),
        "open_trades": int(portfolio.trades.open.count()),
    }

    return stats, portfolio.value()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", default=None)
    args = parser.parse_args()

    config = load_config()
    data_config = config["data"]
    bt = config["backtest"]

    source = Path(
        args.data or data_config["output_file"]
    )

    if not source.exists():
        raise FileNotFoundError(f"Dataset not found: {source}")

    cash = float(bt["initial_cash"])
    fees = float(bt["fees"])
    slippage = float(bt["slippage"])
    timeframe = str(bt["timeframe"])
    source_timeframe = str(bt["source_timeframe"])

    m5 = pd.read_parquet(source)

    if not isinstance(m5.index, pd.DatetimeIndex):
        if "time" not in m5.columns:
            raise ValueError("Dataset needs a DatetimeIndex or time column.")
        m5["time"] = pd.to_datetime(m5["time"], utc=True)
        m5 = m5.set_index("time")

    if m5.index.tz is None:
        raise ValueError("Dataset timestamps must be timezone-aware.")

    m5 = m5.sort_index()

    h1, excluded = resample_complete_ohlcv(
        m5,
        timeframe,
        source_timeframe,
    )

    if h1.empty:
        raise ValueError("No complete target-timeframe candles found.")

    # Calculate indicators on the entire chronological history.
    # EMA uses past observations only, so this supplies warm-up history
    # without introducing future information.
    all_entries, all_exits, _, _ = generate_signals(h1["close"])

    # A signal at bar t is executed at bar t+1 open.
    all_entries = all_entries.shift(1).fillna(False).astype(bool)
    all_exits = all_exits.shift(1).fillna(False).astype(bool)

    in_start = pd.Timestamp(h1.index.min())
    in_end = pd.Timestamp(bt["in_sample_end"])
    oos_start = pd.Timestamp(bt["out_of_sample_start"])
    oos_end = pd.Timestamp(bt["out_of_sample_end"])

    if in_end.tzinfo is None or oos_start.tzinfo is None or oos_end.tzinfo is None:
        raise ValueError("Configured period boundaries must include UTC offsets.")

    periods = {
        "in_sample": (in_start, in_end),
        "out_of_sample": (oos_start, oos_end),
    }

    results_dir = ROOT / "results" / "ema_trend"
    results_dir.mkdir(parents=True, exist_ok=True)

    reports = []
    oos_equity = None

    for label, (start, end) in periods.items():
        period = h1.loc[start:end]

        if period.empty:
            raise ValueError(f"No complete H1 bars for {label}.")

        entries = all_entries.reindex(period.index, fill_value=False)
        exits = all_exits.reindex(period.index, fill_value=False)

        stats, equity = run_period(
            period,
            entries,
            exits,
            label,
            cash,
            fees,
            slippage,
            timeframe,
        )

        reports.append(stats)

        if label == "out_of_sample":
            oos_equity = equity

    lines = [
        "# EMA 50/200 XAUUSD H1 Backtest",
        "",
        f"Dataset: {source}",
        f"Target timeframe: {timeframe}",
        f"Complete bars retained: {len(h1):,}",
        f"Incomplete target buckets excluded: {excluded:,}",
        f"Initial cash per test: {cash:,.2f}",
        f"Fees per order: {fees:.4%}",
        f"Slippage per order: {slippage:.4%}",
        "",
        "EMA indicators are calculated chronologically using available historical data.",
        "Signals are shifted one bar and executed at the next bar open.",
        "In-sample and out-of-sample portfolios start independently with flat positions.",
        "",
        "Position sizing uses VectorBT defaults; this is not a broker contract or risk-based sizing model.",
        "",
        "| Period | Bars | Return | Max DD | Closed trades | Open trades | Win rate | Profit factor |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for row in reports:
        lines.append(
            f"| {row['period']} | {row['bars']:,} | "
            f"{row['return_pct']:.2f}% | {row['max_drawdown_pct']:.2f}% | "
            f"{row['closed_trades']} | {row['open_trades']} | "
            f"{row['win_rate_pct']:.2f}% | {row['profit_factor']:.2f} |"
        )

    lines += [
        "",
        "## Limitations",
        "",
        "- Historical simulation, not live trading performance.",
        "- Spread and broker-specific contract specifications are not modelled.",
        "- Fees and slippage are assumptions.",
        "- Single instrument and long-only strategy.",
        "- Incomplete H1 buckets are excluded.",
        "- Position sizing requires further specification.",
        "",
    ]

    (results_dir / "report.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    if oos_equity is not None:
        drawdown = (oos_equity / oos_equity.cummax() - 1) * 100

        fig, ax = plt.subplots(figsize=(11, 5))
        oos_equity.plot(ax=ax, title="EMA 50/200 - XAUUSD H1 - Out of sample")
        ax.set_ylabel("Portfolio value")
        ax.grid(True, alpha=0.25)
        fig.tight_layout()
        fig.savefig(results_dir / "equity_curve.png", dpi=150)
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(11, 4))
        drawdown.plot(ax=ax, title="Out-of-sample drawdown")
        ax.set_ylabel("Drawdown (%)")
        ax.grid(True, alpha=0.25)
        fig.tight_layout()
        fig.savefig(results_dir / "drawdown.png", dpi=150)
        plt.close(fig)

        yearly_equity = oos_equity.resample("YE").last()
        yearly_returns = yearly_equity.pct_change()

        if len(yearly_returns):
            yearly_returns.iloc[0] = (
                yearly_equity.iloc[0] / cash
            ) - 1

        yearly_returns.rename("return").to_csv(
            results_dir / "yearly_returns.csv",
            header=True,
        )

    print("\n".join(lines))
    print(f"\nResults saved to: {results_dir}")


if __name__ == "__main__":
    main()
