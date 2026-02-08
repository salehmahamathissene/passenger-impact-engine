"""Simple in-memory queue for testing"""

import threading
import queue
import time
from .db import SessionLocal
from .enterprise_models import EnterpriseJob

job_queue = queue.Queue()

def enqueue_job(job_type, **kwargs):
    """Enqueue a job"""
    db = SessionLocal()
    try:
        job = EnterpriseJob(
            job_type=job_type,
            status="queued",
            parameters=kwargs
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
        # Add to queue
        job_queue.put({
            'job_id': str(job.id),
            'job_type': job_type,
            **kwargs
        })
        
        return str(job.id)
    finally:
        db.close()

def worker_loop():
    """Worker that processes jobs"""
    while True:
        try:
            job_data = job_queue.get(timeout=1)
            process_job(job_data)
        except queue.Empty:
            time.sleep(0.1)
        except Exception as e:
            print(f"Worker error: {e}")

def process_job(job_data):
    """Process a single job"""
    db = SessionLocal()
    try:
        job = db.query(EnterpriseJob).filter(
            EnterpriseJob.id == job_data['job_id']
        ).first()
        
        if not job:
            return
        
        # Update status
        job.status = "processing"
        job.started_at = time.time()
        db.commit()
        
        # Simulate work
        time.sleep(2)
        
        # Mark as completed
        job.status = "completed"
        job.finished_at = time.time()
        job.processing_time_ms = int((job.finished_at - job.started_at) * 1000)
        db.commit()
        
    except Exception as e:
        if job:
            job.status = "failed"
            job.error = str(e)
            db.commit()
    finally:
        db.close()

# Start worker thread
worker_thread = threading.Thread(target=worker_loop, daemon=True)
worker_thread.start()
