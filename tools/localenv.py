"""Machine-specific settings, read from `.env` at the repository root.

`.env` is git-ignored; copy `.env.example` and fill it in. Values already set in the
environment win over the file. Nothing machine-specific belongs in tracked files.
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load():
    path = ROOT / ".env"
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), os.path.expanduser(value.strip().strip('"').strip("'")))


def data_dir(dataset_id, env_var="SD_DATA_ROOT"):
    """The local copy of one dataset: $<env_var>/<dataset_id>."""
    load()
    if not os.environ.get(env_var):
        sys.exit(f"{env_var} is not set (put it in .env or the environment)")
    return Path(os.environ[env_var]) / dataset_id
