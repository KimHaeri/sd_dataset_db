# Diarization data plan: use, licence, download

Snapshot of 2026-11-01, written for discussion with the PI. It summarises `data/datasets.csv` and
the maintainer decisions recorded in `data/evidence.csv`; where they differ, the CSV tables are
authoritative. Open points are listed under "To confirm".

Rules:

- ShareAlike (SA) and NonCommercial (NC) data is used for evaluation only.
- Published splits are used as defined: train splits for training, dev and test splits for
  evaluation.
- LDC data is used internally only and never redistributed.

Hours, speakers and recording condition are the figures the source reports for its whole
release (paper, official page or LDC catalogue), not what the lab holds; for the two lab
simulations they cover the clean and reverb conditions we use. **—** means the DB has no
verified figure yet.

Download needed: **No** = already on the lab storage (most still need RTTM converted from their
transcripts or annotations), **Yes** = to be downloaded (free), **LDC** = needs an LDC licence,
**Agreement** = needs a signed agreement, **Copy** = lab simulation on purgeable scratch storage,
to be copied to permanent storage, **Partial** = only part of the release is on the lab storage.
Download needed was checked against the lab's shared corpus storage on 2026-11-01.

## Training data

| Dataset | Use | Hours | Speakers (total; per session) | Recording condition | Licence | Download needed | To confirm |
|---|---|---|---|---|---|---|---|
| [AMI](https://groups.inf.ed.ac.uk/ami/corpus/) | Train split | 100 h | — | Meeting; close-talk and far-field arrays | CC BY 4.0 (the release 1.7 licence file says CC BY-NC-SA 2.5) | No | Licence: may we treat it as CC BY 4.0 (current official page), or must we follow CC BY-NC-SA 2.5 (licence file in release 1.7)? Which partition: full-corpus-ASR (BUT setup, 136 / 18 / 16 meetings) recommended |
| [ICSI](https://groups.inf.ed.ac.uk/ami/icsi/) | Train | about 70 h (75 meetings) | — | Meeting; close-talk | CC BY 4.0 | Yes | — |
| [NOTSOFAR-1](https://github.com/microsoft/NOTSOFAR1-Challenge) | Train split | — (237 meetings) | 35; 4-8 per meeting | Meeting; close-talk, far-field arrays and single far-field devices | CC BY 4.0 | Yes | — |
| LibriSpeech simulated meetings (lab) | Train, clean and reverb conditions only (6,000 meetings, about 1,004 h) | about 1,004 h (6,000 meetings) | 2,334 source speakers; 3-8 per meeting | Simulated meetings; clean and simulated-room reverb | [LibriSpeech](https://www.openslr.org/12/) CC BY 4.0 + generated RIRs | Copy | — |
| [Switchboard-1 Release 2](https://catalog.ldc.upenn.edu/LDC97S62) | Train | 260 h (2,400 calls) | 543; 2 per call | Telephone | LDC | No | — |
| Fisher English Training [Part 1](https://catalog.ldc.upenn.edu/LDC2004S13) and [Part 2](https://catalog.ldc.upenn.edu/LDC2005S13) | Train | 984 h + 975 h (11,699 calls) | 2 per call | Telephone | LDC | No | — |
| Fisher simulated meetings (lab) | Train, clean and reverb conditions only (6,000 meetings) | about 1,004 h (6,000 meetings) | 8,400 source speakers; 3-8 per meeting | Simulated meetings; clean and simulated-room reverb | LDC (built from Fisher) + generated RIRs | Copy | — |
| [CALLHOME Spanish](https://catalog.ldc.upenn.edu/LDC96S35) | Train split (devtest and evltest: evaluation) | 38 h (120 calls) | — | Telephone | LDC | No | — |
| [CALLHOME American English](https://catalog.ldc.upenn.edu/LDC97S42) | Train split (development and evaluation data: evaluation) | 56 h (120 calls) | — | Telephone | LDC | No | Transcripts (LDC97T14) or RTTM: purchase or find? |
| [Mixer 6 - CHiME 8](https://catalog.ldc.upenn.edu/LDC2025S07) | Train split (dev and test: evaluation) | 80 h of speech (1,063 h of audio over 13 microphones) | — | Interviews and telephone calls | LDC | Partial | Is the lab copy the same as LDC2025S07? |
| [MSP-Conversation](https://lab-msp.com/MSP/MSP-Conversation.html) | Train partition (development and test: evaluation) | 59.6 h (244 conversations, v1.1) | — | Podcasts | Research-only agreement, no redistribution (held like LDC) | No (outside the shared corpus storage) | Who signed the agreement for the lab copy? It covers only that person and the people they supervise |
| [Ego4D](https://ego4d-data.org/) Audio-Visual Diarization | Train split (val and test: evaluation) | — | — | Egocentric video; wearable camera | Signed licence agreement | No | Who signed the agreement for the lab copy? Only an institutional signature covers a shared copy |

## Evaluation data

| Dataset | Use | Hours | Speakers (total; per session) | Recording condition | Licence | Download needed | To confirm |
|---|---|---|---|---|---|---|---|
| [AISHELL-4](https://www.openslr.org/111/) | Eval | 120 h (211 meetings) | 60; 4-8 per meeting | Meeting; far-field array | CC BY-SA 4.0 | No | — |
| [AliMeeting](https://www.openslr.org/119/) | Eval | 118.75 h (240 meetings) | 2-4 per meeting | Meeting; close-talk and far-field array | CC BY-SA 4.0 | No | — |
| [CHiME-6](https://openslr.org/150/) | Eval | — (20 sessions) | 4 per session | Dinner party at home; binaural close-talk and far-field arrays | CC BY-SA 4.0 | No | — |
| [CHiME-5](https://www.chimechallenge.org/datasets/chime5) | Eval | 50.2 h (20 sessions) | 48; 4 per session | Dinner party at home; binaural close-talk and far-field arrays | CC BY-SA 4.0 | No | Licence: the copy's licence file is non-commercial, the plan says CC BY-SA 4.0 |
| [Seamless Interaction](https://huggingface.co/datasets/facebook/seamless-interaction) | Eval | — | 2 per conversation | Two-person conversation; one channel per participant | CC BY-NC 4.0 | No | — |
| [Earnings-21](https://github.com/revdotcom/speech-datasets/tree/main/earnings21) | Eval | 39.25 h (44 calls) | 2-20 per call | Earnings calls | Transcripts CC BY-SA 4.0; audio under a fair-use claim | Yes | — |
| [LibriCSS](https://github.com/chenzhuo1011/libri_css) | Eval | 10 h (10 sessions) | 40; 8 per session | LibriSpeech replayed in a room; far-field array | No licence stated for the recordings | Yes | — |
| [VoxConverse](https://github.com/joonson/voxconverse) | Eval | 63.8 h (448 videos) | — | Broadcast and web video | CC BY 4.0 (video copyright stays with its owners) | No | — |
| [DISPLACE 2023](https://zenodo.org/records/8375161) | Eval | about 31.5 h (Dev about 15.5 h) | 3-5 per session | Conversation; single far-field microphone | CC BY 4.0 | Yes | — |
| [RT-03 evaluation set](https://catalog.ldc.upenn.edu/LDC2007S10) | Eval | — | — | Broadcast news and telephone | LDC | No | — |
| [NIST SRE 2000 CALLHOME](https://catalog.ldc.upenn.edu/LDC2001S97) | Eval | — | — | Telephone | LDC | No | — |
| [DIHARD III development set](https://catalog.ldc.upenn.edu/LDC2022S12) | Eval | 34.15 h (254 recordings) | — | 11 domains (meetings, clinical interviews, telephone, audiobooks, ...) | LDC | No | — |
| [DIHARD III evaluation set](https://catalog.ldc.upenn.edu/LDC2022S14) | Eval | 33.01 h (259 recordings) | — | 11 domains (meetings, clinical interviews, telephone, audiobooks, ...) | LDC | No | — |
| [DiPCo](https://cdn.amazon.science/ec/9b/de4df24f4aff87aee591b58f9ff5/dipco-dinner-party-corpus.pdf) | Eval | 5.32 h (10 sessions) | 32; 4 per session | Dinner party; close-talk and far-field arrays | CDLA-Permissive-1.0 | No | — |

## Not used or undecided

| Dataset | Status | Hours | Speakers (total; per session) | Recording condition | Licence | Download needed | To confirm |
|---|---|---|---|---|---|---|---|
| [MSDWild](https://github.com/X-LANCE/MSDWILD) | Undecided | 80.05 h (3,143 videos) | 2-10 per video | Web video (vlogs) | Research-only agreement, no redistribution | Agreement | Sign? Use for training or evaluation? |
| [AVA-AVD](https://github.com/zcxu-eric/AVA-AVD) | Excluded | 29.25 h (351 five-minute clips from 117 movies) | 1,500; 2-24 per clip | Movies without dubbing; more than 6 languages | Annotations MIT; no licence stated for the movie videos | — | — |
| [MagicData-RAMC](https://www.openslr.org/123/) | Excluded | 180 h (351 conversations) | 663 | Conversation; mobile phone | CC BY-NC-ND 4.0 | — | — |
| [Mixer 6 Speech](https://catalog.ldc.upenn.edu/LDC2013S03) | Excluded (no speaker segments) | 15,863 h | 594 | Interviews and telephone calls | LDC | — | — |
