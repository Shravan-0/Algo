# Algo

A lightweight quantitative research repository focused on testing rule-based trading strategies on historical XAUUSD data.

The first study is an EMA 50/200 trend-following strategy. The repository is designed to grow gradually: each strategy has its own source file and its own results folder.

## Current study

| Strategy | Market | Timeframe | Status |
|---|---|---|---|
| EMA 50/200 crossover | XAUUSD | H1 | Research baseline; rerun on validated Dukascopy data |

> The current backtest report is exploratory and must not be treated as validated performance. The old H1 CSV included with the original project was synthetic placeholder data and must not be used to support performance claims.

## Data

The intended research dataset is Dukascopy XAUUSD M5 data for 2015–2025. Keep the full raw dataset outside this Git repository. By default, the builder looks for yearly files named `XAUUSD_M5_YYYY.csv` in `C:\MarketData\XAUUSD\M5`.

Set a different folder with the `XAUUSD_M5_DIR` environment variable if needed. The builder standardizes the files, checks timestamps and OHLC values, reports candidate intraday gaps separately from long market closures, and writes a local Parquet file to the path configured in `config.yaml`. Keep market data outside Git.

The loader treats timestamps as UTC. Confirm the CSV's timestamp format and price-side metadata against your Dukascopy export before relying on research results. The code does not infer whether the prices are bid or ask. An optional MetaTrader 5 downloader is retained in `scripts/download_mt5.py`; install `requirements-mt5.txt` only if you use it.

## Setup

Python 3.10 or newer is recommended.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Build the dataset

```powershell
$env:XAUUSD_M5_DIR = "C:\MarketData\XAUUSD\M5"
python scripts/build_dataset.py
```

The script writes to the output path configured in `config.yaml` and prints a data-quality summary. It does not fill missing candles. Candidate gaps include intervals longer than five minutes but no longer than 24 hours; long closures are reported separately, so normal market closures are not presented as missing candles.

## Run the EMA study

```powershell
python scripts/run_backtest.py
```

The backtest resamples M5 candles to H1, calculates EMA 50/200 signals, and shifts signals by one bar so they are not executed on the same bar that generated them. It uses the next bar's open as the assumed fill price, with configurable flat fees and slippage in `config.yaml`.

Results are written to `results/ema_trend/`:

- `report.md`
- `equity_curve.png`
- `drawdown.png`
- `yearly_returns.csv`

The report separates 2015–2021 in-sample and 2022–2025 out-of-sample periods. These are research splits, not a guarantee against all forms of selection bias.

## Add another strategy

1. Add a strategy module under `strategies/`.
2. Add tests under `tests/`.
3. Run it using the shared data and execution assumptions.
4. Save its report and charts in a matching `results/<strategy_name>/` directory.
5. Add the result to the study table above only after the run is reproducible.

## Project structure

```text
Algo/
├── data/                 # local data; raw and processed data are gitignored
├── results/
│   └── ema_trend/        # reproducible research outputs
├── scripts/
│   ├── build_dataset.py
│   └── run_backtest.py
├── src/
│   └── main/
│       └── data.py
├── strategies/
│   └── ema_trend.py
├── tests/
├── config.yaml
├── requirements.txt
└── README.md
```

## Limitations

- One market and one baseline strategy are currently included.
- The strategy is long-only; a sell signal closes the long position.
- Fees and slippage are simplified flat assumptions, not a full broker spread/commission model.
- No live order execution is included.
- Results depend on data quality, timezone alignment, fill assumptions, and parameter choices.

## Disclaimer

For research and educational purposes only. Backtests are hypothetical and do not guarantee future results. Trading involves risk.

## Author

Shravan
