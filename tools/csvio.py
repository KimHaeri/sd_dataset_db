"""Canonical CSV reading and writing for the speaker diarization dataset database.

Every file under data/, schema/ and views/ is written only through this module,
so a file that was written by hand shows up as a byte difference in validate.py.
Canonical form: UTF-8 without BOM, LF line ends, minimal quoting, rows sorted
by the table's key columns, no trailing newline-less last line.
"""

import csv
import io
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = ROOT / "schema"


def parse(text):
    """Return (header, rows) where rows is a list of dicts."""
    reader = csv.reader(io.StringIO(text, newline=""))
    records = list(reader)
    if not records:
        return [], []
    header = records[0]
    rows = []
    for rec in records[1:]:
        if len(rec) != len(header):
            raise ValueError(f"row has {len(rec)} cells, header has {len(header)}: {rec[:3]}")
        rows.append(dict(zip(header, rec)))
    return header, rows


def read_rows(path):
    return parse(Path(path).read_bytes().decode("utf-8"))


def format_rows(header, rows, key_columns=None):
    """Serialize rows in canonical form (sorted by key columns when given)."""
    if key_columns:
        rows = sorted(rows, key=lambda r: tuple(r[k] for k in key_columns))
    buf = io.StringIO(newline="")
    writer = csv.writer(buf, lineterminator="\n", quoting=csv.QUOTE_MINIMAL)
    writer.writerow(header)
    for row in rows:
        writer.writerow([row.get(c, "") for c in header])
    return buf.getvalue()


def write_rows(path, header, rows, key_columns=None):
    Path(path).write_bytes(format_rows(header, rows, key_columns).encode("utf-8"))


def tables():
    """Return {table: {"path", "keys", "description"}} from schema/tables.csv."""
    _, rows = read_rows(SCHEMA_DIR / "tables.csv")
    return {
        r["table"]: {
            "path": ROOT / r["path"],
            "keys": r["key_columns"].split(";"),
            "description": r["description"],
        }
        for r in rows
    }


def columns():
    """Return {table: [column dict, ...]} in header order from schema/columns.csv."""
    _, rows = read_rows(SCHEMA_DIR / "columns.csv")
    out = {}
    for r in rows:
        out.setdefault(r["table"], []).append(r)
    return out


def enums():
    """Return {enum_name: {value: row}} from schema/enums.csv."""
    _, rows = read_rows(SCHEMA_DIR / "enums.csv")
    out = {}
    for r in rows:
        out.setdefault(r["enum"], {})[r["value"]] = r
    return out
