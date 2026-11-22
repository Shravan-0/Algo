import pandas as pd
import pytest

from scripts.run_walk_forward import build_walk_forward_folds


def test_builds_eight_non_overlapping_six_month_folds():
    index = pd.date_range(
        "2015-01-01",
        "2025-12-31",
        freq="h",
        tz="UTC",
    )

    folds = build_walk_forward_folds(
        index,
        "2022-01-01 00:00:00+00:00",
        "2025-12-31 23:59:59+00:00",
    )

    assert len(folds) == 8
    assert folds[0]["test_start"] == pd.Timestamp("2022-01-01", tz="UTC")
    assert folds[0]["train_start"] == index.min()
    assert folds[0]["train_end"] < folds[0]["test_start"]
    assert folds[-1]["test_end"] <= pd.Timestamp(
        "2025-12-31 23:59:59",
        tz="UTC",
    )

    for previous, current in zip(folds, folds[1:]):
        assert previous["test_end"] < current["test_start"]
        assert previous["train_start"] == current["train_start"]
        assert current["training_bars"] > previous["training_bars"]


def test_rejects_naive_timestamps():
    index = pd.date_range("2015-01-01", periods=100, freq="h")

    with pytest.raises(ValueError, match="timezone-aware"):
        build_walk_forward_folds(
            index,
            "2022-01-01 00:00:00+00:00",
            "2022-12-31 23:59:59+00:00",
        )


def test_rejects_insufficient_training_history():
    index = pd.date_range(
        "2020-01-01",
        "2025-12-31",
        freq="h",
        tz="UTC",
    )

    with pytest.raises(ValueError, match="Insufficient training history"):
        build_walk_forward_folds(
            index,
            "2022-01-01 00:00:00+00:00",
            "2022-12-31 23:59:59+00:00",
        )
