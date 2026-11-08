"""Generate the files under views/ from data/.

Usage: python3 tools/views.py      (rewrite every view)
validate.py regenerates them in memory and fails if the files on disk differ.

- views/datasets_wide.csv       one row per dataset with the main columns and joined facts
- views/discrepancies.csv       evidence that disagrees with the canonical value; reported vs measured
- views/usable_hours.csv         training / evaluation hours per dataset, from usable_as, hours and splits
- views/usable_hours.md          the same summed up: what can train, what can evaluate, what is on the lab storage
- views/needs_verification.csv  canonical values that rest only on unchecked evidence: `seed`, or
                                `secondary` (survey leads, mirrors, recipes) with no primary or stronger row
"""

import csvio
import db as dbmod

WIDE_COLS = [
    "dataset_id", "name", "collection_status", "status_reason_codes", "languages", "domain", "speech_style",
    "recording_setup", "modality", "license_spdx", "license_class", "license_tier", "access_method", "raw_audio_available",
    "hours_reported", "n_sessions_reported", "n_speakers_reported", "speakers_per_session_reported",
    "overlap_ratio_reported", "annotation_format", "annotation_method", "turn_source", "usable_as", "has_transcript", "has_official_splits",
    "hours_measured", "n_sessions_measured", "n_speakers_measured", "overlap_ratio_measured",
    "splits", "challenges", "annotation_items", "aliases", "relations", "source_url", "paper_url",
    "status_note", "notes", "n_seed_values", "license_source_type", "license_checked_on",
    "oldest_checked_on", "latest_checked_on",
]
DISC_COLS = ["dataset_id", "field", "kind", "datasets_value", "datasets_source_type", "other_value",
             "other_source_type", "other_source_ref", "note"]
DISC_KEYS = ("dataset_id", "field", "kind", "other_value", "other_source_ref")
VERIFY_COLS = ["dataset_id", "field", "value", "source_type", "evidence_id", "checked_on"]
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
    return [{"dataset_id": e["dataset_id"], "field": e["field"], "value": e["value"], "source_type": e["source_type"],
             "evidence_id": e["evidence_id"], "checked_on": e["checked_on"]}
            for e in db["evidence"][1] if e["is_canonical"] == "true" and e["source_type"] in ("seed", "secondary")]


HOURS_COLS = ["dataset_id", "name", "usable_as", "license_tier", "on_lab_storage", "train_hours", "eval_hours",
              "unsplit_hours", "basis"]


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def on_lab(d):
    if d["collection_status"] == "collected" or "lab_copy_available" in d["status_reason_codes"]:
        return "yes"
    if "not on the lab" in d["status_note"].lower():
        return "no"
    return "unknown"


def usable_hours(db):
    """Split each usable dataset's hours into training and evaluation hours.

    train: all hours train; conditions marked "Used"/"Not used" in splits.csv keep only the used share.
    train_split: train splits train, the other splits evaluate (eval_splits_only: only the evaluation part counts); when split hours are missing, use total minus
    train, or the share of sessions; otherwise the hours stay unsplit. eval: all hours evaluate.
    """
    splits = {}
    for r in db["splits"][1]:
        splits.setdefault(r["dataset_id"], []).append(r)
    out = []
    for d in db["datasets"][1]:
        use = d["usable_as"]
        if use not in ("train", "train_split", "eval", "eval_splits_only"):
            continue
        total = _num(d["hours_reported"])
        rows = splits.get(d["dataset_id"], [])
        cond = [r for r in rows if r["note"].startswith(("Used", "Not used"))]
        parts = [r for r in rows if r not in cond]
        train = ev = unsplit = None
        basis = "reported" if total is not None else "no hours recorded"
        if cond and total is not None:
            used = sum(_num(r["n_sessions_reported"]) or 0 for r in cond if r["note"].startswith("Used"))
            alls = sum(_num(r["n_sessions_reported"]) or 0 for r in cond)
            if alls:
                total = total * used / alls
                basis = "derived: used conditions' share of sessions"
        if use == "train":
            train = total
        elif use == "eval":
            ev = total if total is not None else (sum(_num(r["hours_reported"]) for r in parts)
                                                  if parts and all(_num(r["hours_reported"]) is not None for r in parts) else None)
            if total is None and ev is not None:
                basis = "split hours summed"
        else:  # train_split, eval_splits_only
            tr = [r for r in parts if "train" in r["split"] or "fine" in r["split"]]
            te = [r for r in parts if r not in tr]
            if tr and all(_num(r["hours_reported"]) is not None for r in parts):
                train = sum(_num(r["hours_reported"]) for r in tr)
                ev = sum(_num(r["hours_reported"]) for r in te)
                basis = "split hours"
            elif tr and total is not None and all(_num(r["hours_reported"]) is not None for r in tr):
                train = sum(_num(r["hours_reported"]) for r in tr)
                ev = max(total - train, 0.0)
                basis = "derived: total minus train split"
            elif tr and total is not None and all(_num(r["n_sessions_reported"]) is not None for r in parts):
                n_tr = sum(_num(r["n_sessions_reported"]) for r in tr)
                n_all = sum(_num(r["n_sessions_reported"]) for r in parts)
                train = total * n_tr / n_all
                ev = total - train
                basis = "derived: share of sessions"
            else:
                unsplit = total if use == "train_split" else None
                if total is not None:
                    basis = "reported total; split hours not recorded"
            if use == "eval_splits_only":
                train = None
        fmt = lambda x: "" if x is None else f"{x:.2f}"
        out.append({"dataset_id": d["dataset_id"], "name": d["name"], "usable_as": use, "license_tier": d["license_tier"],
                    "on_lab_storage": on_lab(d), "train_hours": fmt(train), "eval_hours": fmt(ev),
                    "unsplit_hours": fmt(unsplit), "basis": basis})
    return out


def usable_hours_md(rows, db):
    groups = [("Training, permissive licence", lambda r: r["license_tier"] == "train", "train_hours"),
              ("Training, signed agreement (internal only; LDC training is on hold for review)", lambda r: r["license_tier"] == "licensed_internal", "train_hours"),
              ("Evaluation (all licences)", lambda r: True, "eval_hours")]
    lab = ("yes", "no", "unknown")
    lines = ["# Usable hours", "",
             "Generated by `tools/views.py` from `usable_as`, `hours_reported` and `data/splits.csv`; do not edit. "
             "Hours are recording hours as stated by the sources (speech-only hours are lower); \"derived\" rows are "
             "computed from session shares or totals (see `views/usable_hours.csv`, column `basis`). Survey leads and "
             "datasets on hold are not counted.", "",
             "| | On the lab storage | Not on the lab storage | Storage not checked | Total |", "|---|---|---|---|---|"]
    for title, keep, col in groups:
        vals = [sum(_num(r[col]) or 0 for r in rows if keep(r) and r["on_lab_storage"] == s) for s in lab]
        lines.append(f"| {title} | {vals[0]:,.0f} h | {vals[1]:,.0f} h | {vals[2]:,.0f} h | **{sum(vals):,.0f} h** |")
    uns = [r for r in rows if r["unsplit_hours"]]
    nohours = [r for r in rows if not (r["train_hours"] or r["eval_hours"] or r["unsplit_hours"])]
    lines += ["", f"Not in the table: {sum(_num(r['unsplit_hours']) for r in uns):,.0f} h in {len(uns)} datasets whose "
              "train/evaluation split hours are not recorded (" + ", ".join(f"`{r['dataset_id']}`" for r in uns) + "), and "
              f"{len(nohours)} usable datasets with no hours recorded (" + ", ".join(f"`{r['dataset_id']}`" for r in nohours) + ").", ""]
    for title, keep, col in groups:
        sel = sorted((r for r in rows if keep(r) and _num(r[col])), key=lambda r: -_num(r[col]))
        if not sel:
            continue
        lines += [f"## {title}", "", "| Dataset | Hours | On the lab storage | Basis |", "|---|---|---|---|"]
        lines += [f"| `{r['dataset_id']}` | {_num(r[col]):,.1f} | {r['on_lab_storage']} | {r['basis']} |" for r in sel]
        lines.append("")
    return "\n".join(lines)


def build(db):
    """Return {relative path: canonical file text}."""
    return {
        "views/datasets_wide.csv": csvio.format_rows(WIDE_COLS, wide(db), ("dataset_id",)),
        "views/discrepancies.csv": csvio.format_rows(DISC_COLS, discrepancies(db), DISC_KEYS),
        "views/needs_verification.csv": csvio.format_rows(VERIFY_COLS, needs_verification(db), ("dataset_id", "field")),
        "views/usable_hours.csv": csvio.format_rows(HOURS_COLS, usable_hours(db), ("dataset_id",)),
        "views/usable_hours.md": usable_hours_md(sorted(usable_hours(db), key=lambda r: r["dataset_id"]), db),
    }


def main():
    for path, text in build(dbmod.load()).items():
        (csvio.ROOT / path).write_bytes(text.encode("utf-8"))
        print("wrote", path, text.count("\n") - 1, "rows")


if __name__ == "__main__":
    main()
