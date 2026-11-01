# sd_dataset_db

A database of speaker diarization datasets, kept as CSV files under git, together with the tools to download them, measure them from their reference RTTM files and record the results. It is built to be read and maintained by AI assistants (such as Claude Code) as well as people, so every important value carries its source.

The design follows [itoten/ser_dataset_db](https://github.com/itoten/ser_dataset_db) (the same idea for speech emotion recognition): `data/*.csv` is authoritative, every fact has an evidence row, and `tools/validate.py` enforces the rules before each commit.

## Where to look first

| You want | Look at |
|---|---|
| All datasets at a glance | `views/datasets_wide.csv` (generated; one row per dataset) |
| Values nobody has checked yet | `views/needs_verification.csv` (generated; every canonical value backed only by `seed`) |
| Disagreements between values | `views/discrepancies.csv` (generated; includes reported vs measured) |
| The source of a value | `data/evidence.csv`, filtered by `dataset_id` and `field` |
| Meaning, type and allowed nulls of a column | `schema/columns.csv`; allowed values in `schema/enums.csv`; table keys in `schema/tables.csv` |
| What we downloaded and measured | `data/collections.csv`, `measurements/<dataset_id>.json` |
| Which challenge used which dataset | `data/challenges.csv`, `data/challenge_membership.csv` |
| A guide with the workflows | `docs/manual.md` |
| How Claude Code maintains the DB | `.claude/skills/maintaining-sd-dataset-db/SKILL.md` |

## Tables

| File | One row is | Key |
|---|---|---|
| `data/datasets.csv` | one dataset (authoritative) | `dataset_id` |
| `data/evidence.csv` | the source for one value in `datasets` | `evidence_id` = `<dataset_id>/<field>/<NN>` |
| `data/aliases.csv` | another name (official name, short name, LDC/OpenSLR number, former label) | `dataset_id`, `alias` |
| `data/relations.csv` | a relation between datasets (version, subset, shared recordings, different dataset) | `dataset_id`, `relation`, `other_dataset_id` |
| `data/splits.csv` | one published split (sessions, hours), with its own source | `dataset_id`, `split` |
| `data/challenges.csv` | one evaluation campaign (DIHARD, CHiME, VoxSRC, M2MeT, ...) | `challenge_id` |
| `data/challenge_membership.csv` | a dataset used by a challenge, and in which role | `challenge_id`, `dataset_id`, `role` |
| `data/annotations.csv` | an annotation other than speaker segments (transcript, gender, face tracks), with its own source | `dataset_id`, `item` |
| `data/collections.csv` | one dataset we downloaded: where it lives and what was measured | `dataset_id` |

Diarization-specific columns of `datasets`:

- Setting: `domain` (meeting, telephone, broadcast, web_video, dinner_party, egocentric, ...), `speech_style` (spontaneous / scripted / read / simulated_mixture), `recording_setup` (close_talk, far_field_single, far_field_array, wearable, telephone_channel, broadcast_mix), `modality` (audio / audio_visual). Lists are `;`-separated.
- Size, as published (`*_reported`): `hours_reported`, `n_sessions_reported`, `n_speakers_reported`, `speakers_per_session_reported` (`N` or `MIN-MAX`), `overlap_ratio_reported` (percent of speech).
- Size, as measured by us (`*_measured`): `hours_measured`, `n_sessions_measured`, `n_speakers_measured`, `overlap_ratio_measured`. Only `tools/sync.py` writes these, from `measurements/<dataset_id>.json`.
- Labels: `annotation_format` (rttm, uem, textgrid, ...), `annotation_method` (manual / forced_alignment / automatic / mixed), `has_transcript`, `has_official_splits`.
- Status: `collection_status` is `collected` (downloaded, measured, has a `collections.csv` row) / `candidate` / `needs_decision` / `deferred` / `excluded`. Every status except `collected` has reasons in `status_reason_codes`; `collected` has `NA`.

## Conventions

- **Missing values**: empty = not checked. `unknown` = checked, but the sources do not say; `NA` = does not apply; `none` = checked, there is none. Which are allowed per column is in `schema/columns.csv`.
- **IDs** match `^[a-z][a-z0-9]*(_[a-z0-9]+)*$` and never change once committed (keep an old one in `aliases` as `former_label`).
- **CSV format**: UTF-8, no BOM, LF, minimal quoting, rows in key order. After editing by hand, run `python3 tools/db.py fmt`.
- **Licenses**: `license_spdx` maps the stated terms to an SPDX identifier or `LicenseRef-...`; `license_class` is derived from it mechanically. Separate terms for audio, annotations and video go in `license_note`.
- **License tier**: `license_tier` says what the data may be used for: `train` (permissive), `eval` (ShareAlike, NonCommercial or research-only terms that allow redistribution; open-set evaluation only), `licensed_internal` (LDC, ELRA), `excluded` (NoDerivatives, no redistribution, paid) or `hold` (undecided). It carries evidence like the licence. `license_class` is not the tier: CC BY-SA is `open` but `eval`. `tools/validate.py` rejects a tier that the licence does not allow; a missing or unclear licence can become `eval` only by a maintainer decision (rules in `docs/manual.md`).
- **Language**: everything in the DB and its documents is English.
- **No machine-specific paths**: local data is referred to by environment variable (`$SD_DATA_ROOT/<dataset_id>`), set in the git-ignored `.env`. `tools/validate.py` rejects absolute home paths in tracked files.

## Evidence rules

Columns marked `yes` or `status` in the `evidence` column of `schema/columns.csv` need an evidence row for each value. URL and free-text columns do not.

- Each such cell has exactly one row with `is_canonical=true`, and its value equals the cell.
- Strength of `source_type`: `user` > `measured` > `primary` (paper, official page, LICENSE, LDC catalogue) > `secondary` > `seed`. When a weaker source is canonical while a stronger one exists, `note` must say why.
- **`seed`** marks values filled from an assistant's background knowledge when the repository was created. Nobody opened a source for them. They are listed in `views/needs_verification.csv`; replace each with a checked source (`tools/db.py ev ...`) before relying on it. A `collected` dataset may not keep any `seed` value, and `validate.py --strict` fails while any remain.
- A new fact never overwrites the old evidence: the old row becomes `superseded`. A value that was simply wrong and has no replacement is withdrawn with `tools/db.py clear`, which empties the cell and keeps the row as `superseded` with the reason; evidence rows are never deleted. When sources disagree and cannot be decided, keep both as `conflicting` and set the cell to `conflicting` (license) or leave the better one canonical with a note.
- `*_measured` columns take only `measured` evidence; `*_reported` columns cannot use `measured`.
- Write nothing the sources do not say. Never guess URLs, catalogue numbers or counts.

## Collecting a dataset

```bash
cp .env.example .env                                   # set SD_DATA_ROOT
python3 tools/fetch.py voxconverse --dry-run           # direct_download datasets only; others by hand
python3 tools/fetch.py voxconverse                     # -> $SD_DATA_ROOT/voxconverse/raw/ + SHA256SUMS
# unpack; then add a collections row that says where the RTTM/UEM/audio files are
python3 tools/db.py add collections dataset_id=voxconverse data_env_var=SD_DATA_ROOT rttm_glob='dev/*.rttm' uem_glob=NA audio_glob='audio/*.wav'
python3 tools/db.py ev voxconverse collection_status collected source_type=user source_ref="maintainer decision"
python3 tools/db.py ev voxconverse status_reason_codes NA source_type=user source_ref="maintainer decision"
python3 tools/measure.py voxconverse                   # -> measurements/voxconverse.json
python3 tools/sync.py                                  # fills collections + datasets.*_measured with evidence
python3 tools/views.py && python3 tools/validate.py
```

`tools/measure.py --rttm-dir DIR` prints the same statistics for loose RTTM files without touching the DB. It needs only the standard library; `soundfile` is used for audio durations when installed (otherwise `.wav` via `wave`).

## Validation

```bash
python3 tools/validate.py            # format, types, enums, keys, evidence rules, measurements, views
python3 tools/validate.py --strict   # also fail while any seed value remains
python3 tools/views.py               # regenerate views/
python3 tools/db.py get|set|add|ev|clear|fmt
```

- Run with Python 3.9+; no third-party packages are needed for the DB tools.
- `git config core.hooksPath tools/hooks` (once per clone) makes `tools/validate.py` run before every commit; a commit that fails validation is refused. `tools/hooks/pre-commit` must stay executable. Do not use `--no-verify`.
- Make one commit per dataset or per checking session, and say in the message what changed and what the evidence was.

## What counts as one row

- One row per original dataset release. Plain re-uploads (Hugging Face, Kaggle mirrors) go into the original's `aliases`. Re-annotations, re-splits and challenge versions that change the content are separate rows linked with `relations` (e.g. `chime6 shares_recordings_with chime5`).
- Single-speaker corpora used only to simulate conversations are kept as `excluded` with `single_speaker_only;simulation_source_only`, so that what was considered stays visible.
- When two rows turn out to be the same, mark one `excluded` (`duplicate_entry`) and link them with `possibly_same_as`. IDs are never deleted.

## Current state (2026-10-26)

31 datasets, 9 challenges. `candidate` 25, `collected` 1, `deferred` 1, `needs_decision` 2, `excluded` 2.

- Survey of the lab's shared corpus storage on 2026-10-26: `aishell4` is `collected` (train_L, train_M and test; train_S is missing from the lab copy) and measured from its RTTM files. `ami`, `chime6`, `alimeeting` (Test_Ali only), `switchboard1` and `fisher_english_part1` have lab copies but no RTTM yet, so they are `candidate` with `lab_copy_available`. Six datasets were added from the same survey: `msp_conversation`, `seamless_interaction`, `rt03_eval`, `callhome_spanish`, and two lab-internal simulations, `librispeech_meetings_sim` and `fisher_meetings_sim` (on purgeable scratch storage).
- License tiers set on 2026-10-27 for every dataset whose licence is verified (15 of 29): `train` 2 (`voxconverse`; `librispeech` as a simulation source), `eval` 4 (`aishell4`, `alimeeting`, `chime6`, `seamless_interaction`), `licensed_internal` 5 (LDC corpora and `fisher_meetings_sim`), `excluded` 1 (`magicdata_ramc`, ND), `hold` 3: `ami` (the release 1.7 licence file says CC BY-NC-SA 2.5, the official page CC BY 4.0), `msp_conversation` (terms not checked), `librispeech_meetings_sim` (its noise set BFND states no licence).
- Maintainer decisions on 2026-10-30: `ami` is treated as CC BY 4.0 and is `train` (both conflicting licence rows are kept); LDC data is used for training, internal only (`switchboard1`, `fisher_english_part1`, `callhome_spanish`, `fisher_meetings_sim`); `rt03_eval` and `callhome_sre2000` stay for evaluation (internal) because they are evaluation data. `dihard3` (2026-10-31): the development set (LDC2022S12) is used for training, the evaluation set (LDC2022S14) for evaluation only. 
- 2026-10-31: `dipco` is CDLA-Permissive 1.0 (`train`, with `ami` and `voxconverse` the real recordings in that tier), but its download (s3.amazonaws.com/dipco/DiPCo.tgz) answered 403, so it is `deferred` with `host_unreachable`. `displace2023`: only its Dev set is published (Zenodo, CC BY 4.0, `train` by licence; its use is not decided); no release of the Eval set was found. `earnings21`: its CC BY-SA 4.0 licence covers only the text and the audio is distributed on a fair-use claim; the maintainer decided it is `eval` only, as it was built as an evaluation benchmark. `ego4d`: speaker segments exist only for its Audio-Visual Diarization benchmark (572 five-minute clips, about 50 h); access needs a signed licence agreement (read from the draft PDF: training and evaluation allowed, no redistribution, internal copies only for an institutional signatory), so it is `needs_decision` and `licensed_internal`. `fisher_english_part2` (LDC2005S13/T19, on the lab storage) was added as LDC training data. `icsi` is CC BY 4.0 (`train`), downloadable from the Edinburgh ICSI page, headset audio only. `libricss` is built from LibriSpeech test-clean (never for training) and its re-recordings state no licence; the maintainer decided it is `eval` only, as it was built as an evaluation set. `mixer6` (LDC2013S03) has no speaker segments and is excluded as diarization data; its CHiME-7/8 transcribed subset `mixer6_chime8` (LDC2025S07) was added; by maintainer decision its training set is used for training and its development and test sets for evaluation. `msdwild` needs a signed research-only agreement that forbids redistribution, so it is `needs_decision` and `hold`. `notsofar1` is CC BY 4.0 (`train`; downloadable from Hugging Face with a free token); by maintainer decision its train split is used for training and dev1, eval_small and eval_full for evaluation. Tiers now (31 datasets): `train` 7, `eval` 7, `licensed_internal` 12, `excluded` 1, `hold` 3, not set 1 (licence still seed or unknown).

- Checked against primary sources on 2026-10-26 (official pages, papers, HTTP checks of the download URLs): `ami`, `voxconverse`, `aishell4`, `alimeeting`, `magicdata_ramc`. Their status reason is now `not_yet_downloaded`, and their `download_url` cells hold the URLs that were checked. Three seed values were wrong, all for MagicData-RAMC: it was recorded on smartphones, not over phone calls (`domain`, `recording_setup`), and no source states speakers per conversation (`unknown`).
- Still `seed`: 156 canonical evidence rows in `views/needs_verification.csv`, including the languages of `ami` and `voxconverse` and the speech style of `voxconverse`, which no source states.

Not yet surveyed: DIHARD I/II, NIST RT meeting sets, VoxSRC test sets after 2021, DISPLACE 2024, AISHELL-5, CHiME-8 MMCSG, RealMAN, Korean conversational corpora (e.g. AIHub), child-language and clinical corpora.

## License

MIT (see [LICENSE](LICENSE)). The license covers this database and its tools, not the datasets described here: each keeps its own terms, recorded in `license_spdx` and `license_note`.
