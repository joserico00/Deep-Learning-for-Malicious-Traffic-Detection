"""Offline checks for the IoT-23 loader.

No dataset needed: each check writes a small capture in one of the formats the dataset is
distributed in, so a change in the parsing fails here rather than in the notebook.

Run:  python tests/test_iot23.py
"""
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import pandas as pd

from iot23 import capture_name, find_capture_files, read_connection_log, sniff_separator, zeek_directives

ok = 0


def check(label, condition):
    global ok
    assert condition, f"FAILED: {label}"
    ok += 1
    print(f"  ok  {label}")


FIELDS = [
    "ts", "uid", "id.orig_h", "id.orig_p", "id.resp_h", "id.resp_p", "proto", "service",
    "duration", "orig_bytes", "resp_bytes", "conn_state", "local_orig", "local_resp",
    "missed_bytes", "history", "orig_pkts", "orig_ip_bytes", "resp_pkts", "resp_ip_bytes",
]
ROWS = [
    ["1553..1", "Cabc", "192.168.1.1", "42", "8.8.8.8", "53", "udp", "dns",
     "0.01", "40", "80", "SF", "-", "-", "0", "Dd", "1", "68", "1", "108"],
    ["1553..2", "Cdef", "192.168.1.1", "43", "10.0.0.9", "23", "tcp", "-",
     "-", "-", "-", "S0", "-", "-", "0", "S", "1", "60", "0", "0"],
]
LABELS = [("-", "Benign", "-"), ("-", "Malicious", "PartOfAHorizontalPortScan")]


def write_zeek_log(path):
    """The format Stratosphere ships: tab separated, # directives, spaces before the label fields."""
    header = [
        "#separator \\x09",
        "#set_separator\t,",
        "#empty_field\t(empty)",
        "#unset_field\t-",
        "#path\tconn",
        "#fields\t" + "\t".join(FIELDS) + "\ttunnel_parents   label   detailed-label",
        "#types\ttime\tstring\taddr\tport\taddr\tport\tenum\tstring\tinterval\tcount\tcount\tstring"
        "\tbool\tbool\tcount\tstring\tcount\tcount\tcount\tcount",
    ]
    body = ["\t".join(row) + "\t" + "   ".join(label) for row, label in zip(ROWS, LABELS)]
    path.write_text("\n".join(header + body + ["#close\t2019-01-01-00-00-00", ""]), encoding="utf-8")


def write_converted_csv(path, separator):
    """A converted export: one header row, one delimiter, the label fields already split."""
    columns = FIELDS + ["tunnel_parents", "label", "detailed-label"]
    lines = [separator.join(columns)]
    lines += [separator.join(list(row) + list(label)) for row, label in zip(ROWS, LABELS)]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    zeek = root / "CTU-IoT-Malware-Capture-1-1conn.log.labeled"
    piped = root / "nested" / "CTU-IoT-Malware-Capture-3-1conn.log.labeled.csv"
    comma = root / "CTU-IoT-Malware-Capture-8-1conn.log.labeled.csv"
    piped.parent.mkdir()
    write_zeek_log(zeek)
    write_converted_csv(piped, "|")
    write_converted_csv(comma, ",")

    print("discovery")
    found = find_capture_files(root)
    check("both dataset formats are found, including nested folders", found == sorted([zeek, comma, piped]))
    check("capture names come from the file name",
          sorted(capture_name(path) for path in found) ==
          ["CTU-IoT-Malware-Capture-1-1", "CTU-IoT-Malware-Capture-3-1", "CTU-IoT-Malware-Capture-8-1"])

    print("Zeek connection logs")
    directives = zeek_directives(zeek)
    check("the # header is parsed", directives["separator"] == "\t" and directives["unset_field"] == ["-"])
    check("a converted export has no Zeek header", zeek_directives(piped) is None)
    frame = read_connection_log(zeek)
    check("every declared field becomes a column, including the space-separated label fields",
          list(frame.columns) == FIELDS + ["tunnel_parents", "label", "detailed-label"])
    check("labels are recovered from the merged column", list(frame["label"]) == ["Benign", "Malicious"])
    check("detailed labels are recovered, with the unset marker read as missing",
          list(frame["detailed-label"].fillna("-")) == ["-", "PartOfAHorizontalPortScan"]
          and pd.isna(frame.loc[0, "detailed-label"]) and frame["tunnel_parents"].isna().all())
    check("unset fields become missing values", pd.isna(frame.loc[1, "duration"]) and frame.loc[0, "duration"] == 0.01)
    check("numeric columns are numeric", frame["orig_ip_bytes"].tolist() == [68, 60])

    print("converted exports")
    check("the delimiter is detected", sniff_separator(piped) == "|" and sniff_separator(comma) == ",")
    for path in (piped, comma):
        other = read_connection_log(path)
        check(f"{path.suffix} export parses to the same values as the Zeek log ({sniff_separator(path)!r})",
              other[["label", "proto", "orig_ip_bytes"]].equals(frame[["label", "proto", "orig_ip_bytes"]]))

    print("chunked reading")
    chunks = list(read_connection_log(zeek, chunksize=1))
    check("chunks carry the same columns and rows", len(chunks) == 2
          and list(chunks[0]["label"]) == ["Benign"] and list(chunks[1]["label"]) == ["Malicious"])

    print("merge script")
    output = root / "merged.csv"
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "merge_csv_datasets.py"), str(root), str(output)],
        capture_output=True, text=True)
    check("the merge script runs over both formats", result.returncode == 0, )
    merged = pd.read_csv(output)
    check("it writes one row per usable connection from every capture", len(merged) == 6
          and sorted(merged["capture_id"].unique()) == ["CTU-IoT-Malware-Capture-1-1",
                                                        "CTU-IoT-Malware-Capture-3-1",
                                                        "CTU-IoT-Malware-Capture-8-1"])
    check("labels are mapped to 0 and 1", sorted(merged["label"].unique().tolist()) == [0, 1])

print(f"\nAll {ok} checks passed.")
