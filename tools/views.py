"""Generate the files under views/ from data/.

Usage: python3 tools/views.py      (rewrite every view)
validate.py regenerates them in memory and fails if the files on disk differ.

- views/datasets_wide.csv       one row per dataset with the main columns and joined facts
- views/discrepancies.csv       evidence that disagrees with the canonical value; reported vs measured
- views/needs_verification.csv  canonical values that rest only on unchecked `seed` evidence
"""

import csvio
import db as dbmod

WIDE_COLS = [
    "dataset_id", "name", "collection_status", "status_reason_codes", "languages", "domain", "speech_style",
    "recording_setup", "modality", "license_spdx", "license_class", "access_method", "raw_audio_available",
    "hours_reported", "n_sessions_reported", "n_speakers_reported", "speakers_per_session_reported",
    "overlap_ratio_reported", "annotation_format", "annotation_method", "has_transcript", "has_official_splits",
    "hours_measured", "n_sessions_measured", "n_speakers_measured", "overlap_ratio_measured",
    "splits", "challenges", "annotation_items", "aliases", "relations", "source_url", "paper_url",
    "status_note", "notes", "n_seed_values", "license_source_type", "license_checked_on",
    "oldest_checked_on", "latest_checked_on",
]
DISC_COLS = ["dataset_id", "field", "kind", "datasets_value", "datasets_source_type", "other_value",
             "other_source_type", "other_source_ref", "note"]
DISC_KEYS = ("dataset_id", "field", "kind", "other_value", "other_source_ref")
VERIFY_COLS = ["dataset_id", "field", "value", "evidence_id", "checked_on"]
PAIRS = [("hours_reported", "hours_measured"), ("n_sessions_reported", "n_sessions_measured"),
         ("n_speakers_reported", "n_speakers_measured"), ("overlap_ratio_reported", "overlap_ratio_measured")]


def canonical(db):
    out = {}
    for e in db["evidence"][1]:
        if e["is_canonical"] == "true":
            out.setdefault(e["dataset_id"], {})[e["field"]] = e
    return out


def grouped(rows, fmt):
    out = {}
    for r in rows:
        out.setdefault(r["dataset_id"], []).append(fmt(r))
    return {k: ";".join(sorted(v)) for k, v in out.items()}


def wide(db):
    canon = canonical(db)
    splits = grouped(db["splits"][1], lambda r: r["split"])
    chal = grouped(db["challenge_membership"][1], lambda r: f"{r['challenge_id']}:{r['role']}")
    items = grouped(db["annotations"][1], lambda r: r["item"])
    aliases = grouped(db["aliases"][1], lambda r: r["alias"])
    rels = grouped(db["relations"][1], lambda r: f"{r['relation']}:{r['other_dataset_id']}")
    out = []
    for d in db["datasets"][1]:
        i = d["dataset_id"]
        ce = canon.get(i, {})
        lic = ce.get("license_spdx")
        dates = sorted(e["checked_on"] for e in ce.values())
        row = {c: d.get(c, "") for c in WIDE_COLS}
        row.update({
            "splits": splits.get(i, ""), "challenges": chal.get(i, ""), "annotation_items": items.get(i, ""),
            "aliases": aliases.get(i, ""), "relations": rels.get(i, ""),
            "n_seed_values": str(sum(e["source_type"] == "seed" for e in ce.values())),
            "license_source_type": lic["source_type"] if lic else "",
            "license_checked_on": lic["checked_on"] if lic else "",
            "oldest_checked_on": dates[0] if dates else "", "latest_checked_on": dates[-1] if dates else "",
        })
        out.append(row)
    return out


def discrepancies(db):
    ev = db["evidence"][1]
    canon = {(e["dataset_id"], e["field"]): e for e in ev if e["is_canonical"] == "true"}
    out = []
    for e in ev:
        if e["is_canonical"] == "true":
            continue
        c = canon.get((e["dataset_id"], e["field"]))
        if c is None or e["value"] in (c["value"], "unknown"):
            continue
        # A status that moved on is history, not a disagreement.
        if e["field"] in ("collection_status", "status_reason_codes") and e["status"] == "superseded":
            continue
        out.append({"dataset_id": e["dataset_id"], "field": e["field"], "kind": e["status"],
                    "datasets_value": c["value"], "datasets_source_type": c["source_type"], "other_value": e["value"],
                    "other_source_type": e["source_type"], "other_source_ref": e["source_ref"], "note": e["note"]})
    for d in db["datasets"][1]:
        for a, b in PAIRS:
            try:
                x, y = float(d[a]), float(d[b])
            except ValueError:
                continue
            if abs(x - y) > max(0.01 * x, 0.01):
                out.append({"dataset_id": d["dataset_id"], "field": f"{a} vs {b}", "kind": "reported_vs_measured",
                            "datasets_value": d[a], "datasets_source_type": "see evidence", "other_value": d[b],
                            "other_source_type": "measured", "other_source_ref": f"measurements/{d['dataset_id']}.json",
                            "note": "the release we obtained or the RTTM version may differ from the paper"})
    return out


def needs_verification(db):
    return [{"dataset_id": e["dataset_id"], "field": e["field"], "value": e["value"],
             "evidence_id": e["evidence_id"], "checked_on": e["checked_on"]}
            for e in db["evidence"][1] if e["is_canonical"] == "true" and e["source_type"] == "seed"]


def build(db):
    """Return {relative path: canonical file text}."""
    return {
        "views/datasets_wide.csv": csvio.format_rows(WIDE_COLS, wide(db), ("dataset_id",)),
        "views/discrepancies.csv": csvio.format_rows(DISC_COLS, discrepancies(db), DISC_KEYS),
        "views/needs_verification.csv": csvio.format_rows(VERIFY_COLS, needs_verification(db), ("dataset_id", "field")),
    }


def main():
    for path, text in build(dbmod.load()).items():
        (csvio.ROOT / path).write_bytes(text.encode("utf-8"))
        print("wrote", path, text.count("\n") - 1, "rows")


if __name__ == "__main__":
    main()
