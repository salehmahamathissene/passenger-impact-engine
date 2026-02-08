#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = str(ROOT / "src")

# IMPORTANT: prepend so it wins over anything else
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from rq import Worker
from pie.pro.queue import redis_conn

if __name__ == "__main__":
    queues = ["pie-pro", "pie-enterprise"]
    print(f"Starting RQ worker for queues: {queues} | PYTHONPATH={SRC}")
    worker = Worker(queues, connection=redis_conn)
    worker.work()
