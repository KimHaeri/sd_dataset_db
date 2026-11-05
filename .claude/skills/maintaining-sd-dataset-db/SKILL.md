---
name: maintaining-sd-dataset-db
description: Maintains the speaker diarization dataset database (diarization datasets and any conversational speech that can become diarization data), a git repository of CSV tables in which every value carries an evidence row (source, date, strength). Verifies seed values against primary sources, adds datasets and challenges, registers copies that already exist on the lab's storage, records simulated mixtures with their speech, noise and RIR sources, measures datasets from their RTTM files, sorts data into license tiers (train / eval / licensed_internal / excluded / hold), validates and commits. Use when someone asks to add, verify, download, measure or reclassify a diarization dataset, asks what diarization data the lab already has, asks whether a dataset may be used for training or only for evaluation, or asks about a dataset's license, access, size, overlap or status.
---

# Maintaining the speaker diarization dataset DB

Each dataset is one row in `data/datasets.csv`; every important value has a row in
`data/evidence.csv` saying where it came from. `tools/validate.py` enforces the rules. Correctness
matters more than coverage: when something is not known, the DB says so.

All paths are relative to the repository root. `<skill dir>` is this skill's directory
(`${CLAUDE_SKILL_DIR}` in Claude Code).

## First time in the repository

Read `README.md` and `docs/manual.md`, then run `python3 tools/validate.py`. It must end with
`0 error(s)`. While seed values remain, a warning about them is expected.

What you need to know about the surroundings:

- **Local data.** `.env` (git-ignored) sets `SD_DATA_ROOT`, and the dataset lives in
  `$SD_DATA_ROOT/<dataset_id>`. If the lab already keeps the corpora in one shared directory
  whose sub-directories use the same names as `dataset_id`, point `SD_DATA_ROOT` there instead of
  downloading again. Data outside that layout, such as a colleague's simulation on scratch
  storage, cannot be measured through `collections.csv` yet: record it as
  `lab_copy_available`.
- **Two Pythons.** The DB tools need only the standard library. `tools/measure.py` needs
  `soundfile` for any audio that is not `.wav` (FLAC, for example). Without it the audio duration
  step fails. Use an environment that has `soundfile` (a throw-away venv outside the repository
  is enough) and run with `python -I`.
- **The pre-commit hook runs `tools/validate.py`** once `git config core.hooksPath tools/hooks`
  is set in the clone (a local setting: check it with `git config core.hooksPath`). A commit
  that fails validation is refused. If git prints `hook was ignored because it's not set as
  executable`, the hook did not run: run `tools/validate.py` yourself and never claim the hook
  validated that commit.
- **Heavy work runs as a batch job.** That means scanning large trees, decoding many hours of
  audio and computing checksums. Reading RTTM files and audio headers of one corpus is light.

## Principles

1. **Check every factual claim yourself.** Open the paper, the official page, the LICENSE or the
   LDC catalogue entry. Count files yourself and measure with `tools/measure.py`. Reports from
   colleagues, other sessions and your own earlier replies are leads, not facts.
2. **Seed values are leads, not facts.** Never answer from a `seed` value without saying it is
   unverified, and never copy one into a new row.
3. **Write only what a source or a measurement supports.** No invented URLs, catalogue numbers,
   counts or licenses. When a source gives an approximate number ("over 4,000 hours"), leave the
   cell empty and quote the number in `notes`. Never cite a file you did not open.
4. **Decisions belong to the project maintainer.** Paying for LDC data, signing agreements,
   excluding data, choosing the tier of a `hold` dataset and choosing which data trains and which
   evaluates are theirs. Record their decisions as `source_type=user`; propose, do not decide.
   An instruction such as "update the DB" covers registering what you verified. It does not cover
   decisions they have not made.
5. **Never delete history.** Use `tools/db.py ev`, which supersedes the old evidence row. To
   withdraw a value that was simply wrong, use `tools/db.py clear ... reason=...`; never delete
   an evidence row. When
   sources disagree (for example the licence file in our copy and the current web page), keep
   both and mark the disagreement.
6. **Keep "the whole release" and "what we hold or use" apart** in counts and notes: full corpus
   vs challenge subset, all channels vs one, all splits vs the partial copy on the lab storage.
7. **No machine-specific paths, usernames or hostnames** in tracked files. Write
   `$SD_DATA_ROOT/<dataset_id>` or a description such as "the lab's shared corpus storage" or "a
   lab member's simulation". `validate.py` catches home directories only, not cluster paths such
   as `/work/...` or `/scratch/...`: check these yourself.
8. **Licensed data stays on the cluster.** Never upload, redistribute or paste its content
   (transcripts, RTTM excerpts) into an external service.
9. **Stay within the request.** Large sweeps (re-checking every license) are proposed, not started.

## Choose the workflow

- "Verify X" / values still seed or a survey lead → manual, "Workflow: verify a seed value or survey lead". Survey leads (`status_note` starts with "Survey lead") rest on `secondary` evidence copied by a search: open the page before trusting any of it.
- "Add this dataset" / a survey → manual, "Workflow: add a dataset". The scope is any real multi-speaker conversation whose turns can be obtained (`turn_source`: utterance timestamps with speakers, or VAD on per-speaker close-talk channels), not only diarization releases.
- "What does the lab already have?" / a directory of corpora → **Register lab copies** below.
- "Download / measure X" → README, "Collecting a dataset", then manual, "Workflow: collect a dataset".
- A simulation built from other corpora → **Simulated data** below.
- "May we train on X?" / "training or evaluation?" →
  [references/license-tiers.md](references/license-tiers.md).
- A challenge and its data → manual, "Workflow: record a challenge".
- A question → look in `views/datasets_wide.csv` and `data/evidence.csv` first and give the
  source type. Search outside only for empty, `unknown` or contested values, and offer to record
  what you find.

## Register lab copies

Use this when the user points at a directory of corpora. Copy the checklist and tick it off:

```
- [ ] 1. List the directory; pick the multi-speaker candidates; note unreadable entries
- [ ] 2. Find speaker-turn files (RTTM, UEM, TextGrid, JSON, NXT XML) per candidate
- [ ] 3. For each: what the copy holds vs the full release (splits, sessions, channels)
- [ ] 4. Read the licence file in the copy and compare it with the official page
- [ ] 5. Match to existing rows (grep views/datasets_wide.csv, data/aliases.csv)
- [ ] 6. Has RTTM and no seed values left → collections row, collected, measure, sync
- [ ] 7. Otherwise → candidate + lab_copy_available, with status_note saying what is missing
- [ ] 8. New datasets → add rows with evidence from the copy's readme and the official page
- [ ] 9. Finish; reply with the tier of each dataset
```

- In step 2, a time-limited scan (`timeout` with a bounded `find -maxdepth`) misses files in
  large trees. Say so in the reply, and look by hand inside every candidate that matters.
- In step 6, check that the RTTM files come from the official release (for example by listing
  the release tarball) before calling them the reference. Then correct `annotation_format` if
  needed.
- In step 7, `lab_copy_available` covers three cases: no RTTM yet (NXT XML, JSON, transcripts
  only), a partial copy, or a copy outside `$SD_DATA_ROOT`. Its status evidence is
  `source_type=measured` (the directory listing).
- Large differences between measured and published values (speakers per session, overlap) go
  into `collections.known_issues`. Mark them "not investigated" until someone has looked into
  them.
- Speaker labels are not always global across sessions. When labels repeat across sessions, say
  in `known_issues` that `n_speakers` counts labels.

## Simulated data

A simulation is its own row with `speech_style=simulated_mixture` and `domain=simulated`, linked
to its speech source with `relations` (`shares_recordings_with`). Record:

- the generation report it ships (meetings, hours, speakers per meeting, overlap) as
  `*_reported` with `source_type=primary`, and what you count from its manifests as `measured`;
- the source speakers and which split they come from. Training-split sources keep evaluation
  sets clean; say so in `notes`;
- the **speech, noise and RIR sources and each one's licence** in `license_note`. The tier
  follows the most restrictive source, per condition
  ([references/license-tiers.md](references/license-tiers.md));
- where it lives, without the path: whether the storage is purged (scratch) and whether the
  manifests hold absolute audio paths that break when the data moves.

Do not cite the generator's own log or config by path. Describe it ("merge_report.json of the
synth-librispeech-meetings simulation").

## Finish

```bash
python3 tools/db.py fmt
python3 tools/views.py
python3 tools/validate.py      # fix every error, then run again
```

- Update the "Current state" section of the README when counts or statuses change. Count the
  statuses with `csv`, not `cut -d,`: quoted titles contain commas.
- If you added a reason code or another enum value, describe it in `docs/manual.md` as well.
- Commit one dataset (or one checking session) per commit, staging files by name. Say in the
  message what was wrong or unverified, what the evidence was and what changed. Never bypass
  validation. Do not push unless asked.

## Reply

Keep it short, in this order:
1. What was registered (statuses, commits, validation result).
2. What was verified, and against what.
3. **What differs from earlier claims**, including your own earlier replies.
4. What could not be verified.
5. The tier of each dataset touched, with the licence evidence.
6. What is left for the maintainer to decide.

State nothing as fact that you did not check.

## Common errors

| Message contains | Fix |
|---|---|
| `needs exactly one canonical row` | add the value with `tools/db.py ev`, not `set` |
| `canonical value ... != datasets value` | the cell was edited with `set`; use `ev` so both change together |
| `*_reported fields cannot use measured` | your counts belong in `*_measured`, written by `tools/sync.py` |
| `collected but data/collections.csv has no row` | add the collections row before changing the status |
| `collected, but some values still rest on unchecked seed evidence` | verify the remaining seed values of that dataset first |
| `status_reason_codes must be NA exactly when collected` | `NA` for collected rows, at least one reason code otherwise |
| `... != measurements ... (run tools/sync.py)` | a measurement changed; run `tools/sync.py` |
| `views/... is out of date` | run `python3 tools/views.py` |
| `the datasets cell is empty but a row is still canonical or current` | the cell was emptied with `set`; restore it, then use `tools/db.py clear` |
| `not in canonical form` | run `python3 tools/db.py fmt` |
| `license_tier ... does not fit license_spdx` | the tier contradicts the licence (e.g. SA as `train`); re-read [references/license-tiers.md](references/license-tiers.md) |
| `not in enum ...` | use a value from `schema/enums.csv`, or add one there and describe it in the manual |
| `no files match ... under $SD_DATA_ROOT/<id>` (measure.py) | the glob in `collections.csv` is relative to the dataset directory; check `.env` |
| `ModuleNotFoundError: soundfile` / FLAC durations missing (measure.py) | run it in an environment with `soundfile` |
| git hint `hook was ignored because it's not set as executable` | the hook did not run; run `tools/validate.py` yourself, and check that `tools/hooks/pre-commit` is executable (`chmod +x`; git records mode 100755) |

## Files in this skill

- [references/license-tiers.md](references/license-tiers.md): which licences may train, which may
  only evaluate, the checks before assigning a tier, and keeping evaluation apart from training.
