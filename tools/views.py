"""Generate the files under views/ from data/.

Usage: python3 tools/views.py      (rewrite every view)
validate.py regenerates them in memory and fails if the files on disk differ.

- views/datasets_wide.csv       one row per dataset with the main columns and joined facts
- views/discrepancies.csv       evidence that disagrees with the canonical value; reported vs measured
- views/usable_hours.csv         training / evaluation hours per dataset, from usable_as, hours and splits
- views/usable_hours.md          the same summed up: what can train, what can evaluate, what is on the lab storage
- views/ldc.csv, views/ldc.md     every LDC release in the DB: catalogue ids, lab copy, use, hours, check level
- views/needs_verification.csv  canonical values that rest only on unchecked evidence: `seed`, or
                                `secondary` (survey leads, mirrors, recipes) with no primary or stronger row
"""

import re

import csvio
import db as dbmod

WIDE_COLS = [
    "dataset_id", "name", "collection_status", "status_reason_codes", "languages", "domain", "speech_style",
    "recording_setup", "modality", "license_spdx", "license_class", "license_tier", "access_method", "raw_audio_available",
    "hours_reported", "n_sessions_reported", "n_speakers_reported", "speakers_per_session_reported",
    "overlap_ratio_reported", "annotation_format", "annotation_method", "turn_source", "usable_as", "has_transcript", "has_official_splits",
    "hours_measured", "session_hours_measured", "n_sessions_measured", "n_speakers_measured", "overlap_ratio_measured",
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


# Workflow defaults the survey wrote for every lead: they describe the DB's own state (a lead not yet examined),
# not a claim about the dataset, so they need no source. Only these exact values are skipped.
WORKFLOW_DEFAULTS = {("collection_status", "candidate"), ("status_reason_codes", "unexamined")}


def needs_verification(db):
    return [{"dataset_id": e["dataset_id"], "field": e["field"], "value": e["value"], "source_type": e["source_type"],
             "evidence_id": e["evidence_id"], "checked_on": e["checked_on"]}
            for e in db["evidence"][1] if e["is_canonical"] == "true" and e["source_type"] in ("seed", "secondary")
            and not (e["source_type"] == "secondary" and (e["field"], e["value"]) in WORKFLOW_DEFAULTS)]


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
        measured = total is None and _num(d["hours_measured"]) is not None
        if measured:
            total = _num(d["hours_measured"])
        session_hours = _num(d.get("session_hours_measured"))
        if session_hours is not None:
            total, measured = session_hours, False
        rows = splits.get(d["dataset_id"], [])
        cond = [r for r in rows if r["note"].startswith(("Used", "Not used"))]
        # Split rows of a published partition the project does not use (e.g. AMI scenario-only) are left out.
        parts = [r for r in rows if r not in cond and not r["note"].startswith("Partition not used")]
        train = ev = unsplit = None
        basis = ("measured: each session once" if session_hours is not None else "measured" if measured
                 else "reported" if total is not None else "no hours recorded")
        if cond and all(_num(r["hours_reported"]) is not None for r in cond):
            total = sum(_num(r["hours_reported"]) for r in cond if r["note"].startswith("Used"))
            basis = "used conditions' hours"
        elif cond and total is not None:
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
    sim_ids = {d["dataset_id"] for d in db["datasets"][1] if d["speech_style"] == "simulated_mixture"}
    real, sim = (lambda r: r["dataset_id"] not in sim_ids), (lambda r: r["dataset_id"] in sim_ids)
    lab = ("yes", "no", "unknown")
    lines = ["# Usable hours", "",
             "Generated by `tools/views.py` from `usable_as`, `hours_reported` (or `hours_measured` when no stated figure exists) and `data/splits.csv`; do not edit. "
             "Hours are recording hours as stated by the sources (speech-only hours are lower); \"derived\" rows are "
             "computed from session shares or totals (see `views/usable_hours.csv`, column `basis`). Survey leads and "
             "datasets on hold are not counted. Simulated data (`speech_style` simulated_mixture: mixtures built from other "
             "corpora, and LibriCSS, a room replay of LibriSpeech) is totalled apart from real recordings.", "",
             "| | On the lab storage | Not on the lab storage | Storage not checked | Total |", "|---|---|---|---|---|"]

    def total(keep, col):
        return [sum(_num(r[col]) or 0 for r in rows if keep(r) and r["on_lab_storage"] == s) for s in lab]

    for name, col in (("Training", "train_hours"), ("Evaluation", "eval_hours")):
        a, b = total(real, col), total(sim, col)
        for title, v, bold in ((f"{name}, real recordings", a, True), (f"{name}, simulated", b, False),
                               (f"{name}, both", [x + y for x, y in zip(a, b)], False)):
            t = f"**{sum(v):,.0f} h**" if bold else f"{sum(v):,.0f} h"
            lines.append(f"| {title} | {v[0]:,.0f} h | {v[1]:,.0f} h | {v[2]:,.0f} h | {t} |")
    uns = [r for r in rows if r["unsplit_hours"]]
    nohours = [r for r in rows if not (r["train_hours"] or r["eval_hours"] or r["unsplit_hours"])]
    lines += ["", f"The totals leave out {sum(_num(r['unsplit_hours']) for r in uns):,.0f} h in {len(uns)} datasets whose "
              f"train/evaluation split hours are not recorded, and {len(nohours)} datasets with no hours recorded; "
              "they are in the tables below with \"—\".", ""]
    uses = {"train_hours": ("train", "train_split"), "eval_hours": ("eval", "train_split", "eval_splits_only")}
    for title, keep, col in (("Training, real recordings", real, "train_hours"), ("Training, simulated", sim, "train_hours"),
                             ("Evaluation, real recordings", real, "eval_hours"), ("Evaluation, simulated", sim, "eval_hours")):
        sel = [r for r in rows if keep(r) and r["usable_as"] in uses[col]]
        sel = sorted(sel, key=lambda r: (-(_num(r[col]) or -1), r["dataset_id"]))
        if not sel:
            continue
        lines += [f"## {title}", "", "| Dataset | Hours | Licence tier | On the lab storage | Basis |", "|---|---|---|---|---|"]
        for r in sel:
            h = _num(r[col])
            if h is not None:
                hs = f"{h:,.1f}"
            elif r["unsplit_hours"]:
                hs = f"— ({_num(r['unsplit_hours']):,.1f} h in all; split not recorded)"
            else:
                hs = "—"
            lines.append(f"| `{r['dataset_id']}` | {hs} | {r['license_tier']} | {r['on_lab_storage']} | {r['basis']} |")
        lines.append("")
    return "\n".join(lines)


LDC_COLS = ["dataset_id", "name", "catalogue_ids", "check_level", "usable_as", "on_lab_storage", "hours_reported", "hours_basis",
            "hours_as_found", "languages", "domain", "turn_source", "source_url"]


def is_ldc(d):
    return (d["license_spdx"] == "LicenseRef-LDC-member-or-nonmember" or "catalog.ldc.upenn.edu" in d["source_url"]
            or "built from Fisher" in d["license_note"] or "Fisher English Training Speech Parts 1 and 2 (LDC" in d["license_note"])


def check_level(d):
    if d["collection_status"] == "excluded":
        return "excluded"
    if d["status_note"].startswith("Survey lead"):
        return "licence checked" if "licence checked" in d["status_note"] else "survey lead"
    return "checked"


def ldc(db):
    ids = {}
    for a in db["aliases"][1]:
        ids.setdefault(a["dataset_id"], set()).update(re.findall(r"LDC\d{2,4}[A-Z]\d{2,3}", a["alias"]))
    basis = {}
    for e in db["evidence"][1]:
        if e["field"] == "hours_reported" and e["is_canonical"] == "true":
            n = e["note"]
            basis[e["dataset_id"]] = ("estimate" if "Estimate" in n or "Computed:" in n else
                                      "catalogue, approximate" if n.startswith("Approximate figure") else
                                      "catalogue" if e["source_type"] == "primary" else e["source_type"])
    out = []
    for d in db["datasets"][1]:
        if not is_ldc(d):
            continue
        cat = set(re.findall(r"LDC\d{2,4}[A-Z]\d{2,3}", d["source_url"])) | ids.get(d["dataset_id"], set())
        m = re.search(r"; hours ([^;]*);", d["notes"])
        nd = not d["hours_reported"] and "Diarization hours not derivable" in d["notes"]
        out.append({"dataset_id": d["dataset_id"], "name": d["name"], "catalogue_ids": ";".join(sorted(cat)),
                    "check_level": check_level(d), "usable_as": d["usable_as"], "on_lab_storage": on_lab(d),
                    "hours_reported": d["hours_reported"] or d["session_hours_measured"] or d["hours_measured"],
                    "hours_basis": ("not derivable" if nd else basis.get(d["dataset_id"], "") if d["hours_reported"] else
                                    "measured" if d["session_hours_measured"] or d["hours_measured"] else ""),
                    "hours_as_found": m.group(1).strip()[:60] if m and not nd else "",
                    "languages": d["languages"], "domain": d["domain"], "turn_source": d["turn_source"], "source_url": d["source_url"]})
    return out


def ldc_hours_summary(rows, db):
    """Hours of the LDC rows, on and off the lab storage, each recording counted once where the DB knows the overlap."""
    D = {d["dataset_id"]: d for d in db["datasets"][1]}
    live = [r for r in rows if r["check_level"] != "excluded"]
    ids = {r["dataset_id"] for r in live}
    inside = {r["dataset_id"] for r in db["relations"][1] if r["relation"] == "subset_of" and r["other_dataset_id"] in ids}
    inside |= {r["other_dataset_id"] for r in db["relations"][1] if r["relation"] == "contains" and r["dataset_id"] in ids}

    def hours(d):
        for f in ("session_hours_measured", "hours_measured", "hours_reported"):
            if d[f]:
                return float(d[f]), f
        return None, ""

    groups = {}
    sims, skipped, partial = [], [], []
    for r in live:
        d = D[r["dataset_id"]]
        if d["speech_style"] == "simulated_mixture":
            sims.append(r)
            continue
        if r["dataset_id"] in inside:
            skipped.append(r["dataset_id"])
            continue
        h, f = hours(d)
        on = "yes" if r["on_lab_storage"] == "yes" else "no"
        use = {"eval": "evaluation", "hold": "on hold (training)"}.get(r["usable_as"], "not yet assigned")
        g = groups.setdefault((on, use), [0, 0, 0.0])
        g[0] += 1
        if h is not None:
            g[1] += 1
            g[2] += h
        if on == "yes" and f != "hours_reported" and d["hours_reported"]:
            rest = float(d["hours_reported"]) - h
            if rest > 0:
                partial.append((r["dataset_id"], h, float(d["hours_reported"])))
                g2 = groups.setdefault(("no", use), [0, 0, 0.0])
                g2[2] += rest
    lines = ["## Hours on and off the lab storage", "",
             "Hours usable for diarization, each recording counted once as far as the DB knows: a lab copy uses its measured "
             "session hours, otherwise the hours above; rows inside another counted row (relations subset_of/contains) and "
             "simulated mixtures are left out. Partial overlaps that remain (BOLT with CALLFRIEND/CALLHOME, DIHARD editions, "
             "ASpIRE with Mixer 6) still make the totals slightly high, and estimates are rough.", "",
             "| Where | Use | Rows | Rows with hours | Hours |", "|---|---|---|---|---|"]
    tot = {"yes": [0, 0, 0.0], "no": [0, 0, 0.0]}
    for on in ("yes", "no"):
        for use in ("evaluation", "on hold (training)", "not yet assigned"):
            g = groups.get((on, use))
            if not g or not g[0] and not g[2]:
                continue
            where = "On the lab storage" if on == "yes" else "Not on the lab storage (needs a licence or order)"
            lines.append(f"| {where} | {use} | {g[0]} | {g[1]} | {g[2]:,.0f} h |")
            for i in range(3):
                tot[on][i] += g[i]
    for on, label in (("yes", "On the lab storage, all"), ("no", "Not on the lab storage, all")):
        t = tot[on]
        lines.append(f"| **{label}** | | {t[0]} | {t[1]} | **{t[2]:,.0f} h** |")
    a = [tot["yes"][i] + tot["no"][i] for i in range(3)]
    lines += [f"| **All LDC rows** | | {a[0]} | {a[1]} | **{a[2]:,.0f} h** |", ""]
    for did, h, full in partial:
        lines.append(f"- `{did}`: the lab copy is partial ({h:,.0f} h measured); the rest of the release "
                     f"({full - h:,.0f} h of the {full:,.0f} h above) is counted as not on the lab storage.")
    for r in sims:
        lines.append(f"- Simulated, not counted: `{r['dataset_id']}` ({r['hours_reported'] or '—'} h), built from LDC recordings.")
    if skipped:
        lines.append("- Counted inside another row: " + ", ".join(f"`{x}`" for x in sorted(skipped)) + ".")
    nohours = [r["dataset_id"] for r in live if r["dataset_id"] not in inside and D[r["dataset_id"]]["speech_style"] != "simulated_mixture"
               and hours(D[r["dataset_id"]])[0] is None]
    if nohours:
        lines.append("- Without hours (not in the totals): " + ", ".join(f"`{x}`" for x in sorted(nohours)) + ".")
    return lines + [""]


def ldc_md(rows, db):
    rows = sorted(rows, key=lambda r: r["dataset_id"])
    by = {}
    for r in rows:
        by.setdefault((r["check_level"], r["on_lab_storage"]), []).append(r)
    lines = ["# LDC releases", "",
             "Generated by `tools/views.py`; do not edit. Every LDC release in the DB (licence `LicenseRef-LDC-member-or-nonmember`, "
             "a catalogue page as source, or built from one). LDC data is internal only and never redistributed, and is "
             "used for evaluation only, never for training (PI decision 2026-11-13). Corpora with official splits evaluate on their development "
             "and test splits only.", "",
             "Hours basis: `catalogue` is the figure the catalogue page states; `catalogue, approximate` is a page that says "
             "approximately, or gives minutes, file sizes or several parts that were summed; `estimate` is derived from call counts "
             "and durations (method in the evidence note) and is only a rough size; `measured` is the lab copy, each session once, "
             "shown where no catalogue figure is recorded; `not derivable` means the catalogue total counts "
             "the same conversations several times (segments, summed and separate channels, extra microphones) and the distinct "
             "conversation hours are not stated (reason in the row notes). For the Mixer releases the hours are the "
             "conversation usable for diarization (telephone calls plus informal conversation, each counted once), not the "
             "catalogue total, which counts each of the 14 room microphones separately. Some rows still overlap partly (BOLT and "
             "CALLFRIEND/CALLHOME, the DIHARD editions, ASpIRE and the SRE test sets with Mixer), so a column total overstates. "
             "Each table is sorted by hours, largest first; rows without hours come last.", "",
             f"{len(rows)} rows: " + ", ".join(f"{sum(1 for r in rows if r['check_level'] == k)} {k}" for k in
                                            ("checked", "licence checked", "survey lead", "excluded")) +
             f"; {sum(1 for r in rows if r['on_lab_storage'] == 'yes')} on the lab storage.", ""] + ldc_hours_summary(rows, db)
    def table(title, sel, note=""):
        if not sel:
            return []
        t = [f"## {title} ({len(sel)})", ""] + ([note, ""] if note else [])
        t += ["| Dataset | Catalogue | Use | Hours | Hours basis | Turns | Languages |", "|---|---|---|---|---|---|---|"]
        def hours_key(r):
            try:
                return (0, -float(r["hours_reported"]), r["dataset_id"])
            except ValueError:
                return (1, 0.0, r["dataset_id"])
        for r in sorted(sel, key=hours_key):
            h = r["hours_reported"] or (f"{r['hours_as_found']} (as found)" if r["hours_as_found"] else "")
            name = f"[{r['name']}]({r['source_url']})" if r["source_url"] else r["name"]
            t.append(f"| {name} | {r['catalogue_ids'].replace(';', ', ')} | {r['usable_as'] or '—'} | {h or '—'} | {r['hours_basis'] or '—'} | "
                     f"{r['turn_source'] or '—'} | {r['languages'] or '—'} |")
        return t + [""]
    lines += table("On the lab storage", [r for r in rows if r["on_lab_storage"] == "yes" and r["check_level"] != "excluded"])
    lines += table("Checked, not on the lab storage (would need a licence)",
                   [r for r in rows if r["on_lab_storage"] != "yes" and r["check_level"] == "checked"])
    lines += table("Survey leads, licence checked on the catalogue page (would need a licence)",
                   [r for r in rows if r["check_level"] == "licence checked" and r["on_lab_storage"] != "yes"],
                   "The licence line and the hours were checked on the catalogue page (hours on 2026-11-11); languages and turns are as the survey found them.")
    lines += table("Survey leads not checked", [r for r in rows if r["check_level"] == "survey lead"])
    lines += table("Excluded (duplicates)", [r for r in rows if r["check_level"] == "excluded"])
    return "\n".join(lines)


def manual_review_md(db):
    """Only what a person must decide, grouped; then what is waiting for information (no decision needed)."""
    D = [d for d in db["datasets"][1] if d["collection_status"] != "excluded"]
    tier_ev = {e["dataset_id"]: e for e in db["evidence"][1] if e["field"] == "license_tier" and e["is_canonical"] == "true"}
    note = lambda d: " ".join(tier_ev.get(d["dataset_id"], {}).get("note", "").split())
    link = lambda d: f"[`{d['dataset_id']}`]({d['source_url']})" if d["source_url"] else f"`{d['dataset_id']}`"
    ldc = [d for d in D if is_ldc(d)]
    groups = [
        ("Purchase or vendor terms (commercial data: buy, or ask the vendor)",
         [d for d in D if not is_ldc(d) and d["license_spdx"] == "LicenseRef-proprietary-restricted" and d["license_tier"] in ("hold", "")]),
        ("Agreements to accept or sign (EULA, DUA, access request; research use)",
         [d for d in D if not is_ldc(d) and d["license_spdx"] != "LicenseRef-proprietary-restricted"
          and d["license_tier"] == "hold" and "needs_human_agreement" in note(d)]),
        ("Conflicting licence statements (choose a reading or ask the authors)",
         [d for d in D if not is_ldc(d) and d["license_tier"] in ("hold", "") and not note(d).startswith("Hold (information)") and
          (d["license_spdx"] == "conflicting" or "needs_human_conflict" in note(d))]),
        ("Open decisions recorded earlier (collection_status needs_decision)",
         [d for d in D if d["collection_status"] == "needs_decision"]),
    ]
    seen = set()
    lines = ["# Manual review", "",
             "Generated by `tools/views.py`; do not edit. Only items that need a person: a decision, a signature, a purchase or a "
             "choice between conflicting licence statements. Everything a primary page or a written rule could settle has been "
             "recorded in the DB with its evidence. The second part lists rows waiting for information, which need no decision.", "",
             "## Decisions", "",
             f"### LDC releases ({len(ldc)} rows)", "",
             "Decided 2026-11-13 with the PI: LDC data is used for evaluation only, never for training. LDC data not on the lab "
             "storage would still need a licence or order, which is a decision only if you want more of it. Rows, hours and storage: `views/ldc.md`.", ""]
    for title, rows in groups:
        rows = [d for d in rows if d["dataset_id"] not in seen]
        seen |= {d["dataset_id"] for d in rows}
        if not rows:
            continue
        lines += [f"### {title} ({len(rows)})", "", "| Dataset | Licence | What we found |", "|---|---|---|"]
        for d in sorted(rows, key=lambda d: d["dataset_id"]):
            why = note(d).replace("Hold (needs_human_agreement): ", "").replace("Hold (needs_human_conflict): ", "") or d["license_note"] or d["status_note"]
            lines.append(f"| {link(d)} | {d['license_spdx'] or '—'} | {why[:300].replace('|', '/')} |")
        lines.append("")
    waiting = [
        ("Licence or audio rights not yet established (find the source terms; no decision until then)",
         [d for d in D if note(d).startswith("Hold (information)")]),
        ("Licence page unreadable (retry later or from another network)", [d for d in D if d["license_spdx"] == "unknown" and not is_ldc(d)]),
        ("No licence stated for the data (ask the authors before any use)",
         [d for d in D if d["license_spdx"] == "none_stated" and not is_ldc(d) and d["license_tier"] in ("hold", "")]),
        ("Usable licence, but how to get speaker turns is not stated (check the files once obtained)",
         [d for d in D if d["license_tier"] in ("train", "eval") and d["usable_as"] not in ("not_used",) and not d["turn_source"]]),
    ]
    rest = [d for d in D if not is_ldc(d) and d["license_tier"] == "hold" and d["dataset_id"] not in seen
            and d["license_spdx"] not in ("unknown", "none_stated") and not note(d).startswith("Hold (information)")]
    if rest:
        seen |= {d["dataset_id"] for d in rest}
        lines += [f"### Other rows on hold (reason in the note) ({len(rest)})", "", "| Dataset | Licence | Reason |", "|---|---|---|"]
        for d in sorted(rest, key=lambda d: d["dataset_id"]):
            lines.append(f"| {link(d)} | {d['license_spdx'] or '—'} | {(note(d) or d['license_note'] or d['status_note'])[:300].replace('|', '/')} |")
        lines.append("")
    lines += ["## Waiting for information (no decision needed)", ""]
    for title, rows in waiting:
        rows = [d for d in rows if d["dataset_id"] not in seen]
        seen |= {d["dataset_id"] for d in rows}
        if rows:
            lines += [f"### {title} ({len(rows)})", "", ", ".join(link(d) for d in sorted(rows, key=lambda d: d["dataset_id"])), ""]
    nr = [d for d in D if note(d).startswith("Excluded by the rule (no redistribution")]
    if nr:
        lines += ["## For information: excluded only because redistribution is not allowed", "",
                  "No action needed. Each could be used internally (`licensed_internal`) if you decide to obtain it under its "
                  "agreement: " + ", ".join(link(d) for d in sorted(nr, key=lambda d: d["dataset_id"])) + ".", ""]
    return "\n".join(lines)


def build(db):
    """Return {relative path: canonical file text}."""
    return {
        "views/datasets_wide.csv": csvio.format_rows(WIDE_COLS, wide(db), ("dataset_id",)),
        "views/discrepancies.csv": csvio.format_rows(DISC_COLS, discrepancies(db), DISC_KEYS),
        "views/needs_verification.csv": csvio.format_rows(VERIFY_COLS, needs_verification(db), ("dataset_id", "field")),
        "views/ldc.csv": csvio.format_rows(LDC_COLS, ldc(db), ("dataset_id",)),
        "views/ldc.md": ldc_md(ldc(db), db),
        "views/manual_review.md": manual_review_md(db),
        "views/usable_hours.csv": csvio.format_rows(HOURS_COLS, usable_hours(db), ("dataset_id",)),
        "views/usable_hours.md": usable_hours_md(sorted(usable_hours(db), key=lambda r: r["dataset_id"]), db),
    }


def main():
    for path, text in build(dbmod.load()).items():
        (csvio.ROOT / path).write_bytes(text.encode("utf-8"))
        print("wrote", path, text.count("\n") - 1, "rows")


if __name__ == "__main__":
    main()
