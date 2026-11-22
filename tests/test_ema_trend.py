import pandas as pd

from strategies.ema_trend import generate_signals


def test_signal_output_has_boolean_entries_and_exits():
    close = pd.Series([10, 9, 8, 9, 10, 11, 12, 11, 10, 9], dtype=float)
    entries, exits, fast, slow = generate_signals(close, fast_period=2, slow_period=4)

    assert entries.dtype == bool
    assert exits.dtype == bool
    assert len(fast) == len(close)
    assert len(slow) == len(close)


def test_invalid_periods_raise():
    close = pd.Series([1.0, 2.0, 3.0])
    try:
        generate_signals(close, fast_period=5, slow_period=2)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected invalid EMA periods to raise ValueError")
