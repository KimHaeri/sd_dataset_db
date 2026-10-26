"""Measure a downloaded dataset from its reference RTTM (and audio) and write measurements/<dataset_id>.json.

Usage:
  python3 tools/measure.py DATASET_ID [DATASET_ID ...]
  python3 tools/measure.py --all            every row of data/collections.csv
  python3 tools/measure.py --rttm-dir DIR   print the statistics of loose RTTM files (no file written)

The dataset directory is $<data_env_var>/<dataset_id> (collections.csv; SD_DATA_ROOT by
default). rttm_glob, uem_glob and audio_glob in collections.csv are relative to it.
Audio durations use soundfile when it is installed, else the standard wave module (.wav only).
The output records only the variable name, never the local path. Then run tools/sync.py.
"""

import collections
import hashlib
import json
import sys
import wave
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import csvio  # noqa: E402
import localenv  # noqa: E402

OUT = csvio.ROOT / "measurements"


def read_rttm(paths):
    """Return {session: {speaker: [(start, end), ...]}} from SPEAKER lines."""
    sessions = collections.defaultdict(lambda: collections.defaultdict(list))
    for p in paths:
        for ln in Path(p).read_text(encoding="utf-8").splitlines():
            f = ln.split()
            if not f or f[0] != "SPEAKER":
                continue
            start, dur = float(f[3]), float(f[4])
            if dur > 0:
                sessions[f[1]][f[7]].append((start, start + dur))
    return sessions


def read_uem(paths):
    """Return {session: [(start, end), ...]}."""
    out = collections.defaultdict(list)
    for p in paths:
        for ln in Path(p).read_text(encoding="utf-8").splitlines():
            f = ln.split()
            if len(f) >= 4:
                out[f[0]].append((float(f[2]), float(f[3])))
    return out


def merge(spans):
    out = []
    for s, e in sorted(spans):
        if out and s <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], e))
        else:
            out.append((s, e))
    return out


def clip(spans, regions):
    if regions is None:
        return spans
    out = []
    for s, e in spans:
        for rs, re_ in regions:
            a, b = max(s, rs), min(e, re_)
            if a < b:
                out.append((a, b))
    return out


def session_stats(speakers, regions=None):
    """Seconds with >=1 speaker and with >=2 speakers. A speaker's own overlapping segments count once."""
    events = []
    for spans in speakers.values():
        for s, e in merge(clip(spans, regions)):
            events += [(s, 1), (e, -1)]
    events.sort()
    speech = overlap = 0.0
    active, prev = 0, None
    for t, d in events:
        if prev is not None:
            if active >= 1:
                speech += t - prev
            if active >= 2:
                overlap += t - prev
        active += d
        prev = t
    return speech, overlap


def rttm_summary(sessions, uem=None):
    speech = overlap = 0.0
    per_session = collections.Counter()
    labels = set()
    for name, speakers in sessions.items():
        s, o = session_stats(speakers, uem.get(name) if uem else None)
        speech += s
        overlap += o
        per_session[len(speakers)] += 1
        labels |= set(speakers)
    counts = sorted(per_session)
    return {
        "n_sessions": len(sessions),
        "n_speakers": len(labels),
        "speakers_per_session": {
            "min": counts[0] if counts else None, "max": counts[-1] if counts else None,
            "histogram": {str(k): per_session[k] for k in counts},
        },
        "speech_hours": round(speech / 3600, 3),
        "overlap_ratio": round(100 * overlap / speech, 2) if speech else None,
    }


def audio_info(path):
    try:
        import soundfile as sf
        i = sf.info(str(path))
        return i.duration, f"{i.samplerate}Hz/{i.channels}ch"
    except ImportError:
        with wave.open(str(path)) as w:
            return w.getnframes() / w.getframerate(), f"{w.getframerate()}Hz/{w.getnchannels()}ch"


def sha1_of(paths):
    h = hashlib.sha1()
    for p in sorted(paths, key=lambda p: p.as_posix()):
        h.update(Path(p).read_bytes())
    return h.hexdigest()


def measure(row):
    base = localenv.data_dir(row["dataset_id"], row["data_env_var"])
    rttms = sorted(base.glob(row["rttm_glob"]))
    if not rttms:
        sys.exit(f"{row['dataset_id']}: no files match {row['rttm_glob']} under ${row['data_env_var']}/{row['dataset_id']}")
    uem = None
    if row["uem_glob"] not in ("", "NA"):
        uem = read_uem(sorted(base.glob(row["uem_glob"])))
    result = {"dataset_id": row["dataset_id"], "data_env_var": row["data_env_var"],
              "measured_on": date.today().isoformat(), "rttm_glob": row["rttm_glob"],
              "uem_glob": row["uem_glob"], "audio_glob": row["audio_glob"],
              "n_rttm_files": len(rttms), "rttm_sha1": sha1_of(rttms)}
    result.update(rttm_summary(read_rttm(rttms), uem))
    result["audio"] = None
    if row["audio_glob"] not in ("", "NA"):
        files = sorted(base.glob(row["audio_glob"]))
        fmt = collections.Counter()
        total = 0.0
        for f in files:
            dur, key = audio_info(f)
            total += dur
            fmt[key] += 1
        result["audio"] = {"n_files": len(files), "hours": round(total / 3600, 3), "format": dict(sorted(fmt.items()))}
    return result


def main(argv):
    if not argv:
        sys.exit(__doc__)
    if argv[0] == "--rttm-dir":
        print(json.dumps(rttm_summary(read_rttm(sorted(Path(argv[1]).rglob("*.rttm")))), indent=2))
        return
    _, rows = csvio.read_rows(csvio.ROOT / "data" / "collections.csv")
    rows = {r["dataset_id"]: r for r in rows}
    ids = sorted(rows) if argv[0] == "--all" else argv
    OUT.mkdir(exist_ok=True)
    for i in ids:
        if i not in rows:
            sys.exit(f"{i}: no row in data/collections.csv (add one first)")
        m = measure(rows[i])
        (OUT / f"{i}.json").write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        print(f"wrote measurements/{i}.json: {m['n_sessions']} sessions, {m['speech_hours']} h speech, overlap {m['overlap_ratio']}%")


if __name__ == "__main__":
    main(sys.argv[1:])
