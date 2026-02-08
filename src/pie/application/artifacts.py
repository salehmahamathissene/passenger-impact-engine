from __future__ import annotations

import csv
import gzip
from pathlib import Path
from typing import Any


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def write_ledger_gz(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        with gzip.open(path, "wt", encoding="utf-8", newline="") as f:
            f.write("")
        return
    with gzip.open(path, "wt", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def plot_bar(path: Path, labels: list[str], values: list[float], title: str, xlabel: str, ylabel: str) -> None:
    """
    Optional dependency: matplotlib.
    If missing, we skip chart generation but keep the pipeline producing monetizable CSV artifacts.
    """
    try:
        import matplotlib.pyplot as plt  # lazy import
    except ModuleNotFoundError:
        # Create a tiny marker file so you know charts were skipped
        path.parent.mkdir(parents=True, exist_ok=True)
        (path.parent / "CHARTS_SKIPPED.txt").write_text(
            "matplotlib not installed; charts skipped.\n",
            encoding="utf-8",
        )
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure()
    plt.bar(labels, values)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
