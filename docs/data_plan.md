# Diarization data plan: use, licence, download

Snapshot of 2026-10-31, written for discussion with the PI. It summarises `data/datasets.csv` and
the maintainer decisions recorded in `data/evidence.csv`; where they differ, the CSV tables are
authoritative. Open points are listed under "To confirm".

Rules:

- ShareAlike (SA) and NonCommercial (NC) data is used for evaluation only.
- Published splits are used as defined: train splits for training, dev and test splits for
  evaluation.
- LDC data is used internally only and never redistributed.

Download needed: **No** = already on the lab storage (most still need RTTM converted from their
transcripts or annotations), **Yes** = to be downloaded (free), **LDC** = needs an LDC licence,
**Agreement** = needs a signed agreement, **Copy** = lab simulation on purgeable scratch storage,
to be copied to permanent storage.

## Training data

| Dataset | Use | Licence | Download needed | To confirm |
|---|---|---|---|---|
| [AMI](https://groups.inf.ed.ac.uk/ami/corpus/) | Train split | CC BY 4.0 (the release 1.7 licence file says CC BY-NC-SA 2.5) | No | Licence: may we treat it as CC BY 4.0 (current official page), or must we follow CC BY-NC-SA 2.5 (licence file in release 1.7)? Which partition: full-corpus-ASR (BUT setup, 136 / 18 / 16 meetings) recommended |
| [ICSI](https://groups.inf.ed.ac.uk/ami/icsi/) | Train | CC BY 4.0 | Yes | — |
| [NOTSOFAR-1](https://github.com/microsoft/NOTSOFAR1-Challenge) | Train split | CC BY 4.0 | Yes (Hugging Face token) | — |
| LibriSpeech simulated meetings (lab) | Train, clean and reverb conditions only (6,000 meetings, about 1,004 h) | [LibriSpeech](https://www.openslr.org/12/) CC BY 4.0 + generated RIRs | Copy | — |
| [Switchboard-1 Release 2](https://catalog.ldc.upenn.edu/LDC97S62) | Train | LDC | No | — |
| Fisher English Training [Part 1](https://catalog.ldc.upenn.edu/LDC2004S13) and [Part 2](https://catalog.ldc.upenn.edu/LDC2005S13) | Train | LDC | No | — |
| Fisher simulated meetings (lab) | Train, clean and reverb conditions only (6,000 meetings) | LDC (built from Fisher) + generated RIRs | Copy | — |
| [CALLHOME Spanish](https://catalog.ldc.upenn.edu/LDC96S35) | Train split (devtest and evltest: evaluation) | LDC | No | — |
| [CALLHOME American English](https://catalog.ldc.upenn.edu/LDC97S42) | Train split (development and evaluation data: evaluation) | LDC | LDC | Check overlap with the HUB5 English evaluation sets drawn from it (the 2000 set, LDC2002S09, is on the lab storage) |
| [Mixer 6 - CHiME 8](https://catalog.ldc.upenn.edu/LDC2025S07) | Train split (dev and test: evaluation) | LDC | LDC | — |
| [Ego4D](https://ego4d-data.org/) Audio-Visual Diarization | Train split (val and test: evaluation) | Signed licence agreement | Agreement | Sign? An individual or the institution |

## Evaluation data

| Dataset | Use | Licence | Download needed | To confirm |
|---|---|---|---|---|
| [AISHELL-4](https://www.openslr.org/111/) | Eval | CC BY-SA 4.0 | No (measured) | — |
| [AliMeeting](https://www.openslr.org/119/) | Eval | CC BY-SA 4.0 | Partial (only Test on the lab storage) | — |
| [CHiME-6](https://openslr.org/150/) | Eval | CC BY-SA 4.0 | No (re-release of the CHiME-5 recordings with their audio alignment fixed) | — |
| [CHiME-5](https://www.chimechallenge.org/datasets/chime5) | Eval | CC BY-SA 4.0 | No (use the CHiME-6 copy) | — |
| [Seamless Interaction](https://huggingface.co/datasets/facebook/seamless-interaction) | Eval | CC BY-NC 4.0 | No (audio, improvised sessions only) | — |
| [Earnings-21](https://github.com/revdotcom/speech-datasets/tree/main/earnings21) | Eval | Transcripts CC BY-SA 4.0; audio under a fair-use claim | Yes | — |
| [LibriCSS](https://github.com/chenzhuo1011/libri_css) | Eval | No licence stated for the recordings | Yes | — |
| [VoxConverse](https://github.com/joonson/voxconverse) | Eval | CC BY 4.0 (video copyright stays with its owners) | Yes | — |
| [DISPLACE 2023](https://zenodo.org/records/8375161) | Eval | CC BY 4.0 | Yes (Dev only; Eval not released) | — |
| [RT-03 evaluation set](https://catalog.ldc.upenn.edu/LDC2007S10) | Eval | LDC | No | — |
| [NIST SRE 2000 CALLHOME](https://catalog.ldc.upenn.edu/LDC2001S97) | Eval | LDC | LDC | — |
| [DIHARD III development set](https://catalog.ldc.upenn.edu/LDC2022S12) | Eval | LDC | LDC | — |
| [DIHARD III evaluation set](https://catalog.ldc.upenn.edu/LDC2022S14) | Eval | LDC | LDC | — |

## Not used or undecided

| Dataset | Status | Licence | Download needed | To confirm |
|---|---|---|---|---|
| [MSP-Conversation](https://lab-msp.com/MSP/MSP-Conversation.html) | Hold | Research-only agreement | No (v1.1; v2.0 exists) | Who signed the agreement for the lab copy? |
| [MSDWild](https://github.com/X-LANCE/MSDWILD) | Hold | Research-only agreement | Agreement | Sign? |
| [AVA-AVD](https://github.com/zcxu-eric/AVA-AVD) | Undecided | Annotations MIT; video rights unclear | Yes (lab storage not checked) | Proposed: hold |
| [DiPCo](https://cdn.amazon.science/ec/9b/de4df24f4aff87aee591b58f9ff5/dipco-dinner-party-corpus.pdf) | Deferred (planned for evaluation) | CDLA-Permissive-1.0 | Not available (the download link in the paper returns 403) | A working download link? |
| [MagicData-RAMC](https://www.openslr.org/123/) | Excluded | CC BY-NC-ND 4.0 | — | — |
| [Mixer 6 Speech](https://catalog.ldc.upenn.edu/LDC2013S03) | Excluded (no speaker segments) | LDC | — | — |
