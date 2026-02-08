from __future__ import annotations

import redis
from rq import Queue
from .settings import settings

# Redis connection used by both API and worker
redis_conn = redis.Redis.from_url(settings.REDIS_URL)

# Separate queues (SLA separation)
pro_queue = Queue("pie-pro", connection=redis_conn, default_timeout=3600)
ent_queue = Queue("pie-enterprise", connection=redis_conn, default_timeout=7200)

def enqueue_order_job(order_id: str) -> bool:
    pro_queue.enqueue("pie.pro.worker.run_order_job", order_id)
    return True

def enqueue_enterprise_job(job_id: str) -> bool:
    ent_queue.enqueue("pie.pro.worker.run_enterprise_job", job_id)
    return True
