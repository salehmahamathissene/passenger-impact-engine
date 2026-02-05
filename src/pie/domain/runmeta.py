from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any


def stable_hash(obj: Any) -> str:
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:16]


@dataclass(frozen=True)
class RunMeta:
    run_id: str
    seed: int
    iterations: int
    config_hash: str
    audit: str
