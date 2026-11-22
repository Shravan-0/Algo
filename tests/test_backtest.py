import pandas as pd

from scripts.run_backtest import resample_complete_ohlcv


def test_resample_separates_complete_partial_and_empty_buckets():
    complete_index = pd.date_range(
        "2024-01-01 00:00:00",
        periods=12,
        freq="5min",
        tz="UTC",
    )
    partial_index = pd.date_range(
        "2024-01-01 02:00:00",
        periods=2,
        freq="5min",
        tz="UTC",
    )
    index = complete_index.append(partial_index)

    frame = pd.DataFrame(
        {
            "open": [100.0] * len(index),
            "high": [101.0] * len(index),
            "low": [99.0] * len(index),
            "close": [100.5] * len(index),
            "volume": [1.0] * len(index),
        },
        index=index,
    )

    result, audit = resample_complete_ohlcv(frame, "1h", "5min")

    assert len(result) == 1
    assert result.index[0] == pd.Timestamp("2024-01-01 00:00:00", tz="UTC")
    assert audit == {
        "complete": 1,
        "empty": 1,
        "partial": 1,
        "malformed": 0,
    }
