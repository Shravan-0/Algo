# EMA 50/200 XAUUSD H1 Backtest

Dataset: C:\MarketData\XAUUSD\processed\XAUUSD_M5.parquet
Target timeframe: 1h
Complete bars retained: 64,919
Incomplete target buckets excluded: 31,488
Initial cash per test: 100,000.00
Fees per order: 0.0200%
Slippage per order: 0.0100%

EMA indicators are calculated chronologically using available historical data.
Signals are shifted one bar and executed at the next bar open.
In-sample and out-of-sample portfolios start independently with flat positions.

Position sizing uses VectorBT defaults; this is not a broker contract or risk-based sizing model.

| Period | Bars | Return | Max DD | Closed trades | Open trades | Win rate | Profit factor |
|---|---:|---:|---:|---:|---:|---:|---:|
| in_sample | 41,306 | 10.82% | -21.34% | 128 | 1 | 28.91% | 1.10 |
| out_of_sample | 23,613 | 84.97% | -14.48% | 61 | 0 | 34.43% | 2.88 |

## Limitations

- Historical simulation, not live trading performance.
- Spread and broker-specific contract specifications are not modelled.
- Fees and slippage are assumptions.
- Single instrument and long-only strategy.
- Incomplete H1 buckets are excluded.
- Position sizing requires further specification.
