from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal


Mode = Literal["auto", "real", "demo"]


@dataclass(frozen=True)
class EngineConfig:
    seed: int = 42
    runs: int = 500
    tickets_per_flight: int = 120
    out_dir: Path = Path("out")
    mode: Mode = "auto"

    # ✅ PDF export
    pdf: bool = False
