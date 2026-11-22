# EMA 50/200 XAUUSD H1 - Final Walk-Forward Validation

Dataset: C:\MarketData\XAUUSD\processed\XAUUSD_M5.parquet
Target timeframe: 1h
Complete H1 candles retained: 64,919
Empty H1 buckets: 31,399
Partial H1 buckets excluded: 89
Malformed H1 buckets excluded: 0
Initial cash per fold: 100,000.00
Fees per order: 0.0200%
Slippage per order: 0.0100%

## Validation methodology

- Anchored expanding training history.
- Six-month, non-overlapping out-of-sample test windows.
- Minimum three years of historical training data before each test.
- EMA 50/200 parameters remain fixed; no optimization is performed.
- Indicators use chronological historical data only.
- Signals are shifted one bar and executed at the next bar open.
- Each test fold starts with independent initial cash and a flat position.
- Fold returns are not a continuous broker equity curve.

## Fold results

| Fold | Training bars | Test bars | Test period | Return | Max DD | Trades | Win rate | Profit factor |
|---|---:|---:|---|---:|---:|---:|---:|---:|
| fold_01 | 41,306 | 2,933 | 2022-01-02 to 2022-06-30 | -0.90% | -12.70% | 8 | 25.00% | 0.89 |
| fold_02 | 44,239 | 2,974 | 2022-07-01 to 2022-12-30 | 5.46% | -5.74% | 6 | 50.00% | 2.03 |
| fold_03 | 47,213 | 2,931 | 2023-01-02 to 2023-06-30 | 1.41% | -5.67% | 8 | 12.50% | 1.24 |
| fold_04 | 50,144 | 2,952 | 2023-07-02 to 2023-12-29 | 8.05% | -6.40% | 7 | 42.86% | 4.88 |
| fold_05 | 53,096 | 2,933 | 2024-01-01 to 2024-06-30 | 6.93% | -8.63% | 7 | 14.29% | 2.13 |
| fold_06 | 56,029 | 2,992 | 2024-07-01 to 2024-12-31 | 6.17% | -6.32% | 10 | 40.00% | 2.02 |
| fold_07 | 59,021 | 2,907 | 2025-01-01 to 2025-06-30 | 13.65% | -9.66% | 7 | 57.14% | 5.02 |
| fold_08 | 61,928 | 2,991 | 2025-07-01 to 2025-12-31 | 20.98% | -9.30% | 6 | 33.33% | 6.75 |

## Aggregate validation statistics

- Number of test folds: 8
- Positive-return folds: 7/8
- Positive-fold ratio: 87.50%
- Mean fold return: 7.72%
- Median fold return: 6.55%
- Geometrically compounded fold return: 78.77%
- Worst individual fold drawdown: -12.70%
- Total closed trades across folds: 59
- Median fold profit factor: 2.08

## Interpretation and limitations

- These are historical simulation results, not live performance.
- Fold portfolios reset independently; compounded return is diagnostic, not a continuous portfolio result.
- Spread and broker-specific contract specifications are not modelled.
- Fees and slippage remain assumptions from config.yaml.
- The strategy is single-instrument and long-only.
- All-in position sizing is a research assumption, not fixed-risk or broker lot sizing.
- Positive historical folds do not establish a reliable future trading edge.

The validation evaluates the fixed strategy across chronological unseen periods. It does not optimize or select strategy parameters.
