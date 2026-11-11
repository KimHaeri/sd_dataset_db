# Diarization data plan: use, licence, download

Snapshot of 2026-11-01, written for discussion with the PI. It summarises `data/datasets.csv` and
the maintainer decisions recorded in `data/evidence.csv`; where they differ, the CSV tables are
authoritative. Open points are listed under "To confirm".

Rules:

- ShareAlike (SA) and NonCommercial (NC) data is used for evaluation only.
- Published splits are used as defined: train splits for training, dev and test splits for
  evaluation.
- LDC data is used internally only and never redistributed. Training on LDC data needs the PI's review first (2026-11-08): those rows say "Needs review".

Hours, speakers and recording condition are the figures the source reports for its whole
release (paper, official page or LDC catalogue), not what the lab holds; for the two lab
simulations they cover the clean and reverb conditions we use. **—** means the DB has no
verified figure yet. Figures with "about" or "over" are the source's own approximations.

Download needed: **No** = already on the lab storage (most still need RTTM converted from their
transcripts or annotations), **Yes** = to be downloaded (free), **LDC** = needs an LDC licence,
**Agreement** = needs a signed agreement, **Partial** = only part of the release is on the lab storage.
Download needed was checked against the lab's shared corpus storage on 2026-11-01.

## Training data

| Dataset | Use | Hours | Speakers (total; per session) | Recording condition | Licence | Download needed | To confirm |
|---|---|---|---|---|---|---|---|
| [AMI](https://groups.inf.ed.ac.uk/ami/corpus/) | Train split of the full-corpus-ASR partition (dev and eval: evaluation) | 100 h (lab copy: 99.97 h; train 80.67, dev 9.67, eval 9.06) | — | Meeting; close-talk and far-field arrays | CC BY 4.0 (the release 1.7 licence file says CC BY-NC-SA 2.5) | No | — |
| [ICSI](https://groups.inf.ed.ac.uk/ami/icsi/) | Train | about 70 h (75 meetings) | — | Meeting; close-talk | CC BY 4.0 | Yes | — |
| [NOTSOFAR-1](https://github.com/microsoft/NOTSOFAR1-Challenge) | Train split | 237 meetings of about 6 min (about 150 h single-channel and 110 h multi-channel over all devices) | 35; 4-8 per meeting | Meeting; close-talk, far-field arrays and single far-field devices | CC BY 4.0 | Yes | — |
| LibriSpeech simulated meetings (lab) | Train, clean and reverb conditions only (6,000 meetings, about 1,004 h) | about 1,004 h (6,000 meetings) | 2,334 source speakers; 3-8 per meeting | Simulated meetings; clean and simulated-room reverb | [LibriSpeech](https://www.openslr.org/12/) CC BY 4.0 + generated RIRs | No | — |
| [Switchboard-1 Release 2](https://catalog.ldc.upenn.edu/LDC97S62) | **Needs review** (LDC training use on hold) | 260 h (2,400 calls) | 543; 2 per call | Telephone | LDC | No | — |
| Fisher English Training [Part 1](https://catalog.ldc.upenn.edu/LDC2004S13) and [Part 2](https://catalog.ldc.upenn.edu/LDC2005S13) | **Needs review** (LDC training use on hold) | 984 h + 975 h (11,699 calls) | 2 per call | Telephone | LDC | No | — |
| Fisher simulated meetings (lab) | **Needs review** (built from Fisher, LDC; clean and reverb conditions only) | about 1,004 h (6,000 meetings) | 8,400 source speakers; 3-8 per meeting | Simulated meetings; clean and simulated-room reverb | LDC (built from Fisher) + generated RIRs | No | — |
| [CALLHOME Spanish](https://catalog.ldc.upenn.edu/LDC96S35) | **Needs review** (LDC; all use on hold, evaluation splits included, until discussed with the PI) | 38 h (120 calls) | — | Telephone | LDC | No | — |
| [CALLHOME American English](https://catalog.ldc.upenn.edu/LDC97S42) | **Needs review** (LDC; all use on hold, evaluation splits included, until discussed with the PI) | 56 h (120 calls) | — | Telephone | LDC | No | Transcripts (LDC97T14) or RTTM: purchase or find? |
| [Mixer 6 - CHiME 8](https://catalog.ldc.upenn.edu/LDC2025S07) | **Needs review** (LDC; all use on hold, evaluation splits included, until discussed with the PI) | 80 h of speech (1,063 h of audio over 13 microphones) | — | Interviews and telephone calls | LDC | Partial | Is the lab copy the same as LDC2025S07? |
| [MSP-Conversation](https://lab-msp.com/MSP/MSP-Conversation.html) | Train partition (development and test: evaluation) | 59.6 h (244 conversations, v1.1) | — | Podcasts | Research-only agreement, no redistribution (held like LDC) | No (outside the shared corpus storage) | — |
| [Ego4D](https://ego4d-data.org/) Audio-Visual Diarization | Train split (val and test: evaluation) | about 50 h annotated (572 clips of 5 min) | — | Egocentric video; wearable camera | Signed licence agreement | No | Who signed the agreement for the lab copy? Only an institutional signature covers a shared copy |

## Evaluation data

| Dataset | Use | Hours | Speakers (total; per session) | Recording condition | Licence | Download needed | To confirm |
|---|---|---|---|---|---|---|---|
| [AISHELL-4](https://www.openslr.org/111/) | Eval | 120 h (211 meetings) | 60; 4-8 per meeting | Meeting; far-field array | CC BY-SA 4.0 | No | — |
| [AliMeeting](https://www.openslr.org/119/) | Eval | 118.75 h (240 meetings) | 2-4 per meeting | Meeting; close-talk and far-field array | CC BY-SA 4.0 | No | — |
| [CHiME-6](https://openslr.org/150/) | Eval | 50.2 h (20 sessions; same recordings as CHiME-5) | 4 per session | Dinner party at home; binaural close-talk and far-field arrays | CC BY-SA 4.0 | No | — |
| [CHiME-5](https://www.chimechallenge.org/datasets/chime5) | Eval | 50.2 h (20 sessions) | 48; 4 per session | Dinner party at home; binaural close-talk and far-field arrays | CC BY-SA 4.0 | No | Licence: the copy's licence file is non-commercial, the plan says CC BY-SA 4.0 |
| [Seamless Interaction](https://huggingface.co/datasets/facebook/seamless-interaction) | Eval | over 4,000 h in the full release (the lab copy has the improvised part only) | 2 per conversation | Two-person conversation; one channel per participant | CC BY-NC 4.0 | No | — |
| [Earnings-21](https://github.com/revdotcom/speech-datasets/tree/main/earnings21) | Eval | 39.25 h (44 calls) | 2-20 per call | Earnings calls | Transcripts CC BY-SA 4.0; audio under a fair-use claim | Yes | — |
| [LibriCSS](https://github.com/chenzhuo1011/libri_css) | Eval | 10 h (10 sessions) | 40; 8 per session | LibriSpeech replayed in a room; far-field array | No licence stated for the recordings | Yes | — |
| [VoxConverse](https://github.com/joonson/voxconverse) | Eval | 63.8 h (448 videos) | — | Broadcast and web video | CC BY 4.0 (video copyright stays with its owners) | No | — |
| [DISPLACE 2023](https://zenodo.org/records/8375161) | Eval | about 31.5 h (Dev about 15.5 h) | 3-5 per session | Conversation; single far-field microphone | CC BY 4.0 | Yes | — |
| [RT-03 evaluation set](https://catalog.ldc.upenn.edu/LDC2007S10) | Eval | about 9 h for diarization (broadcast news about 3 h, telephone about 6 h) | — | Broadcast news and telephone | LDC | No | — |
| [NIST SRE 2000 CALLHOME](https://catalog.ldc.upenn.edu/LDC2001S97) | Eval | — | — | Telephone | LDC | No | — |
| [DIHARD III development set](https://catalog.ldc.upenn.edu/LDC2022S12) | Eval | 34.15 h (254 recordings) | — | 11 domains (meetings, clinical interviews, telephone, audiobooks, ...) | LDC | No | — |
| [DIHARD III evaluation set](https://catalog.ldc.upenn.edu/LDC2022S14) | Eval | 33.01 h (259 recordings) | — | 11 domains (meetings, clinical interviews, telephone, audiobooks, ...) | LDC | No | — |
| [DiPCo](https://cdn.amazon.science/ec/9b/de4df24f4aff87aee591b58f9ff5/dipco-dinner-party-corpus.pdf) | Eval | 5.32 h (10 sessions) | 32; 4 per session | Dinner party; close-talk and far-field arrays | CDLA-Permissive-1.0 | No | — |
| [MSDWild](https://github.com/X-LANCE/MSDWILD) | Eval | 80.05 h (3,143 videos) | 2-10 per video | Web video (vlogs) | Research-only agreement, no redistribution | Agreement | Sign? Which splits: few_val and many_val only, or few_train as well? |

## Not used or undecided

| Dataset | Status | Hours | Speakers (total; per session) | Recording condition | Licence | Download needed | To confirm |
|---|---|---|---|---|---|---|---|
| [AVA-AVD](https://github.com/zcxu-eric/AVA-AVD) | Excluded | 29.25 h (351 five-minute clips from 117 movies) | 1,500; 2-24 per clip | Movies without dubbing; more than 6 languages | Annotations MIT; no licence stated for the movie videos | — | — |
| [MagicData-RAMC](https://www.openslr.org/123/) | Excluded | 180 h (351 conversations) | 663 | Conversation; mobile phone | CC BY-NC-ND 4.0 | — | — |
| [Mixer 6 Speech](https://catalog.ldc.upenn.edu/LDC2013S03) | Candidate since 2026-11-04 (telephone calls: one channel per side, turns by VAD); not on the lab storage | 15,863 h | 594 | Interviews and telephone calls | LDC | — | — |

## New candidates checked on 2026-11-03 and 2026-11-04 (not discussed yet)

Found by the conversation survey and the re-scan of the lab storage, and checked against their pages; the use follows the licence under the current rules and still needs the maintainer's decision. Hours as stated by the source ("—": only approximate figures, see the DB). Unchecked leads are in `docs/conversation_survey.md` and `views/needs_verification.csv`.

### Train (22)

| Dataset | Hours | Speaker turns | Licence | Download needed |
|---|---|---|---|---|
| [AMERICAN ENGLISH TRANSCRIBED HI-FI FULL-DUPLEX TWO-SPEAKER CONVERSATIONAL DATASET — SAMPLE (Ocular AI)](https://huggingface.co/datasets/OcularAIInc/AMERICAN-ENGLISH-TRANSCRIBED-HIFI-FULL-DUPLEX-TWO-SPEAKER-CONVERSATIONAL-DATASET-SAMPLE) | 1.01 h | timed segments and channel per speaker | CC BY 4.0 | Yes (gated) |
| [DataHive Conversations samples](https://huggingface.co/datasets/datahiveai/multilingual-conversations-sample) | 19.53 h | channel per speaker (VAD) | CC BY 4.0 | Yes |
| [EgoCom (Egocentric Communications)](https://github.com/facebookresearch/EgoCom-Dataset) | — | timed segments and channel per speaker | MIT | Yes |
| [Fearless Steps Challenge corpus (Apollo, FS-1 to FS-4)](https://fearless-steps.github.io/ChallengePhase4/) | 100 h | timed segments | CC BY 4.0 | Request |
| [Gridspace-Stanford Harper Valley speech dataset](https://github.com/cricketclub/gridspace-stanford-harper-valley) | — | timed segments | CC BY 4.0 | No (lab copy) |
| [HCRC Map Task Corpus](https://groups.inf.ed.ac.uk/maptask/) | — | timed segments and channel per speaker | CC BY 4.0 | Yes |
| [Indic High-Fidelity MultiSpeaker ASR (Humyn Labs)](https://huggingface.co/datasets/humyn-labs/Indic-High-Fidelity-MultiSpeaker-ASR) | — | timed segments | CC BY 4.0 | Yes |
| [Kallaama (Wolof, Pulaar, Sereer)](https://www.openslr.org/151/) | — | not confirmed | CC BY 4.0 | Yes |
| [Kenya/Philippines English Dialogue (Reord-AI)](https://huggingface.co/datasets/Reord-AI/kenya-philippines-twospeaker-english-dialogue) | — | channel per speaker (VAD) | CC BY 4.0 | Yes (gated) |
| [Multi-TPC (three-party conversations)](https://zenodo.org/records/17935560) | — | timed segments and channel per speaker | CC BY 4.0 | Yes |
| [NB Samtale (Norwegian Conversation Speech Corpus)](https://www.nb.no/sprakbanken/en/resource-catalogue/oai-nb-no-sbr-85/) | 24 h | timed segments | CC0 1.0 | Yes |
| [Norwegian Parliamentary Speech Corpus (NPSC)](https://www.nb.no/sprakbanken/ressurskatalog/oai-nb-no-sbr-58/) | 140.3 h | timed segments | CC0 1.0 | No (lab copy) |
| [otoSpeech-full-duplex-280h](https://huggingface.co/datasets/otoearth/otoSpeech-full-duplex-280h) | — | not confirmed | CC BY 4.0 | Yes (gated) |
| [otoSpeech-full-duplex-task-oriented-20h](https://huggingface.co/datasets/otoearth/otoSpeech-full-duplex-task-oriented-20h) | 20.005954 h | channel per speaker (VAD) | CC BY 4.0 | Yes (gated) |
| [otoSpeech-full-duplex-task-oriented-v2](https://huggingface.co/datasets/otoearth/otoSpeech-full-duplex-task-oriented-v2) | 17.376131 h | channel per speaker (VAD) | CC BY 4.0 | Yes (gated) |
| [Perit Duplex Support Conversations (English)](https://huggingface.co/datasets/perit-ai/perit-duplex-support-en) | 5.10 h | channel per speaker (VAD) | CC BY 4.0 | Yes |
| [PriMock57](https://github.com/babylonhealth/primock57) | — | timed segments | CC BY 4.0 | Yes |
| [Real-TurnTurk](https://huggingface.co/datasets/tugrulbayrak/Real-TurnTurk) | 1.94 h | timed segments and channel per speaker | Apache 2.0 | Yes |
| [Simsamu](https://huggingface.co/datasets/medkit/simsamu) | 3.25 h | timed segments | MIT | Yes |
| [SpiCE: Speech in Cantonese and English](https://doi.org/10.5683/SP2/MJOXP3) | — | channel per speaker (VAD) | CC BY 4.0 | Yes |
| [Spjallrómur - Icelandic Conversational Speech](https://repository.clarin.is/repository/xmlui/handle/20.500.12537/379) | 21.33 h | timed segments and channel per speaker | CC BY 4.0 | Yes |

### Eval (8)

| Dataset | Hours | Speaker turns | Licence | Download needed |
|---|---|---|---|---|
| [AISHELL-5](https://www.openslr.org/159/) | — | timed segments and channel per speaker | CC BY-SA 4.0 | No (lab copy) |
| [ASCEND: A Spontaneous Chinese-English Dataset for Code-switching in Multi-turn Conversation](https://huggingface.co/datasets/CAiRE/ASCEND) | 10.62 h | timed segments | CC BY-SA 4.0 | Yes |
| Dinner Party Corpus (DiPCo) | 5.32 h | timed segments and channel per speaker | CDLA-Permissive-1.0 | No (lab copy) |
| [Earnings-22](https://huggingface.co/datasets/revdotcom/earnings22) | — | not confirmed | CC BY-SA 4.0 | No (lab copy) |
| [Expresso](https://speechbot.github.io/expresso/) | — | not confirmed | CC BY-NC 4.0 | No (lab copy) |
| [Indic DiarBench](https://huggingface.co/datasets/sarvamai/indic-diarbench) | — | timed segments | CC BY 4.0 | Yes |
| [SpokenWOZ](https://spokenwoz.github.io/SpokenWOZ-github.io/) | 249 h | timed segments | CC BY-NC 4.0 | No (lab copy) |
| [VoxMM](https://mm.kaist.ac.kr/projects/voxmm/) | — | timed segments | CC BY 4.0 | Request |

### Internal (LDC or agreement; LDC training use needs the PI's review) (7)

| Dataset | Hours | Speaker turns | Licence | Download needed |
|---|---|---|---|---|
| [2000 HUB5 English Evaluation Speech and Transcripts](https://catalog.ldc.upenn.edu/LDC2002S09) | — | timed segments and channel per speaker | LDC | No (lab copy) |
| [Fisher Spanish Speech](https://catalog.ldc.upenn.edu/LDC2010S01) | 163 h | timed segments and channel per speaker | LDC | No (lab copy) |
| [IARPA Babel language packs](https://catalog.ldc.upenn.edu/LDC2016S02) | — | timed segments and channel per speaker | LDC | No (lab copy) |
| [Mandarin-English Code-Switching in South-East Asia (SEAME)](https://catalog.ldc.upenn.edu/LDC2015S04) | 192 h | not confirmed | LDC | No (lab copy) |
| [Open Yap 1K](https://theagenticdatacompany.com/open-yap-1k) | 1000.245 h | timed segments and channel per speaker | Signed agreement, no redistribution | No (lab copy) |
| Switchboard-1 Release 2 | 260 h | timed segments and channel per speaker | LDC | No (lab copy) |
| synth-fisher-meetings | 2007.24 h | timed segments |  | No (lab copy) |

### Undecided (22)

| Dataset | Hours | Speaker turns | Licence | Download needed |
|---|---|---|---|---|
| [AphasiaBank](https://talkbank.org/aphasia/) | — | timed segments | CC BY-NC-SA 4.0 | No (lab copy) |
| [Australian Parliamentary Speech Corpus - Proof of Concept (turns, 2026-03-30)](https://huggingface.co/datasets/stcoats/au-parliament-poc-turns-2026-03-30) | — | timed segments | CC BY 4.0 | Yes |
| [Bangla-10K (multi_speaker config)](https://huggingface.co/datasets/psdn-ai/bangla-10k) | 3534 h | timed segments and channel per speaker | Other (see DB) | Agreement |
| [Bengali-Loop speaker diarization benchmark (DL Sprint 4.0; HF copy AdilShamim8/Bengali-Speaker-Diarization_dataset)](https://www.kaggle.com/competitions/dl-sprint-4-0-bengali-speaker-diarization-challenge/data) | 22.0 h | timed segments | Conflicting statements | Yes |
| [CantoMap (Cantonese MapTask corpus)](https://github.com/gwinterstein/CantoMap) | 12.8 h | timed segments and channel per speaker | Other (see DB) | Request |
| [DementiaBank](https://talkbank.org/dementia/) | — | not confirmed | CC BY-NC-SA 4.0 | No (lab copy) |
| [DISPLACE-M 2026](https://displace2026.github.io/) | — | timed segments | Conflicting statements | Agreement |
| [Earnings25](https://doi.org/10.5281/zenodo.18762167) | — | timed segments | CC BY 4.0 | Yes |
| [GaMMA Corpus (Gaze, Motion, and Multi-talker Audio)](https://zenodo.org/records/18343509) | — | channel per speaker (VAD) | Conflicting statements | Yes |
| [Highland Puebla Nahuatl Speech with Transcription (OpenSLR 92)](https://www.openslr.org/92/) | — | timed segments and channel per speaker | Conflicting statements | No (lab copy) |
| [IFA Dialog Video corpus (IFADV)](https://www.fon.hum.uva.nl/IFA-SpokenLanguageCorpora/IFADVcorpus/) | 5 h | timed segments and channel per speaker | Other (see DB) | Yes |
| [IMDA National Speech Corpus (NSC), conversational part (Part 3)](https://www.imda.gov.sg/how-we-can-help/national-speech-corpus) | — | channel per speaker (VAD) | Other (see DB) | Request |
| [Maleo Short](https://huggingface.co/datasets/maleo-ai/maleo-short) | — | timed segments | CC BY 4.0 | Yes (gated) |
| [MISP-M3SD](https://huggingface.co/datasets/Igor97/MISP-M3SD) | 770.55 h | timed segments | Apache 2.0 | Yes (gated) |
| [Multimodal Earnings Call Dataset (2018–2024)](https://zenodo.org/records/19032377) | — | timed segments | CC BY 4.0 | Yes |
| [Rhapsodie (Treebank Rhapsodie)](https://www.ortolang.fr/market/corpora/rhapsodie) | — | timed segments | Conflicting statements | Yes |
| [Tamil-English Code-Mixed Podcast Diarization Dataset](https://huggingface.co/datasets/Rangasuthan/tamil-english-podcast-diarization) | — | timed segments | Conflicting statements | Yes |
| [USC IEMOCAP](https://sail.usc.edu/iemocap/) | — | timed segments | Unknown | No (lab copy) |
| [ViYT-Diar (Vietnamese YouTube Diarization Dataset)](https://huggingface.co/datasets/tuanduy1612/ViYT-Diar) | — | timed segments | Apache 2.0 | Yes |
| [Who Speaks When? (LIAS, French)](https://github.com/lias-laboratory/who-speaks-when-speaker-diarization-dataset) | — | timed segments | MIT | Yes |
| [Yoloxóchitl Mixtec Speech with Transcription (OpenSLR 89)](https://www.openslr.org/89/) | — | timed segments and channel per speaker | Conflicting statements | No (lab copy) |
| [아동·청소년 상담데이터 (Children & Adolescent Counselling Data, AIHub 71680)](https://www.aihub.or.kr/aihubdata/data/view.do?currMenu=115&topMenu=100&dataSetSn=71680) | — | timed segments | Conflicting statements | Yes |
