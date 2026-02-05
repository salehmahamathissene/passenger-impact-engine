from __future__ import annotations

import csv
import gzip
from collections.abc import Mapping
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any


class LedgerWriter:
    """
    Streaming writer for large passenger-level ledgers.

    - Avoids keeping 10M+ rows in RAM
    - Supports .csv and .csv.gz
    """

    def __init__(self, path: Path, fieldnames: list[str]) -> None:
        self.path = path
        self.fieldnames = fieldnames
        self._fh: Any | None = None
        self._writer: csv.DictWriter | None = None

    def __enter__(self) -> LedgerWriter:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.suffix == ".gz":
            self._fh = gzip.open(self.path, "wt", encoding="utf-8", newline="")
        else:
            self._fh = open(self.path, "w", encoding="utf-8", newline="")
        self._writer = csv.DictWriter(self._fh, fieldnames=self.fieldnames)
        self._writer.writeheader()
        return self

    def write_row(self, obj: Any) -> None:
        if self._writer is None:
            raise RuntimeError("LedgerWriter not initialized. Use: with LedgerWriter(...) as w:")

        if is_dataclass(obj):
            row = asdict(obj)
        elif isinstance(obj, Mapping):
            row = dict(obj)
        else:
            raise TypeError(f"Unsupported row type: {type(obj)}")

        cleaned = {k: row.get(k, "") for k in self.fieldnames}
        self._writer.writerow(cleaned)

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._fh is not None:
            self._fh.close()
        self._fh = None
        self._writer = None
