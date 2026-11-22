
"""Load, standardize, validate, and resample Dukascopy-style OHLCV CSV data."""

from __future__ import annotations

from pathlib import Path
import re

import pandas as pd


ALIASES = {
    "time": {"time", "timestamp", "datetime", "date", "localtime", "gmttime"},
    "open": {"open", "o"},
    "high": {"high", "h"},
    "low": {"low", "l"},
    "close": {"close", "c"},
    "volume": {"volume", "tickvolume", "vol", "tickvol"},
}


def _key(value: object) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).strip().lower())


def _read_csv(path: Path) -> pd.DataFrame:
    """Read comma, semicolon, or tab-delimited CSV files."""
    return pd.read_csv(
        path,
        sep=None,
        engine="python",
        encoding="utf-8-sig",
    )


def standardize_frame(
    frame: pd.DataFrame,
    source: str = "<dataframe>",
) -> pd.DataFrame:
    """Return a validated UTC-indexed OHLCV DataFrame."""

    lookup = {_key(col): col for col in frame.columns}
    selected: dict[str, str] = {}

    for canonical, aliases in ALIASES.items():
        for alias in aliases:
            if alias in lookup:
                selected[canonical] = lookup[alias]
                break

    required = {"time", "open", "high", "low", "close"}
    missing = sorted(required - selected.keys())

    if missing:
        raise ValueError(
            f"{source}: missing required columns {missing}. "
            f"Available columns: {list(frame.columns)}"
        )

    out = pd.DataFrame()
    raw_time = frame[selected["time"]]

    # Detect numeric Unix timestamps.
    numeric_time = pd.to_numeric(raw_time, errors="coerce")
    numeric_mask = numeric_time.notna()

    out["time"] = pd.to_datetime(
        raw_time,
        errors="coerce",
        utc=True,
    )

    if numeric_mask.any():
        sample = numeric_time[numeric_mask].abs().median()

        if sample >= 1e17:
            unit = "ns"
        elif sample >= 1e11:
            unit = "ms"
        elif sample >= 1e9:
            unit = "s"
        else:
            raise ValueError(
                f"{source}: cannot determine numeric timestamp unit."
            )

        out.loc[numeric_mask, "time"] = pd.to_datetime(
            numeric_time[numeric_mask],
            unit=unit,
            errors="coerce",
            utc=True,
        )

    # Convert OHLC columns to numeric values.
    for column in ("open", "high", "low", "close"):
        out[column] = pd.to_numeric(
            frame[selected[column]],
            errors="coerce",
        )

    if "volume" in selected:
        out["volume"] = pd.to_numeric(
            frame[selected["volume"]],
            errors="coerce",
        )
    else:
        out["volume"] = float("nan")

    # Remove invalid rows and standardize timestamps.
    out = out.dropna(
        subset=["time", "open", "high", "low", "close"]
    )

    out = out.set_index("time").sort_index()
    out = out[~out.index.duplicated(keep="last")]

    # Validate price relationships.
    valid = (
        (out[["open", "high", "low", "close"]] > 0).all(axis=1)
        & (
            out["high"]
            >= out[["open", "low", "close"]].max(axis=1)
        )
        & (
            out["low"]
            <= out[["open", "high", "close"]].min(axis=1)
        )
    )

    out = out.loc[valid]

    return out


def load_yearly_csvs(
    input_dir: str | Path,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Load yearly XAUUSD M5 CSV files and return data and diagnostics."""

    folder = Path(input_dir).expanduser()
    files = sorted(folder.glob("XAUUSD_M5_*.csv"))

    if not files:
        raise FileNotFoundError(
            f"No XAUUSD_M5_YYYY.csv files found in: {folder}"
        )

    frames: list[pd.DataFrame] = []
    raw_rows = 0

    for file in files:
        raw = _read_csv(file)
        raw_rows += len(raw)

        frames.append(
            standardize_frame(raw, str(file))
        )

    combined = pd.concat(frames).sort_index()

    before_dedup = len(combined)
    combined = combined[
        ~combined.index.duplicated(keep="last")
    ]

    duplicates_removed = before_dedup - len(combined)

    # Separate candidate intraday gaps from long market closures.
    deltas = combined.index.to_series().diff()

    candidate_gaps = int(
        (
            (deltas > pd.Timedelta(minutes=5))
            & (deltas <= pd.Timedelta(hours=24))
        ).sum()
    )

    long_closures = int(
        (deltas > pd.Timedelta(hours=24)).sum()
    )

    diagnostics = {
        "files": len(files),
        "raw_rows": raw_rows,
        "valid_rows": len(combined),
        "duplicates_removed_across_files": duplicates_removed,
        "candidate_intraday_gaps": candidate_gaps,
        "closures_over_24h": long_closures,
    }

    return combined, diagnostics


def resample_ohlcv(
    frame: pd.DataFrame,
    timeframe: str = "1h",
) -> pd.DataFrame:
    """Resample OHLCV bars. Source timestamps represent bar open."""

    rule = timeframe.lower()

    agg = {
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum",
    }

    result = frame.resample(
        rule,
        label="left",
        closed="left",
    ).agg(agg)

    return result.dropna(
        subset=["open", "high", "low", "close"]
    )
