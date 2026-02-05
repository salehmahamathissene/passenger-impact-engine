from __future__ import annotations

import gzip
import json
from pathlib import Path
from typing import Any


def _count_csv_rows_gz(path: Path) -> tuple[int, str]:
    """
    Returns (data_rows_count, header_line).
    data_rows_count excludes the header row.
    Header is normalized to avoid CRLF / trailing whitespace issues.
    """
    with gzip.open(path, "rt", encoding="utf-8", newline="") as f:
        header = f.readline()
        # normalize: remove BOM, \r\n, trailing spaces
        header = header.lstrip("\ufeff").strip("\r\n ").strip()
        rows = 0
        for _ in f:
            rows += 1
    return rows, header


def verify_run(out_dir: str) -> dict[str, Any]:
    out = Path(out_dir)
    index_path = out / "ledger_index.json"
    run_path = out / "run.json"

    if not run_path.exists():
        raise FileNotFoundError(f"Missing: {run_path}")

    run_meta = json.loads(run_path.read_text(encoding="utf-8"))
    run_id = run_meta["run_id"]

    if not index_path.exists():
        return {
            "ok": True,
            "message": "No ledger_index.json found (likely audit=summary).",
            "run_id": run_id,
        }

    idx = json.loads(index_path.read_text(encoding="utf-8"))
    ledger = idx["ledger"]

    ledger_dir = Path(ledger["dir"])
    fields = ledger["fields"]
    expected_header = ",".join(fields).strip()

    mode = ledger["mode"]
    iterations = int(idx["iterations"])
    passengers = int(idx["passengers"])
    topk = int(ledger["topk"])

    # Expected rows per iteration depends on mode
    if mode == "topk":
        exp_per_it: int | None = topk
    elif mode == "all":
        exp_per_it = passengers
    elif mode in {"eligible", "sample"}:
        # cannot know deterministically without recomputation (or RNG replay for sample)
        exp_per_it = None
    else:
        raise ValueError(f"Unknown mode: {mode}")

    # Verify chunks
    chunks = ledger["chunks"]
    total_rows = 0

    for ch in chunks:
        fname = ch["file"]
        start_it = int(ch["start_iteration"])
        end_it = int(ch["end_iteration"])
        rows_written = int(ch["rows_written"])

        fpath = ledger_dir / fname
        if not fpath.exists():
            raise FileNotFoundError(f"Missing chunk file: {fpath}")

        data_rows, header = _count_csv_rows_gz(fpath)

        # normalize expected too (defensive)
        exp_h = expected_header.lstrip("\ufeff").strip("\r\n ").strip()
        got_h = header.lstrip("\ufeff").strip("\r\n ").strip()

        if got_h != exp_h:
            raise ValueError(
                f"Header mismatch in {fname}\nExpected: {exp_h!r}\nGot:      {got_h!r}"
            )

        if data_rows != rows_written:
            raise ValueError(f"Row count mismatch in {fname}: index says {rows_written}, file has {data_rows}")

        # deterministic check for topk/all
        if exp_per_it is not None:
            expected_chunk_iters = end_it - start_it + 1
            expected_rows = expected_chunk_iters * exp_per_it
            if rows_written != expected_rows:
                raise ValueError(f"Unexpected rows_written in {fname}: got {rows_written}, expected {expected_rows}")

        total_rows += rows_written

    if total_rows != int(ledger["total_rows_written"]):
        raise ValueError(f"Total rows mismatch: computed={total_rows}, index={ledger['total_rows_written']}")

    if exp_per_it is not None:
        expected_total = iterations * exp_per_it
        if total_rows != expected_total:
            raise ValueError(f"Expected total rows {expected_total}, got {total_rows}")

    return {
        "ok": True,
        "run_id": run_id,
        "ledger_mode": mode,
        "chunks": len(chunks),
        "total_rows": total_rows,
        "note": "eligible/sample modes skip deterministic expected-row assertions",
    }
