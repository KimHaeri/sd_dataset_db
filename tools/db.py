"""Load, edit and re-save the database tables.

Usage:
  python3 tools/db.py fmt                           rewrite every table in canonical form
  python3 tools/db.py get TABLE KEY...              print one row (KEY parts follow the table's key columns)
  python3 tools/db.py set TABLE KEY... COL=VAL...   change cells of one existing row
  python3 tools/db.py add TABLE COL=VAL...          add a row
  python3 tools/db.py ev DATASET FIELD VALUE source_type=... source_ref=... [locator=... via=... note=... checked_by=...]
                                                    set a datasets cell together with its evidence row
  python3 tools/db.py clear DATASET FIELD reason=...
                                                    empty a datasets cell whose value was simply wrong

`ev` makes the new row canonical, marks the previous canonical row superseded and
updates datasets.last_updated_on. `clear` keeps the evidence rows: the canonical one
becomes superseded and its note records the reason. After any change, run tools/validate.py.
"""

import datetime
import sys

import csvio


def load():
    """Return {table: (header, rows)} for every table in schema/tables.csv."""
    out = {}
    for name, info in csvio.tables().items():
        header, rows = csvio.read_rows(info["path"])
        out[name] = (header, rows)
    return out


def save(db):
    for name, info in csvio.tables().items():
        header, rows = db[name]
        csvio.write_rows(info["path"], header, rows, info["keys"])


def find(db, table, key):
    keys = csvio.tables()[table]["keys"]
    if len(key) != len(keys):
        sys.exit(f"{table} key needs {len(keys)} part(s): {keys}")
    for row in db[table][1]:
        if all(row[k] == v for k, v in zip(keys, key)):
            return row
    return None


def parse_assignments(items):
    out = {}
    for it in items:
        col, sep, val = it.partition("=")
        if not sep:
            sys.exit(f"expected COL=VAL, got {it!r}")
        out[col] = val
    return out


def set_with_evidence(db, dataset_id, field, value, source_type, source_ref, locator="", via="",
                      note="", checked_by="claude", checked_on=None):
    """Set datasets[dataset_id][field] and add a canonical evidence row; supersede the old one."""
    today = checked_on or datetime.date.today().isoformat()
    row = find(db, "datasets", [dataset_id])
    if row is None:
        sys.exit(f"no dataset {dataset_id}")
    if field not in row:
        sys.exit(f"unknown column {field}")
    ev = db["evidence"][1]
    mine = [e for e in ev if e["dataset_id"] == dataset_id and e["field"] == field]
    for e in mine:
        if e["is_canonical"] == "true":
            e["is_canonical"] = "false"
            if e["status"] == "current":
                e["status"] = "superseded"
    n = max([int(e["evidence_id"].rsplit("/", 1)[1]) for e in mine] + [0]) + 1
    ev.append({
        "evidence_id": f"{dataset_id}/{field}/{n:02d}", "dataset_id": dataset_id, "field": field,
        "value": value, "source_type": source_type, "source_ref": source_ref, "locator": locator,
        "via": via, "checked_on": today, "checked_by": checked_by, "is_canonical": "true",
        "status": "current", "note": note,
    })
    row[field] = value
    if field == "license_spdx":
        row["license_class"] = csvio.enums()["license_spdx"].get(value, {}).get("derived", "")
    row["last_updated_on"] = today


def clear_with_evidence(db, dataset_id, field, reason, checked_on=None):
    """Empty datasets[dataset_id][field]; supersede its canonical evidence row and record why."""
    today = checked_on or datetime.date.today().isoformat()
    row = find(db, "datasets", [dataset_id])
    if row is None:
        sys.exit(f"no dataset {dataset_id}")
    if field not in row:
        sys.exit(f"unknown column {field}")
    canon = [e for e in db["evidence"][1]
             if e["dataset_id"] == dataset_id and e["field"] == field and e["is_canonical"] == "true"]
    if not canon:
        sys.exit(f"{dataset_id}/{field} has no canonical evidence row to withdraw")
    for e in canon:
        e["is_canonical"] = "false"
        e["status"] = "superseded"
        withdrawn = f"Withdrawn {today}: {reason}"
        e["note"] = f"{e['note']} {withdrawn}" if e["note"] else withdrawn
    row[field] = ""
    if field == "license_spdx":
        row["license_class"] = ""
    row["last_updated_on"] = today


def main(argv):
    if not argv:
        sys.exit(__doc__)
    cmd, args = argv[0], argv[1:]
    db = load()
    if cmd == "fmt":
        save(db)
    elif cmd in ("get", "set"):
        table = args[0]
        nkeys = len(csvio.tables()[table]["keys"])
        row = find(db, table, args[1 : 1 + nkeys])
        if row is None:
            sys.exit("no such row")
        if cmd == "get":
            for k, v in row.items():
                print(f"{k}: {v}")
        else:
            changes = parse_assignments(args[1 + nkeys :])
            bad = set(changes) - set(row)
            if bad:
                sys.exit(f"unknown column(s): {sorted(bad)}")
            row.update(changes)
            save(db)
    elif cmd == "add":
        table = args[0]
        header, rows = db[table]
        new = {c: "" for c in header}
        changes = parse_assignments(args[1:])
        bad = set(changes) - set(header)
        if bad:
            sys.exit(f"unknown column(s): {sorted(bad)}")
        new.update(changes)
        rows.append(new)
        save(db)
    elif cmd == "ev":
        if len(args) < 3:
            sys.exit(__doc__)
        opts = parse_assignments(args[3:])
        for req in ("source_type", "source_ref"):
            if req not in opts:
                sys.exit(f"ev needs {req}=...")
        set_with_evidence(db, args[0], args[1], args[2], **opts)
        save(db)
    elif cmd == "clear":
        if len(args) < 2:
            sys.exit(__doc__)
        opts = parse_assignments(args[2:])
        if not opts.get("reason"):
            sys.exit("clear needs reason=...")
        clear_with_evidence(db, args[0], args[1], opts["reason"])
        save(db)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
