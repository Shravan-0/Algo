"""Combine yearly Dukascopy XAUUSD M5 CSV files into a local Parquet dataset."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.main.data import load_yearly_csvs  # noqa: E402


def load_config() -> dict:
    with (ROOT / "config.yaml").open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def main() -> None:
    config = load_config()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-dir",
        default=os.getenv("XAUUSD_M5_DIR", config["data"]["input_dir"]),
        help="Folder containing XAUUSD_M5_YYYY.csv files",
    )
    parser.add_argument(
        "--output",
        default=str(ROOT / config["data"]["output_file"]),
        help="Output Parquet path (kept out of Git by .gitignore)",
    )
    args = parser.parse_args()

    data, diagnostics = load_yearly_csvs(args.input_dir)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    data.to_parquet(output, index=True)

    print("Dataset build complete")
    print(f"Files loaded: {diagnostics['files']}")
    print(f"Raw rows: {diagnostics['raw_rows']:,}")
    print(f"Valid rows: {diagnostics['valid_rows']:,}")
    print(f"Duplicates removed across files: {diagnostics['duplicates_removed_across_files']:,}")
    print(f"Candidate intraday gaps (>5 min and <=24 h): {diagnostics['candidate_intraday_gaps']:,}")
    print(f"Closures longer than 24 h: {diagnostics['closures_over_24h']:,}")
    print(f"Date range (UTC): {data.index.min()} to {data.index.max()}")
    print(f"Saved: {output}")


if __name__ == "__main__":
    main()
