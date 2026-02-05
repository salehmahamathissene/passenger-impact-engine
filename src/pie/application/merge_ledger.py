from __future__ import annotations

import gzip
import json
from pathlib import Path


def merge_ledger(out_dir: str, out_name: str = "entitlements.csv.gz") -> Path:
    """
    Merge all ledger chunk files into a single gzip CSV with exactly one header.
    Requires out/ledger_index.json.
    """
    out = Path(out_dir)
    idx_path = out / "ledger_index.json"
    if not idx_path.exists():
        raise FileNotFoundError(f"Missing: {idx_path} (run simulate with audit=ledger|both)")

    idx = json.loads(idx_path.read_text(encoding="utf-8"))
    ledger = idx["ledger"]
    ledger_dir = Path(ledger["dir"])
    chunks = ledger["chunks"]

    target = out / out_name

    first = True
    with gzip.open(target, "wt", encoding="utf-8", newline="") as w:
        for ch in chunks:
            src = ledger_dir / ch["file"]
            if not src.exists():
                raise FileNotFoundError(f"Missing chunk file: {src}")

            with gzip.open(src, "rt", encoding="utf-8", newline="") as r:
                header = r.readline()
                if first:
                    w.write(header)
                    first = False
                # skip header for subsequent chunks
                for line in r:
                    w.write(line)

    return target
