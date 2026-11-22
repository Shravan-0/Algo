"""EMA 50/200 trend-following signals for XAUUSD research."""

import pandas as pd


def generate_signals(close: pd.Series, fast_period: int = 50, slow_period: int = 200):
    """Return raw crossover entries/exits. Execution delay is applied by the runner."""
    if fast_period <= 0 or slow_period <= 0 or fast_period >= slow_period:
        raise ValueError("Periods must be positive and fast_period must be smaller than slow_period.")

    fast = close.ewm(span=fast_period, adjust=False, min_periods=fast_period).mean()
    slow = close.ewm(span=slow_period, adjust=False, min_periods=slow_period).mean()
    entries = (fast > slow) & (fast.shift(1) <= slow.shift(1))
    exits = (fast < slow) & (fast.shift(1) >= slow.shift(1))
    return entries.fillna(False), exits.fillna(False), fast, slow
