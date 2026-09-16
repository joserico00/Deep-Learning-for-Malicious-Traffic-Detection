"""Stream selected IoT-23 connection fields into one optional CSV file.

The canonical notebook reads capture files directly, so merging is not required.
This utility exists for tools that need one table and avoids loading the full
dataset into memory. It reads the Zeek logs the dataset ships (`*conn.log.labeled`)
and converted CSV exports (`*conn.log.labeled.csv`) alike.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from iot23 import capture_name, find_capture_files, read_connection_log


NUMERIC_FEATURES = [
    "id.orig_p",
    "id.resp_p",
    "duration",
    "orig_bytes",
    "resp_bytes",
    "missed_bytes",
    "orig_pkts",
    "orig_ip_bytes",
    "resp_pkts",
    "resp_ip_bytes",
]
CATEGORICAL_FEATURES = ["proto", "service", "conn_state", "history"]
OUTPUT_COLUMNS = NUMERIC_FEATURES + CATEGORICAL_FEATURES + ["label", "capture_id"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_dir", type=Path, help="Directory containing IoT-23 connection logs")
    parser.add_argument("output_csv", type=Path, help="Destination CSV file")
    parser.add_argument("--chunk-size", type=int, default=250_000, help="Rows processed at once")
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing output file")
    return parser.parse_args()


def select_columns(chunk: pd.DataFrame, path: Path) -> pd.DataFrame:
    chunk.columns = chunk.columns.str.strip()
    if "label" not in chunk.columns:
        raise ValueError(f"{path.name} has no 'label' column")

    normalized_label = chunk["label"].astype("string").str.strip().str.split().str[0].str.title()
    valid = normalized_label.isin(["Benign", "Malicious"])
    chunk = chunk.loc[valid].copy()
    chunk["label"] = normalized_label.loc[valid].map({"Benign": 0, "Malicious": 1}).astype("int8")
    chunk["capture_id"] = capture_name(path)

    for column in NUMERIC_FEATURES + CATEGORICAL_FEATURES:
        if column not in chunk.columns:
            chunk[column] = np.nan
    return chunk[OUTPUT_COLUMNS]


def main() -> None:
    args = parse_args()
    input_dir = args.input_dir.expanduser().resolve()
    output_csv = args.output_csv.expanduser().resolve()
    paths = [path for path in find_capture_files(input_dir) if path.resolve() != output_csv]
    if not paths:
        raise SystemExit(f"No *conn.log.labeled or *conn.log.labeled.csv files found under {input_dir}")
    if output_csv.exists() and not args.overwrite:
        raise SystemExit(f"Output already exists: {output_csv}. Pass --overwrite to replace it.")

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    if output_csv.exists():
        output_csv.unlink()

    rows_written = 0
    write_header = True
    for path in paths:
        capture_rows = 0
        for chunk in read_connection_log(path, chunksize=args.chunk_size):
            selected = select_columns(chunk, path)
            selected.to_csv(output_csv, mode="a", header=write_header, index=False)
            write_header = False
            capture_rows += len(selected)
            rows_written += len(selected)
        print(f"{path.name}: {capture_rows:,} rows")

    print(f"Wrote {rows_written:,} rows to {output_csv}")


if __name__ == "__main__":
    main()
