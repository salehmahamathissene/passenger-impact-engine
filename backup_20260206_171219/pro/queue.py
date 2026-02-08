from __future__ import annotations

from typing import Any
import os

import redis
from rq import Queue

from .settings import settings

_redis = redis.Redis.from_url(settings.REDIS_URL)

# Separate queues: pro vs enterprise (helps SLAs)
pro_queue = Queue("pie-pro", connection=_redis, default_timeout=3600)
ent_queue = Queue("pie-enterprise", connection=_redis, default_timeout=7200)


def enqueue_order_job(order_id: int) -> bool:
    """PRO pipeline job: runs simulation and packages artifact."""
    pro_queue.enqueue("pie.pro.worker.run_order_job", order_id)
    return True


def enqueue_enterprise_job(job_id: str) -> bool:
    """Enterprise job runner (invoice-paid order triggers a job)."""
    ent_queue.enqueue("pie.pro.worker.run_enterprise_job", job_id)
    return True
