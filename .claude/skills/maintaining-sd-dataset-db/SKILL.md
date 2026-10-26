---
name: maintaining-sd-dataset-db
description: Maintains the speaker diarization dataset database, a git repository of CSV tables in which every value carries an evidence row (source, date, strength). Verifies seed values against primary sources, adds datasets and challenges, downloads and measures datasets from their RTTM files, records evidence, validates and commits. Use when someone asks to add, verify, download or reclassify a diarization dataset, or asks about a dataset's license, access, size, overlap or status.
---

# Maintaining the speaker diarization dataset DB

Each dataset is one row in `data/datasets.csv`; every important value has a row in
`data/evidence.csv` saying where it came from. `tools/validate.py` enforces the rules and runs
as a pre-commit hook. Correctness matters more than coverage: when something is not known, the
DB says so.

## First time in the repository

Read `README.md` and `docs/manual.md`, then run `python3 tools/validate.py`. It must end with
`0 error(s)`; the warning about seed values is expected until they are verified.

## Principles

1. **Check every factual claim yourself.** Open the paper, the official page, the LICENSE or the
   LDC catalogue entry. Count files yourself with `tools/measure.py`.
2. **Seed values are leads, not facts.** Never answer from a `seed` value without saying it is
   unverified, and never copy one into a new row.
3. **Write only what a source or a measurement supports.** No invented URLs, catalogue numbers,
   counts or licenses. Leave a cell empty rather than filling in a plausible value.
4. **Decisions belong to the project maintainer**: paying for LDC data, signing agreements,
   excluding data. Record their decisions as `source_type=user`; propose, do not decide.
5. **Never delete history.** Use `tools/db.py ev`, which supersedes the old evidence row.
6. **Keep "the whole release" and "what we use" apart** in counts and notes (full corpus vs a
   challenge subset, all channels vs one).
7. **No machine-specific paths** in tracked files: `$SD_DATA_ROOT/<dataset_id>` only.
8. **Stay within the request.** Large sweeps (re-checking every license) are proposed, not started.

## Choose the workflow

- "Verify X" / values still seed → manual, "Workflow: verify a seed value".
- "Add this dataset" / a survey → manual, "Workflow: add a dataset".
- "Download / measure X" → README, "Collecting a dataset", then manual, "Workflow: collect a dataset".
- A challenge and its data → manual, "Workflow: record a challenge".
- A question → look in `views/datasets_wide.csv` and `data/evidence.csv` first; give the source type.

## Finish

```bash
python3 tools/views.py
python3 tools/validate.py      # fix every error, then run again
```

Update the "Current state" section of the README when counts change. Commit one dataset (or one
checking session) per commit, staging files by name. Say in the message what was wrong or
unverified, what the evidence was and what changed. Never bypass the hook.

## Common errors

| Message contains | Fix |
|---|---|
| `needs exactly one canonical row` | add the value with `tools/db.py ev`, not `set` |
| `canonical value ... != datasets value` | the cell was edited with `set`; use `ev` so both change together |
| `*_reported fields cannot use measured` | your counts belong in `*_measured`, written by `tools/sync.py` |
| `collected but data/collections.csv has no row` | add the collections row before changing the status |
| `collected, but some values still rest on unchecked seed evidence` | verify the remaining seed values of that dataset first |
| `... != measurements ... (run tools/sync.py)` | a measurement changed; run `tools/sync.py` |
| `not in canonical form` | run `python3 tools/db.py fmt` |
| `not in enum ...` | use a value from `schema/enums.csv`, or add one there and describe it in the manual |
