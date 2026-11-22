import pandas as pd

from src.main.data import standardize_frame, resample_ohlcv


def test_standardize_frame_sorts_and_removes_duplicate_timestamps():
    frame = pd.DataFrame({
        "timestamp": ["2020-01-01 00:05:00", "2020-01-01 00:00:00", "2020-01-01 00:00:00"],
        "open": [2, 1, 1],
        "high": [3, 2, 2],
        "low": [1, 0.5, 0.5],
        "close": [2.5, 1.5, 1.6],
        "volume": [10, 5, 6],
    })
    result = standardize_frame(frame)
    assert result.index.is_monotonic_increasing
    assert not result.index.has_duplicates
    assert len(result) == 2


def test_resample_ohlcv_aggregates_bars():
    index = pd.date_range("2020-01-01", periods=12, freq="5min", tz="UTC")
    frame = pd.DataFrame({
        "open": range(100, 112),
        "high": range(101, 113),
        "low": range(99, 111),
        "close": range(100, 112),
        "volume": [1] * 12,
    }, index=index)
    result = resample_ohlcv(frame, "1h")
    assert len(result) == 1
    assert result.iloc[0]["open"] == 100
    assert result.iloc[0]["close"] == 111
    assert result.iloc[0]["volume"] == 12
