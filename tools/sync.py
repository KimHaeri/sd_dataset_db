"""Fill the measured columns from measurements/<dataset_id>.json.

Usage: python3 tools/sync.py

For every row of data/collections.csv: the measured columns of collections.csv are
rewritten, and datasets.*_measured get a `measured` evidence row when their value changes.
Hand-written columns are never touched.
"""

import json

import csvio
import db as dbmod

MEASURED = ["n_sessions", "n_speakers", "speakers_per_session", "speech_hours", "overlap_ratio",
            "audio_hours", "audio_format", "measured_on", "measurement_file"]


def load(dataset_id):
    path = csvio.ROOT / "measurements" / f"{dataset_id}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


def measured(dataset_id):
    """collections.csv measured columns implied by the measurement file (all NA without one)."""
    m = load(dataset_id)
    if m is None:
        return {c: "NA" for c in MEASURED}
    sps = m["speakers_per_session"]
    lo, hi = sps["min"], sps["max"]
    a = m["audio"]

    def s(v):
        return "NA" if v is None else str(v)

    return {
        "n_sessions": str(m["n_sessions"]), "n_speakers": str(m["n_speakers"]),
        "speakers_per_session": "NA" if lo is None else (str(lo) if lo == hi else f"{lo}-{hi}"),
        "speech_hours": str(m["speech_hours"]), "overlap_ratio": s(m["overlap_ratio"]),
        "audio_hours": s(a and a["hours"]),
        "audio_format": "NA" if not a else ";".join(f"{k}:{v}" for k, v in a["format"].items()),
        "measured_on": m["measured_on"], "measurement_file": f"measurements/{dataset_id}.json",
    }


def dataset_values(dataset_id):
    """datasets.*_measured values implied by the measurement file (None = leave the cell)."""
    m = load(dataset_id)
    if m is None:
        return {}
    return {
        "n_sessions_measured": str(m["n_sessions"]),
        "n_speakers_measured": str(m["n_speakers"]),
        "overlap_ratio_measured": "NA" if m["overlap_ratio"] is None else str(m["overlap_ratio"]),
        "hours_measured": str(m["audio"]["hours"]) if m["audio"] else None,
    }


def main():
    db = dbmod.load()
    for row in db["collections"][1]:
        i = row["dataset_id"]
        row.update(measured(i))
        m = load(i)
        for field, value in dataset_values(i).items():
            ds = dbmod.find(db, "datasets", [i])
            if value is None or ds is None or ds[field] == value:
                continue
            dbmod.set_with_evidence(db, i, field, value, "measured", f"measurements/{i}.json",
                                    locator=f"tools/measure.py output of {m['measured_on']}",
                                    via="tools/sync.py", checked_by="script", checked_on=m["measured_on"])
    dbmod.save(db)
    print(f"synced {len(db['collections'][1])} collection row(s)")


if __name__ == "__main__":
    main()
