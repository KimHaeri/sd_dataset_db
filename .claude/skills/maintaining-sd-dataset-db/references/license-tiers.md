# License tiers: which data may train, which may only evaluate

The DB records the licence (`license_spdx`, `license_note`). The tier, meaning what the data may
be used for, is worked out from the licence with the rules below. `license_class` is **not** the
tier: it puts CC-BY-SA in `open`, but for the tier SA is "less safe".

The tier is stored in `datasets.license_tier`, with evidence like any other value. Cite the same
source as the licence. `tools/validate.py` rejects a tier the licence does not allow (see
`allowed_tiers` in it, and the "License tiers" section of `docs/manual.md`). Leave the tier empty
while the licence is still `seed`.

## The tiers

| Tier | Licences | Use |
|---|---|---|
| `train` | CC0-1.0, CC-BY (any version), MIT, Apache-2.0, CDLA-Permissive-1.0/2.0, public domain | Training, and evaluation as well |
| `eval` | CC-BY-SA, CC-BY-NC, CC-BY-NC-SA, `LicenseRef-custom-research-only`, **only if redistribution is allowed** | Open-set evaluation only, never training |
| `licensed_internal` | `LicenseRef-LDC-member-or-nonmember`, ELRA and similar institutional licences; `LicenseRef-custom-research-only` under a signed agreement, by maintainer decision only | Kept as its own pool. Internal use only, and only where the lab holds the licence for that release. Never redistributed. Whether it enters training or evaluation is the maintainer's decision |
| `excluded` | Any ND (NoDerivatives; cutting, excerpting or relabelling can count as adaptation), terms that forbid redistribution, region-bound obligations, paid licences outside `licensed_internal` | Not used |
| `hold` | `none_stated`, `unknown`, `conflicting`, or a research-only licence whose redistribution terms are not known | Undecided: find the missing fact or ask the maintainer. Do not pick a tier for it |

Two cases come up often:
- **Academic licence signed by the institution.** Such a licence usually forbids redistribution, so
  the data is `hold` until the terms are read. It is not automatically `eval`.
- **Licences that differ by part.** When audio, annotations and video have different terms, the
  tier follows the most restrictive part that we use. For diarization that means the audio plus
  the speaker segments.

## Checks before assigning a tier

1. **Read the licence text itself, not only the tag on a card.** Read it in the copy we hold
   (`LICENSE`, `LICENCE.txt`, readme) and on the current official page. The two can differ
   because datasets are relicensed between releases. Example: AMI's official page says CC BY 4.0,
   but the annotation release 1.7 on the lab storage ships a `LICENCE.txt` with CC BY-NC-SA 2.5.
   Record both as evidence, both rows `conflicting`, with `license_spdx=conflicting` and tier
   `hold`, unless a source says one replaces the other. Let the maintainer decide.
2. **Check the platform's terms.** A CC BY dataset on a platform that forbids mirroring cannot be
   re-hosted from that copy. Corpora that publish only labels plus video IDs have audio under
   the video site's terms. Do not scrape.
3. **Trace provenance.** A mirror cannot grant more rights than its source. Hub mirrors sometimes
   relabel a restricted corpus as MIT; use the official source.
4. **Simulated mixtures** are no more permissive than their most restrictive input. That includes
   the speech source, the **noise source and the RIR source**. A simulation may be `train` for its
   clean and reverb conditions (permissive speech, generated RIRs) and `hold` for its noise
   conditions when the noise set states no licence. Record each source with its own licence in
   `license_note`.
5. **Derived RTTM inherits the licence of the corpus it came from.** This covers RTTM converted
   from transcripts, from NXT XML, or written by a third party.
6. **Check who made the content and how.** Was it recorded by the publisher, collected with
   consent, or scraped? Is it synthetic (TTS, voice conversion)? Synthetic speech belongs only to
   simulated data that is marked as such.

## Keep evaluation apart from training

A tier says what a dataset *may* be used for. It does not make evaluation clean. An evaluation set
must not share recordings or speakers with anything used for training, directly or indirectly.
Indirect sharing means simulation sources whose speakers appear in the evaluation set,
re-releases or subsets of the same meetings, or corpora built from another corpus. Examples to
check, not conclusions:
- LibriCSS and Sparse LibriMix are built from LibriSpeech test-clean.
- RT-03 CTS contains Fisher calls.
- CHiME-6 re-releases CHiME-5.

Record what you checked in `notes` or in `relations`, and only when a source states it.

## Published splits

Maintainer rule (2026-10-31): where the source defines train, development and test splits, use them
as defined. Train splits are for training; development and test splits are for evaluation (a
development split may tune). A dataset that publishes only development and test or evaluation
splits (VoxConverse, DiPCo, DISPLACE 2023) is evaluation only, so its tier is `eval` even when
the licence would allow training. Write the use per split into the `splits.csv` notes. A
decision that departs from the rule (DIHARD III's development set) stays marked as needing
confirmation until the maintainer settles it.

## What the maintainer decides

The tier of a `hold` dataset. Whether `licensed_internal` data is used, and for what. Any
licence interpretation the rules above do not settle. Record their answer with
`source_type=user` and the date the decision was made.

A maintainer may move a dataset with a missing or unclear licence (`none_stated`, `unknown`,
`conflicting`, `LicenseRef-other`) from `hold` to `eval`, typically because it was built as an
evaluation set (Earnings-21, LibriCSS). `validate.py` accepts that only when the tier's canonical
evidence is `source_type=user`, and never accepts `train` for such a licence. Say in the evidence
note that the decision was made knowing the licence gap.
