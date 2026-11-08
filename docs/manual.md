# Manual

A guide for people and assistants who maintain `sd_dataset_db`. The README states the rules; this page explains the workflows and the terms.

## Glossary

| Term | Meaning here |
|---|---|
| Session | One recording that is diarized as a unit: a meeting, a call, a video. RTTM files name it in their second field |
| RTTM | NIST Rich Transcription Time Marked format. Each `SPEAKER` line is `SPEAKER <session> <channel> <start> <duration> <NA> <NA> <speaker> <NA> <NA>` |
| UEM | Un-partitioned Evaluation Map: the regions of each session that are scored. Lines are `<session> <channel> <start> <end>` |
| Overlap ratio | Seconds with two or more active speakers divided by seconds with at least one, in percent. `tools/measure.py` merges each speaker's own overlapping segments first and, when a UEM is given, counts only inside it |
| Speakers per session | Number of distinct speaker labels in a session's RTTM |
| Speaker label | The 8th RTTM field. Labels are not always global across sessions, so `n_speakers_measured` may overcount real people |
| Far-field array | Microphone array placed away from the speakers (AMI, AISHELL-4, CHiME-6) |
| Simulated mixture | Conversations built by mixing or replaying single-speaker recordings (LibriCSS, simulation recipes) |
| Turn source | `turn_source`: where speaker turns come from. `provided_segments`: the release has utterances or segments with speaker labels and times. `close_talk_vad`: it has none, but every speaker has a close-talk microphone or a channel of their own (headset, lapel, one side of a call), so turns are cut by VAD per channel. `both`, or `none` (needs new annotation) |
| Usable as | `usable_as`: what a dataset counts as for the hour totals in `views/usable_hours.*`: `train`, `train_split` (train split trains, dev/test evaluate), `eval`, `hold`, `not_used`. Maintainer decisions are `source_type=user`; otherwise it follows from the licence and the published-splits rule. Simulation conditions that are not used are rows in `splits.csv` whose note starts with "Not used" |
| Seed value | A value entered from an assistant's background knowledge at repository creation, without opening a source. Treated as a lead, never as a fact |

## Lifecycle of a dataset row

```
(survey) → candidate ──download──▶ collected
              │  │
              │  └──cost / terms──▶ needs_decision ──maintainer──▶ candidate | excluded
              └──no access found──▶ deferred ──confirmed──▶ candidate | excluded
```

- `candidate` with `unexamined` is the default for a newly found dataset.
- `candidate` with `lab_copy_available` means a copy already exists on the lab's storage but is not registered and measured yet: it has no RTTM to measure, the copy is partial, or it lives outside `$SD_DATA_ROOT`. Say which in `status_note`, without the local path.
- `needs_decision` is for what only the maintainer can decide: LDC fees, signed agreements, terms of use.
- `excluded` needs a clear reason code: no time-aligned speaker labels, single speaker per recording, duplicate, unobtainable.
- `collected` requires a `collections.csv` row, a measurement and no remaining `seed` value.

## License tiers

`license_tier` records what a dataset may be used for. Work it out from the licence text (in the copy we hold and on the current official page), then record it with `tools/db.py ev`, citing the same source as the licence.

| Tier | Licences | Use |
|---|---|---|
| `train` | CC0, CC BY, MIT, Apache-2.0, CDLA-Permissive, public domain | Training and evaluation |
| `eval` | CC BY-SA, CC BY-NC, CC BY-NC-SA, research-only, if redistribution is allowed | Open-set evaluation only |
| `licensed_internal` | LDC, ELRA and other institutional licences; research-only agreements the lab has signed, by maintainer decision | Internal use where the lab holds the licence; the maintainer decides the use |
| `excluded` | NoDerivatives, no redistribution, region-bound or paid terms | Not used |
| `hold` | No licence, `unknown`, `conflicting`, or redistribution terms not known | Undecided |

- `tools/validate.py` enforces the licence side: ND is always `excluded`; LDC and proprietary terms are `licensed_internal` or `excluded`; ShareAlike, NonCommercial and research-only are never `train`; research-only may be `licensed_internal` when the tier's canonical evidence is a maintainer decision (a signed agreement without redistribution, held like an LDC licence); `none_stated`, `unknown`, `conflicting` and `LicenseRef-other` are `hold` or `excluded`, or `eval` when the tier's canonical evidence is a maintainer decision (`source_type=user`); they can never be `train`. A permissive licence may still be `eval` (evaluation-only use narrows it), `hold` or `excluded` (for example terms that differ by part).
- Terms that differ for audio, annotations and video: the tier follows the most restrictive part we use, and `license_note` says which part is which.
- A simulation has no licence of its own. Its tier follows the most restrictive of its speech, noise and RIR sources, which `license_note` lists one by one; when conditions differ (clean vs noise), the row takes the most restrictive one and `license_note` gives the tier per condition.
- Do not set a tier on a licence that is still `seed`: verify the licence first.
- Published splits (maintainer rule, 2026-10-31): where the source defines train, development and test splits, use them as defined: train splits for training, development and test splits for evaluation (a development split may tune). A dataset that publishes only development and test or evaluation splits is evaluation only. Record the use per split in `splits.csv` notes and as `source_type=user` evidence on `license_tier`; a decision that departs from the rule is marked as needing confirmation.
- A tier says what data may be used for, not that an evaluation set is clean: check that it shares no recordings or speakers with the training data.

## Workflow: verify a seed value or survey lead

1. Open `views/needs_verification.csv` and pick a dataset. Its `source_type` column says whether a value is `seed` or `secondary` (a survey lead, whose `notes` keep what the search found).
2. Open the primary source (paper, official page, LICENSE, LDC catalogue entry).
3. For each value:
   - The source agrees → `python3 tools/db.py ev <id> <field> <value> source_type=primary source_ref=<url> locator="<where in the source>"`. The seed row becomes superseded.
   - The source disagrees → the same command with the source's value. The discrepancy shows up in `views/discrepancies.csv`.
   - The source does not say → `ev <id> <field> unknown ...` (if the column allows `unknown`).
   - The value was simply wrong and nothing can replace it (the column does not allow `unknown`, or the field does not apply in the way the seed assumed) → `python3 tools/db.py clear <id> <field> reason="<what was wrong and the source that shows it>"`. The cell becomes empty; the seed row is kept as superseded and its note records the reason. Never delete an evidence row.
4. Fill free-text columns (`license_note`, `notes`) with what you learned, then `python3 tools/views.py && python3 tools/validate.py`.

## Workflow: add a dataset

Scope (maintainer decision, 2026-11-03): any real multi-speaker conversational speech, not only data released for diarization. It qualifies when speaker turns can be obtained: utterance or segment timestamps with speaker labels (`turn_source=provided_segments`), or one close-talk or separate channel per speaker, cut by VAD (`close_talk_vad`). Record `turn_source` with evidence for every new row; a conversation corpus with neither is `none` and stays a candidate only if someone may annotate it.

1. Search first: `grep -i <name> views/datasets_wide.csv data/aliases.csv`. A mirror is an alias, not a row.
2. `python3 tools/db.py add datasets dataset_id=<id> name="<name>" collection_status=candidate status_reason_codes=unexamined last_updated_on=<today>`.
3. Add evidence for every filled evidence column with `tools/db.py ev` (including `collection_status` and `status_reason_codes`).
4. Splits, challenge use and other annotations go to their tables with `tools/db.py add`; each row carries its own source.
5. Views, validate, commit.

## Workflow: collect a dataset

See "Collecting a dataset" in the README. Points to keep in mind:

- `tools/fetch.py` only fetches `access_method=direct_download` datasets whose `download_url` holds checked URLs. LDC and agreement-based data are obtained by hand into `$SD_DATA_ROOT/<dataset_id>/`.
- `rttm_glob`, `uem_glob` and `audio_glob` in `collections.csv` are relative to the dataset directory. Point `rttm_glob` at the reference RTTM of the release you use (for example the full release, not a challenge subset), and say which in `collections.notes`.
- `measurements/<dataset_id>.json` records only the environment variable, never the local path, plus a SHA-1 over the RTTM files so a change of release is visible.
- Reported and measured values differ often (different versions, UEM, scoring regions). Investigate large differences and write the outcome in `notes`.

## Workflow: record a challenge

Add the campaign to `challenges.csv`, then one `challenge_membership.csv` row per dataset and role. Use `train_dev_eval` when the challenge uses the dataset's own splits for several roles, and say which parts in `note`.

## Answering questions from the DB

Look at the row in `views/datasets_wide.csv`, its evidence rows and `views/discrepancies.csv`. Always state the source type of the answer: a value that is still `seed` must be reported as unverified.
