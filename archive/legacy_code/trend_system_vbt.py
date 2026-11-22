
import vectorbt as vbt
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt

# Define paths
DATA_PATH = os.path.join("data", "XAUUSD_H1.csv")
REPORT_PATH = os.path.join("research", "trend_system_report.txt")
PLOT_PATH = os.path.join("research", "trend_equity_curve.png")

# Ensure research directory exists
os.makedirs("research", exist_ok=True)

def run_backtest():
    if not os.path.exists(DATA_PATH):
        print(f"Error: Data file not found at {DATA_PATH}")
        return

    # Load data
    print("Loading data...")
    df = pd.read_csv(DATA_PATH, index_col='time', parse_dates=True)
    price = df['close']

    # Calculate indicators
    print("Calculating indicators...")
    # EMA 50 and 200
    ema50 = vbt.MA.run(price, 50, ewm=True, short_name='EMA50')
    ema200 = vbt.MA.run(price, 200, ewm=True, short_name='EMA200')

    # Generate signals
    entries = ema50.ma_crossed_above(ema200)
    exits = ema50.ma_crossed_below(ema200)

    # Clean signals (remove consecutive entries etc? vectorbt portfolio handles this by default usually)
    # But explicitly cleaner logic:
    # entries = entries.vbt.signals.clean(exits)
    # exits = exits.vbt.signals.clean(entries)
    
    # Setup Portfolio
    print("Running backtest...")
    portfolio = vbt.Portfolio.from_signals(
        price,
        entries,
        exits,
        init_cash=100000,
        fees=0.0002,
        slippage=0.0001,
        freq='1h'  # hourly data
    )

    # Calculate metrics
    total_return = portfolio.total_return()
    sharpe_ratio = portfolio.sharpe_ratio()
    max_drawdown = portfolio.max_drawdown()
    win_rate = portfolio.trades.win_rate()
    profit_factor = portfolio.trades.profit_factor()

    metrics = (
        f"--- Backtest Report ---\n"
        f"Strategy: EMA Crossover (50/200)\n"
        f"Symbol: XAUUSD H1\n"
        f"Total Return: {total_return:.2%}\n"
        f"Sharpe Ratio: {sharpe_ratio:.2f}\n"
        f"Max Drawdown: {max_drawdown:.2%}\n"
        f"Win Rate: {win_rate:.2%}\n"
        f"Profit Factor: {profit_factor:.2f}\n"
    )

    print(metrics)

    # Save metrics to report
    with open(REPORT_PATH, "w") as f:
        f.write(metrics)
    print(f"Report saved to: {REPORT_PATH}")

    # Plot Equity Curve
    print("Generating plot...")
    # Basic plot
    # fig = portfolio.plot(subplots=['cum_returns', 'orders', 'trade_pnl'])
    # Or just equity curve
    fig = portfolio.value().vbt.plot(title='Equity Curve - Trend System')
    
    # Save plot
    fig.write_image(PLOT_PATH)
    print(f"Plot saved to: {PLOT_PATH}")

    # Show plot structure for verification (optional)
    # fig.show()

if __name__ == "__main__":
    try:
        run_backtest()
    except Exception as e:
        print(f"An error occurred: {e}")
