"""Download the files listed in datasets.download_url into $SD_DATA_ROOT/<dataset_id>/raw/.

Usage:
  python3 tools/fetch.py DATASET_ID [--dry-run]

Only datasets with access_method=direct_download are fetched; everything else (LDC, signed
agreements, request forms) is obtained by hand and placed under the same directory.
Existing files are skipped. SHA256SUMS in the raw directory lists what was downloaded.
After unpacking, add a data/collections.csv row and run tools/measure.py and tools/sync.py.
"""

import hashlib
import shutil
import sys
import urllib.parse
import urllib.request

import csvio
import db as dbmod
import localenv


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main(argv):
    if not argv:
        sys.exit(__doc__)
    dataset_id, dry = argv[0], "--dry-run" in argv
    row = dbmod.find(dbmod.load(), "datasets", [dataset_id])
    if row is None:
        sys.exit(f"no dataset {dataset_id}")
    if row["access_method"] != "direct_download":
        sys.exit(f"{dataset_id}: access_method is {row['access_method'] or 'empty'}; obtain it by hand")
    if not row["download_url"]:
        sys.exit(f"{dataset_id}: download_url is empty; add checked URLs first")
    raw = localenv.data_dir(dataset_id) / "raw"
    sums = []
    for url in row["download_url"].split(";"):
        name = urllib.parse.unquote(urllib.parse.urlparse(url).path.rstrip("/").rsplit("/", 1)[-1]) or "index"
        dest = raw / name
        if dry:
            print(f"would fetch {url} -> raw/{name}")
            continue
        raw.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            print(f"skip raw/{name} (exists)")
        else:
            print(f"fetch {url}")
            tmp = dest.with_suffix(dest.suffix + ".part")
            with urllib.request.urlopen(url) as r, open(tmp, "wb") as f:
                shutil.copyfileobj(r, f)
            tmp.replace(dest)
        sums.append(f"{sha256(dest)}  {name}")
    if sums:
        (raw / "SHA256SUMS").write_text("\n".join(sums) + "\n", encoding="utf-8", newline="\n")
        print(f"wrote SHA256SUMS ({len(sums)} file(s)) under $SD_DATA_ROOT/{dataset_id}/raw")


if __name__ == "__main__":
    main(sys.argv[1:])
