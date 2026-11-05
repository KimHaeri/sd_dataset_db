# sd_dataset_db

A database of speaker diarization datasets and other conversational speech that can be turned into diarization data, kept as CSV files under git, together with the tools to download them, measure them from their reference RTTM files and record the results. It is built to be read and maintained by AI assistants (such as Claude Code) as well as people, so every important value carries its source.

The design follows [itoten/ser_dataset_db](https://github.com/itoten/ser_dataset_db) (the same idea for speech emotion recognition): `data/*.csv` is authoritative, every fact has an evidence row, and `tools/validate.py` enforces the rules before each commit.

## Where to look first

| You want | Look at |
|---|---|
| All datasets at a glance | `views/datasets_wide.csv` (generated; one row per dataset) |
| Values nobody has checked yet | `views/needs_verification.csv` (generated; every canonical value backed only by `seed`, or by `secondary` evidence such as a survey lead) |
| Disagreements between values | `views/discrepancies.csv` (generated; includes reported vs measured) |
| The source of a value | `data/evidence.csv`, filtered by `dataset_id` and `field` |
| Meaning, type and allowed nulls of a column | `schema/columns.csv`; allowed values in `schema/enums.csv`; table keys in `schema/tables.csv` |
| What we downloaded and measured | `data/collections.csv`, `measurements/<dataset_id>.json` |
| Which challenge used which dataset | `data/challenges.csv`, `data/challenge_membership.csv` |
| Which data we plan to use, and what is still open | `docs/data_plan.md` (snapshot for discussion) |
| Conversational datasets found but not yet added | `docs/conversation_survey.md` (survey of 2026-11-03 and 2026-11-04; leads, grouped by licence) |
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
- **License tier**: `license_tier` says what the data may be used for: `train` (permissive), `eval` (ShareAlike, NonCommercial or research-only terms that allow redistribution; open-set evaluation only), `licensed_internal` (LDC, ELRA, or a signed research-only agreement by maintainer decision), `excluded` (NoDerivatives, no redistribution, paid) or `hold` (undecided). It carries evidence like the licence. `license_class` is not the tier: CC BY-SA is `open` but `eval`. `tools/validate.py` rejects a tier that the licence does not allow; a permissive licence may be `eval` when used for evaluation only, and a missing or unclear licence can become `eval` only by a maintainer decision (rules in `docs/manual.md`).
- **Language**: everything in the DB and its documents is English.
- **No machine-specific paths**: local data is referred to by environment variable (`$SD_DATA_ROOT/<dataset_id>`), set in the git-ignored `.env`. `tools/validate.py` rejects absolute home paths in tracked files.

## Evidence rules

Columns marked `yes` or `status` in the `evidence` column of `schema/columns.csv` need an evidence row for each value. URL and free-text columns do not.

- Each such cell has exactly one row with `is_canonical=true`, and its value equals the cell.
- Strength of `source_type`: `user` > `measured` > `primary` (paper, official page, LICENSE, LDC catalogue) > `secondary` > `seed`. When a weaker source is canonical while a stronger one exists, `note` must say why.
- **`seed`** marks values filled from an assistant's background knowledge when the repository was created. Nobody opened a source for them. They are listed in `views/needs_verification.csv`; replace each with a checked source (`tools/db.py ev ...`) before relying on it. A `collected` dataset may not keep any `seed` value, and `validate.py --strict` fails while any remain.
- **Survey leads** (since 2026-11-04) are datasets found by the conversation survey and entered as `candidate` / `unexamined` with `secondary` evidence: the licence and turn type as the search copied them, everything else in `notes`. Their `status_note` starts with "Survey lead". They are listed in `views/needs_verification.csv` too; checking one means opening its page and replacing each value with `primary` evidence (manual, "Workflow: verify a seed value or survey lead").
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
- Conversational corpora not made for diarization count too (since 2026-11-03), when speaker turns can be obtained from utterance timestamps with speaker labels or by VAD on per-speaker close-talk channels; `turn_source` says which.
- Single-speaker corpora used only to simulate conversations are kept as `excluded` with `single_speaker_only;simulation_source_only`, so that what was considered stays visible.
- When two rows turn out to be the same, mark one `excluded` (`duplicate_entry`) and link them with `possibly_same_as`. IDs are never deleted.

## Current state (2026-11-04)

550 datasets, 9 challenges: 100 checked against their sources and 450 survey leads not yet checked. `candidate` 531, `collected` 2 (`aishell4`, `dihard3`), `needs_decision` 2 (`ego4d`, `msdwild`), `deferred` 2, `excluded` 13. Seed values left: none; every dataset has been checked against primary sources (papers, official pages, LICENSE files, LDC catalogue pages, lab copies). The history of each change is in `git log`.

Licence tiers of the checked datasets (`license_tier`; survey leads have none yet):

- **`train`** (31): permissive licence, used for training
  - `ami`: CC BY 4.0 by maintainer decision (the release 1.7 licence file says CC BY-NC-SA 2.5; kept as conflicting evidence); partition not chosen yet
  - `icsi`: CC BY 4.0
  - `notsofar1`: CC BY 4.0; train split only (dev1, eval_small and eval_full are for evaluation)
  - `librispeech_meetings_sim`: clean and reverb conditions only (LibriSpeech CC BY 4.0 and generated RIRs); the noise conditions are not used
  - `librispeech`: CC BY 4.0; simulation source only (excluded as diarization data)
  - Added from the 2026-11-03 conversation survey: `nb_samtale` (CC0 1.0), `hcrc_maptask` (CC BY 4.0), `primock57` (CC BY 4.0), `otospeech_fd_280h` (CC BY 4.0 in the card metadata; gated)
  - Lab copies found by the 2026-11-04 re-scan: `harper_valley_bank` (CC BY 4.0; the lab holds the SLUE-HVB subset), `npsc` (CC0 1.0; 140 h of Norwegian parliament meetings with speaker-timed sentences)
  - Survey candidates checked on 2026-11-04 (verification batches A-C): `spjallromur`, `fearless_steps_challenge`, `otospeech_fd_task_20h`, `otospeech_fd_task_v2`, `spice`, `simsamu`, `kenya_ph_dialogue`, `datahive_conversations_sample`, `ocular_en_fullduplex_sample`, `perit_duplex_support_en`, `real_turnturk`, `humyn_indic_multispeaker`
  - Checked from the survey on 2026-11-04: `egocom` (MIT; 38.5 h, a wearable per participant), `multi_tpc` (CC BY 4.0; a WAV and word timings per participant), `kallaama` (CC BY 4.0; speaker turns not confirmed yet)
- **`eval`** (19): evaluation only
  - ShareAlike or NonCommercial: `aishell4`, `alimeeting`, `chime5`, `chime6` (CC BY-SA 4.0), `seamless_interaction` (CC BY-NC 4.0)
  - Built as evaluation sets, audio without a licence of its own (maintainer decision): `earnings21` (fair-use claim), `libricss` (LibriSpeech test-clean re-recordings)
  - Only development and test splits published: `voxconverse` (CC BY 4.0), `dipco` (CDLA-Permissive-1.0), `displace2023` (CC BY 4.0; only Dev released), `indic_diarbench` (CC BY 4.0; test splits only)
  - Lab copies found by the 2026-11-04 re-scan: `aishell5`, `earnings22` (CC BY-SA 4.0), `expresso`, `spokenwoz` (CC BY-NC 4.0)
  - Survey candidates checked on 2026-11-04: `voxmm` (CC BY 4.0, dev/test only), `ascend` (CC BY-SA 4.0)
  - Research-only agreement; evaluation only because the video copyright stays with the original creators (maintainer decision 2026-11-01): `msdwild` (agreement not signed yet)
- **`licensed_internal`** (18): LDC or signed agreement, internal use only, never redistributed
  - Training: `switchboard1`, `fisher_english_part1`, `fisher_english_part2`, `fisher_meetings_sim` (clean and reverb conditions only; the noise conditions are not used)
  - Train split for training, other splits for evaluation: `callhome_spanish`, `callhome_american_english` (transcripts not on the lab storage), `mixer6_chime8`, `ego4d` (who signed the agreement for the lab copy is not known), `msp_conversation` (research-only agreement; who signed for the lab copy is not known)
  - Evaluation only: `rt03_eval`, `callhome_sre2000`, `dihard3` (development and evaluation sets)
  - Lab copies found by the 2026-11-04 re-scan: `fisher_spanish`, `seame`, `babel` (25 language packs) (LDC); `hub5_2000_eng` (LDC evaluation set); `open_yap_1k` (1,000 h, data use agreement that allows training but not redistribution; who signed it for the lab copy is not known)
  - Re-judged 2026-11-04 under the conversation scope: `mixer6` (its telephone calls have one channel per side, so turns can come from VAD; not on the lab storage). Its interview subset with segments is `mixer6_chime8`
- **`hold`** (29): undecided
  - `iemocap`: release form with a licence PDF not read yet; who signed it for the lab copy is not known
  - `aphasiabank`, `dementiabank`: TalkBank password-protected clinical banks (CC BY-NC-SA 4.0; the Ground Rules say the data cannot be included in models, and password-protected data cannot be posted on other servers: whether the lab's shared copy is allowed needs checking)
- **`excluded`** (3)
  - `magicdata_ramc`: CC BY-NC-ND 4.0 (NoDerivatives)
  - `ava_avd`: annotations MIT, no licence stated for the movie videos (`none_stated`); excluded by maintainer decision after discussion with the PI (2026-11-01)

Maintainer rules: SA/NC data is evaluation only; published splits are used as defined (train splits for training, development and test splits for evaluation; a dataset with only development and test splits is evaluation only); LDC training corpora are used for training, LDC evaluation sets for evaluation, internal only.

Open items:

- Decisions: signing the `msdwild` agreement and which of its splits to evaluate on; who signed the agreement for the lab copy of `ego4d` (only an institutional signature covers a shared copy).
- Licence: the maintainer reports (2026-11-03) that the CHiME organisers decided to drop ShareAlike and plans to train on `chime5`/`chime6` once that is published; on 2026-11-03 the CHiME-5 page and the OpenSLR 150 LICENSE.txt still say CC BY-SA 4.0. The lab copy of `chime5` carries the earlier CHiME-5 non-commercial licence 1.00; the CHiME-5 page re-issued it under CC BY-SA 4.0 in 2024. Either way evaluation only.
- Transcripts for `callhome_american_english` (LDC97T14): not on the lab storage.
- Lab copies without RTTM (`lab_copy_available`): `ami`, `chime6`, `alimeeting`, `msp_conversation`, `seamless_interaction`, `chime5`, `dipco`, `callhome_american_english` (speech only), `ego4d`, `mixer6_chime8` (transcripts still archived), `switchboard1`, `fisher_english_part1`, `fisher_english_part2`, `callhome_spanish`, `rt03_eval`. Lab copies with RTTM in the copy or its repository, not registered yet: `voxconverse`; with speaker segments not yet examined: `callhome_sre2000`. Converting their labels to RTTM is the next step before they can be measured and marked `collected`. The two simulations have RTTM per shard, but they sit outside `$SD_DATA_ROOT` on purgeable scratch storage and need to be copied to permanent storage first.

Conversation survey (2026-11-03, second pass 2026-11-04): `docs/conversation_survey.md` lists 496 further candidates, grouped by licence. The first pass searched speech conferences, LREC/*CL and corpus archives, GitHub, Zenodo, OpenSLR and Hugging Face. The second went through complete lists: toolkit recipes (ESPnet, Lhotse, icefall, Kaldi, SpeechBrain, NeMo), the LDC by-year catalogue, ELRA, the Hugging Face Hub API, all TalkBank banks and CLARIN archives, and journals and regional platforms; journal coverage is still thin. Since 2026-11-04 every lead is also a DB row (`candidate`, `unexamined`, `secondary` evidence), so it shows in `views/datasets_wide.csv` and `views/needs_verification.csv`; the document keeps the grouping by licence. Not covered by it: RealMAN, Korean corpora on AIHub (overseas use needs a separate agreement with NIA).

## License

MIT (see [LICENSE](LICENSE)). The license covers this database and its tools, not the datasets described here: each keeps its own terms, recorded in `license_spdx` and `license_note`.
