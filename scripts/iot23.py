"""Read IoT-23 connection logs in either the format the dataset ships or a converted CSV export.

Stratosphere publishes IoT-23 as Zeek logs named `*conn.log.labeled`: tab separated, preceded by
`#` directive lines, and with `tunnel_parents`, `label` and `detailed-label` written as one
space-separated field instead of the three tab-separated fields the header declares. Public
conversions of the same captures are plain `*conn.log.labeled.csv` tables, usually pipe separated.

Both are accepted here, so the notebook and the merge script work with either download.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

NA_VALUES = ["-", "(empty)", "?", "NA", "null"]
CAPTURE_PATTERNS = ("*conn.log.labeled", "*conn.log.labeled.csv")
LABEL_FIELDS = ("tunnel_parents", "label", "detailed-label")
CANDIDATE_SEPARATORS = ("|", ",", "\t", ";")


def find_capture_files(directory) -> list[Path]:
    """Every IoT-23 connection log under `directory`, in either format, sorted by path."""
    directory = Path(directory)
    paths = {path for pattern in CAPTURE_PATTERNS for path in directory.rglob(pattern) if path.is_file()}
    return sorted(paths)


def capture_name(path) -> str:
    """`CTU-IoT-Malware-Capture-1-1` from `.../CTU-IoT-Malware-Capture-1-1conn.log.labeled.csv`."""
    path = Path(path)
    return path.name.split("conn.log")[0].rstrip("-_.") or path.parent.name


def zeek_directives(path: Path) -> dict | None:
    """The `#` header of a Zeek log as {directive: [values]}, or None for a plain table."""
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        first_line = handle.readline()
        if not first_line.startswith("#separator"):
            return None
        # e.g. "#separator \x09" -> a tab
        separator = first_line.split(None, 1)[1].strip().encode().decode("unicode_escape")
        directives = {"separator": separator}
        for line in handle:
            if not line.startswith("#"):
                break
            name, *values = line[1:].rstrip("\n").split(separator)
            directives[name] = values
    return directives


def sniff_separator(path: Path) -> str:
    """The delimiter of a converted export, guessed from its header line."""
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        header = handle.readline()
    return max(CANDIDATE_SEPARATORS, key=header.count)


def _split_merged_labels(frame: pd.DataFrame) -> pd.DataFrame:
    """Recover `label` and `detailed-label` when the three trailing fields arrived as one column."""
    if "label" not in frame.columns or "tunnel_parents" not in frame.columns:
        return frame
    if frame["label"].notna().any():
        return frame
    parts = frame["tunnel_parents"].astype("string").str.strip().str.split(r"\s+", n=2, expand=True)
    for position, field in enumerate(LABEL_FIELDS):
        if field in frame.columns and position < parts.shape[1]:
            values = parts[position]
            # the split happens after parsing, so apply the unset markers here as read_csv would
            frame[field] = values.astype(object).where(values.notna() & ~values.isin(NA_VALUES), np.nan)
    return frame


def _tidy(frame: pd.DataFrame) -> pd.DataFrame:
    frame.columns = [str(column).strip() for column in frame.columns]
    return _split_merged_labels(frame)


def read_connection_log(path, chunksize: int | None = None):
    """One capture as a DataFrame, or an iterator of DataFrames when `chunksize` is given."""
    path = Path(path)
    directives = zeek_directives(path)
    if directives is None:
        reader = pd.read_csv(
            path,
            sep=sniff_separator(path),
            na_values=NA_VALUES,
            low_memory=False,
            chunksize=chunksize,
        )
    else:
        # IoT-23 packs the last three field names into one header entry, so split on whitespace.
        fields = [name for entry in directives.get("fields", []) for name in entry.split()]
        if not fields:
            raise ValueError(f"{path.name} has a Zeek header without a #fields line")
        na_values = sorted({*NA_VALUES, *directives.get("unset_field", []), *directives.get("empty_field", [])})
        reader = pd.read_csv(
            path,
            sep=directives["separator"],
            names=fields,
            comment="#",
            na_values=na_values,
            low_memory=False,
            chunksize=chunksize,
        )
    if chunksize:
        return (_tidy(chunk) for chunk in reader)
    return _tidy(reader)
