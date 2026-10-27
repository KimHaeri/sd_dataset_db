"""Check the database for format, type, key, evidence and measurement consistency.

Usage: python3 tools/validate.py [--strict]

Exit status is 1 when any error is found; warnings do not fail the run.
--strict turns the warning about unchecked `seed` evidence into an error.
"""

import datetime
import re
import subprocess
import sys
import unicodedata

import csvio
import db as dbmod
import sync
import views

SLUG = re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$")
TOKENS = {"unknown", "NA", "none"}
# Lower number = stronger evidence.
RANK = {"user": 0, "measured": 1, "primary": 2, "secondary": 3, "seed": 4}

errors = []
warnings = []


def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


def norm_name(s):
    # Accents are dropped, but letters of any script are kept.
    s = unicodedata.normalize("NFKD", s.casefold())
    return re.sub(r"[\W_]", "", "".join(c for c in s if not unicodedata.combining(c)))


# ---- 1. file format -------------------------------------------------------


def check_format(tables, cols):
    for path in sorted(csvio.SCHEMA_DIR.glob("*.csv")):
        check_file_bytes(path, None)
    for name, info in tables.items():
        path = info["path"]
        if not path.is_file():
            err(f"{name}: missing file {path}")
            continue
        try:
            header, rows = csvio.read_rows(path)
        except ValueError as e:
            err(f"{name}: {e}")
            continue
        want = [c["column"] for c in cols[name]]
        if header != want:
            err(f"{name}: header {header} does not match schema/columns.csv {want}")
        check_file_bytes(path, info["keys"], header, rows)
        for i, row in enumerate(rows, 2):
            for c, v in row.items():
                if v != v.strip() or "\n" in v or "\r" in v:
                    err(f"{name} line {i} column {c}: leading/trailing space or newline")


def check_file_bytes(path, keys, header=None, rows=None):
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        err(f"{path.name}: has a BOM")
    if b"\r" in raw:
        err(f"{path.name}: has CR characters")
    if header is None:
        header, rows = csvio.read_rows(path)
    if csvio.format_rows(header, rows, keys).encode("utf-8") != raw:
        err(f"{path.name}: not in canonical form (run tools/db.py fmt)")


# ---- 2. types -------------------------------------------------------------


def check_value(v, ctype, enums):
    """Return an error string or None for a non-null cell."""
    if ctype in ("text", "path"):
        return None
    if ctype == "slug":
        return None if SLUG.match(v) else "not a slug"
    if ctype == "url":
        return None if re.match(r"^https?://\S+$", v) else "not an http(s) URL"
    if ctype == "urllist":
        return None if all(re.match(r"^https?://[^\s;]+$", u) for u in v.split(";")) else "not ;-separated http(s) URLs"
    if ctype == "date":
        try:
            datetime.date.fromisoformat(v)
            return None if re.match(r"^\d{4}-\d{2}-\d{2}$", v) else "not YYYY-MM-DD"
        except ValueError:
            return "not a date"
    if ctype == "int":
        return None if re.match(r"^\d+$", v) else "not an integer"
    if ctype == "float":
        return None if re.match(r"^\d+(\.\d+)?$", v) else "not a number"
    if ctype == "range":
        m = re.match(r"^(\d+)(?:-(\d+))?$", v)
        if not m:
            return "not N or MIN-MAX"
        return None if not m.group(2) or int(m.group(1)) < int(m.group(2)) else "MIN must be below MAX"
    if ctype == "bool":
        return None if v in ("true", "false") else "not true/false"
    if ctype in ("list", "isolist") or ctype.startswith("enumlist:"):
        items = v.split(";")
        if any(not it or it != it.strip() for it in items):
            return "empty or padded list item"
        if len(set(items)) != len(items):
            return "repeated list item"
        if ctype == "isolist" and any(not re.match(r"^[a-z]{3}$", it) for it in items):
            return "not ISO 639-3 codes"
        if ctype.startswith("enumlist:"):
            allowed = enums[ctype.split(":", 1)[1]]
            bad = [it for it in items if it not in allowed]
            if bad:
                return f"not in enum {ctype.split(':', 1)[1]}: {bad}"
        return None
    if ctype.startswith("enum:"):
        name = ctype.split(":", 1)[1]
        return None if v in enums[name] else f"not in enum {name}"
    return f"unknown column type {ctype}"


def cell_error(v, ctype, nulls, enums):
    allowed = set(nulls.split(";")) if nulls != "-" else set()
    if v == "":
        return None if "empty" in allowed else "empty cell not allowed"
    if v in TOKENS and v in allowed:
        return None
    return check_value(v, ctype, enums)


def check_types(tables, cols, db, enums):
    for name in tables:
        for i, row in enumerate(db[name][1], 2):
            for c in cols[name]:
                msg = cell_error(row[c["column"]], c["type"], c["nulls"], enums)
                if msg:
                    err(f"{name} line {i} ({row[tables[name]['keys'][0]]}) {c['column']}={row[c['column']]!r}: {msg}")
    for row in db["datasets"][1]:
        derived = enums["license_spdx"].get(row["license_spdx"], {}).get("derived", "")
        if row["license_class"] != derived:
            err(f"datasets {row['dataset_id']}: license_class {row['license_class']!r} != derived {derived!r}")
        allowed = allowed_tiers(row["license_spdx"])
        if row["license_tier"] and allowed and row["license_tier"] not in allowed:
            err(f"datasets {row['dataset_id']}: license_tier {row['license_tier']!r} does not fit "
                f"license_spdx {row['license_spdx']!r} (allowed: {', '.join(sorted(allowed))})")


def allowed_tiers(spdx):
    """Tiers a licence permits. hold and excluded are always allowed except where noted.

    A permissive licence can still be held or excluded (terms that differ by part, platform terms),
    but ShareAlike or NonCommercial terms can never be train, ND is always excluded and an
    institutional licence is licensed_internal. Empty: no licence recorded, no constraint.
    """
    if not spdx:
        return set()
    if "-ND-" in spdx:
        return {"excluded"}
    if spdx in ("LicenseRef-LDC-member-or-nonmember", "LicenseRef-proprietary-restricted"):
        return {"licensed_internal", "excluded"}
    if "-SA-" in spdx or "-NC-" in spdx or spdx == "LicenseRef-custom-research-only":
        return {"eval", "hold", "excluded"}
    if spdx in ("none_stated", "unknown", "conflicting", "LicenseRef-other"):
        return {"hold", "excluded"}
    return {"train", "hold", "excluded"}


# ---- 3. keys, foreign keys, aliases ---------------------------------------


def check_keys(tables, db):
    for name, info in tables.items():
        seen = set()
        for row in db[name][1]:
            k = tuple(row[c] for c in info["keys"])
            if k in seen:
                err(f"{name}: duplicate key {k}")
            seen.add(k)
    ds = {r["dataset_id"]: r for r in db["datasets"][1]}
    challenges = {r["challenge_id"] for r in db["challenges"][1]}
    for r in db["evidence"][1]:
        if r["dataset_id"] not in ds:
            err(f"evidence {r['evidence_id']}: unknown dataset_id")
        m = re.match(r"^(.+)/([a-z_0-9]+)/(\d{2})$", r["evidence_id"])
        if not m or m.group(1) != r["dataset_id"] or m.group(2) != r["field"]:
            err(f"evidence {r['evidence_id']}: id does not match dataset_id/field/NN")
    for table in ("aliases", "splits", "annotations", "challenge_membership", "collections"):
        for r in db[table][1]:
            if r["dataset_id"] not in ds:
                err(f"{table}: unknown dataset_id {r['dataset_id']}")
    for r in db["challenge_membership"][1]:
        if r["challenge_id"] not in challenges:
            err(f"challenge_membership: unknown challenge_id {r['challenge_id']}")
    for r in db["relations"][1]:
        for c in ("dataset_id", "other_dataset_id"):
            if r[c] not in ds:
                err(f"relations {r['dataset_id']}/{r['relation']}/{r['other_dataset_id']}: unknown {c}")
        if r["dataset_id"] == r["other_dataset_id"]:
            err(f"relations {r['dataset_id']}: relation to itself")
    collected = {d for d, r in ds.items() if r["collection_status"] == "collected"}
    in_coll = {r["dataset_id"] for r in db["collections"][1]}
    for d in sorted(collected - in_coll):
        err(f"datasets {d}: collected but data/collections.csv has no row")
    for d in sorted(in_coll - collected):
        err(f"collections {d}: row exists but collection_status is {ds[d]['collection_status'] if d in ds else '?'}")
    for r in db["datasets"][1]:
        if (r["collection_status"] == "collected") != (r["status_reason_codes"] == "NA"):
            err(f"datasets {r['dataset_id']}: status_reason_codes must be NA exactly when collected")
    owners = {}
    names = []
    for r in db["datasets"][1]:
        names += [(r["dataset_id"], r["dataset_id"]), (r["dataset_id"], r["name"])]
    names += [(r["dataset_id"], r["alias"]) for r in db["aliases"][1]]
    for d, n in names:
        owners.setdefault(norm_name(n), set()).add(d)
    for n, d in owners.items():
        if len(d) > 1:
            err(f"name {n!r} is shared by datasets {sorted(d)}; use relations distinct_from and distinct names")


# ---- 4. evidence ----------------------------------------------------------


def check_evidence(cols, db, strict):
    ev_cols = {c["column"]: c["evidence"] for c in cols["datasets"] if c["evidence"] != "no"}
    ev = {}
    for r in db["evidence"][1]:
        ev.setdefault((r["dataset_id"], r["field"]), []).append(r)
        if r["field"] not in ev_cols:
            err(f"evidence {r['evidence_id']}: field {r['field']} does not take evidence")
        if r["field"].endswith("_measured") and r["source_type"] != "measured":
            err(f"evidence {r['evidence_id']}: *_measured fields need source_type measured")
        if r["field"].endswith("_reported") and r["source_type"] == "measured":
            err(f"evidence {r['evidence_id']}: *_reported fields cannot use measured")
        canon = r["is_canonical"] == "true"
        if canon and r["status"] == "superseded":
            err(f"evidence {r['evidence_id']}: canonical row cannot be superseded")
        if not canon and r["status"] == "current":
            err(f"evidence {r['evidence_id']}: non-canonical row must be superseded or conflicting")
    seeded = set()
    for row in db["datasets"][1]:
        d = row["dataset_id"]
        for field in ev_cols:
            v = row[field]
            # NA cells (status_reason_codes of collected rows, measured counts without a measurement) need none.
            needed = v not in ("", "NA")
            rows = ev.get((d, field), [])
            canon = [r for r in rows if r["is_canonical"] == "true"]
            if not needed:
                if rows and v == "":
                    err(f"evidence {d}/{field}: rows exist but the datasets cell is empty")
                continue
            if len(canon) != 1:
                err(f"evidence {d}/{field}: needs exactly one canonical row, found {len(canon)}")
                continue
            c = canon[0]
            if c["value"] != v:
                err(f"evidence {d}/{field}: canonical value {c['value']!r} != datasets value {v!r}")
            if c["source_type"] == "seed":
                seeded.add(d)
            better = [r for r in rows if r is not c and RANK[r["source_type"]] < RANK[c["source_type"]]]
            if better and not c["note"]:
                err(f"evidence {d}/{field}: canonical row uses a weaker source than another row; note is required")
            if c["status"] == "conflicting" and not any(
                r is not c and r["status"] == "conflicting" for r in rows
            ):
                err(f"evidence {d}/{field}: canonical is conflicting but no other conflicting row exists")
    for d in sorted(r["dataset_id"] for r in db["datasets"][1] if r["collection_status"] == "collected"):
        if d in seeded:
            err(f"datasets {d}: collected, but some values still rest on unchecked seed evidence")
    if seeded:
        (err if strict else warn)(
            f"{len(seeded)} dataset(s) have values resting only on unchecked seed evidence "
            "(see views/needs_verification.csv)")


# ---- 5. measurements -------------------------------------------------------


def check_measurements(db):
    """collections.csv measured columns and datasets.*_measured must match measurements/*.json."""
    ds = {r["dataset_id"]: r for r in db["datasets"][1]}
    for r in db["collections"][1]:
        i = r["dataset_id"]
        for col, want in sync.measured(i).items():
            if r[col] != want:
                err(f"collections {i} {col}: csv {r[col]!r} != measurements {want!r} (run tools/sync.py)")
        for field, want in sync.dataset_values(i).items():
            if want is not None and i in ds and ds[i][field] != want:
                err(f"datasets {i} {field}: {ds[i][field]!r} != measurements {want!r} (run tools/sync.py)")
    have = {r["dataset_id"] for r in db["collections"][1]}
    for f in sorted((csvio.ROOT / "measurements").glob("*.json")):
        if f.stem not in have:
            err(f"measurements/{f.name}: no row in data/collections.csv")


# ---- 6. paths --------------------------------------------------------------


def check_paths(cols, tables, db):
    for name in tables:
        for c in cols[name]:
            if c["type"] != "path":
                continue
            for row in db[name][1]:
                v = row[c["column"]]
                if v in ("", "NA", "unknown", "none"):
                    continue
                if not (csvio.ROOT / v).exists():
                    err(f"{name} {c['column']}={v}: path not found (relative to the repository root)")


LOCAL_PATH = re.compile(r"(?<![\w.])(/home/\w+/|/Users/\w+/|/mnt/\w+|[~]/|[A-Za-z]:\\Users\\)")


def check_no_local_paths():
    """The repository may be public: tracked files must not hold machine-specific paths."""
    res = subprocess.run(["git", "-C", str(csvio.ROOT), "ls-files"], capture_output=True, text=True)
    if res.returncode != 0:
        warn("not a git repository: skipped the machine-specific path check")
        return
    for name in res.stdout.split():
        try:
            text = (csvio.ROOT / name).read_text(encoding="utf-8")
        except (UnicodeDecodeError, FileNotFoundError):
            continue
        for i, line in enumerate(text.splitlines(), 1):
            m = LOCAL_PATH.search(line)
            if m:
                err(f"{name}:{i}: machine-specific path {m.group(0)!r} (use an environment variable name or a relative path)")


def check_views(db):
    for path, text in views.build(db).items():
        f = csvio.ROOT / path
        if not f.exists() or f.read_bytes().decode("utf-8") != text:
            err(f"{path} is out of date: run python3 tools/views.py")


def main(argv):
    strict = "--strict" in argv
    tables = csvio.tables()
    cols = csvio.columns()
    enums = csvio.enums()
    check_format(tables, cols)
    if errors:
        report()
    db = dbmod.load()
    check_types(tables, cols, db, enums)
    check_keys(tables, db)
    check_evidence(cols, db, strict)
    check_paths(cols, tables, db)
    check_measurements(db)
    check_views(db)
    check_no_local_paths()
    report()


def report():
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"{len(errors)} error(s), {len(warnings)} warning(s)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
