from __future__ import annotations

import subprocess
import time
import json
from datetime import datetime
from pathlib import Path
import shutil
import sys

from sqlalchemy.orm import Session

from .db import SessionLocal
from .models import Job, JobStatus, Order
from .settings import settings


def run_order_job(order_id: int) -> None:
    """Process an order in background"""
    db: Session = SessionLocal()
    start_time = time.time()
    
    print(f"🚀 Starting job for order {order_id}")
    
    try:
        order = db.get(Order, order_id)
        if not order:
            print(f"❌ Order {order_id} not found")
            return

        # Create job if it doesn't exist
        job = order.job
        if not job:
            job = Job(order_id=order.id, status=JobStatus.queued)
            db.add(job)
            db.commit()
            db.refresh(job)

        # Update job status
        job.status = JobStatus.running
        job.started_at = datetime.utcnow()
        db.commit()
        
        print(f"📧 Processing order for: {order.customer_email}")
        print(f"📦 Plan: {order.plan}, Amount: €{order.amount_cents/100:.2f}")

        # Create client ID from email
        client_id = order.customer_email.split("@")[0]
        # Replace special characters
        client_id = ''.join(c if c.isalnum() else '_' for c in client_id)
        
        # Map plan to simulation runs
        runs_map = {
            "starter": 10000,      # €99 for 10,000 runs
            "pro": 50000,          # €499 for 50,000 runs  
            "enterprise": 200000   # €1999 for 200,000 runs
        }
        
        runs = runs_map.get(order.plan, 10000)
        tier = "premium"  # All paid plans get premium service
        
        # Create artifact directory
        artifact_dir = Path(settings.ARTIFACT_ROOT) / f"order_{order_id:06d}"
        artifact_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"🔢 Will run {runs} simulations at {tier} tier")
        print(f"📁 Artifact dir: {artifact_dir}")
        
        try:
            # Build command to run your existing workflow
            cmd = [
                sys.executable,  # Use current python
                f"{Path.home()}/deliver_to_client.py",
                client_id,
                str(runs),
                tier
            ]
            
            print(f"▶️  Running: {' '.join(cmd)}")
            
            # Run the simulation
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800,  # 30 minute timeout
                cwd=Path.home()
            )
            
            print(f"📊 Command completed with return code: {result.returncode}")
            
            if result.returncode == 0:
                print("✅ Simulation completed successfully")
                
                # Find the generated ZIP file
                zip_pattern = f"deliverables/PRO_{client_id}_*.zip"
                zip_files = list(Path.home().glob(zip_pattern))
                
                if zip_files:
                    # Get the most recent ZIP
                    latest_zip = max(zip_files, key=lambda x: x.stat().st_mtime)
                    print(f"📦 Found delivery package: {latest_zip}")
                    
                    # Copy artifact to order directory
                    artifact_path = artifact_dir / latest_zip.name
                    shutil.copy2(latest_zip, artifact_path)
                    
                    # Also copy any reports
                    reports_pattern = f"reports/{client_id}_*"
                    report_dirs = list(Path.home().glob(reports_pattern))
                    for report_dir in report_dirs:
                        if report_dir.is_dir():
                            shutil.copytree(report_dir, artifact_dir / report_dir.name, dirs_exist_ok=True)
                    
                    # Update job status
                    job.status = JobStatus.done
                    job.completed_at = datetime.utcnow()
                    job.artifact_path = str(artifact_path)
                    job.runs_completed = runs
                    job.processing_time_ms = int((time.time() - start_time) * 1000)
                    
                    print(f"🎉 Order {order_id} completed successfully!")
                    print(f"   📁 Artifact: {artifact_path}")
                    print(f"   🔢 Runs: {runs:,}")
                    print(f"   ⏱️  Time: {job.processing_time_ms:,}ms")
                    
                else:
                    error_msg = f"No delivery package found matching {zip_pattern}"
                    print(f"❌ {error_msg}")
                    job.status = JobStatus.failed
                    job.error = error_msg
                    
            else:
                error_msg = f"Simulation failed with code {result.returncode}: {result.stderr[:500]}"
                print(f"❌ {error_msg}")
                job.status = JobStatus.failed
                job.error = error_msg
                
        except subprocess.TimeoutExpired:
            error_msg = "Simulation timeout after 30 minutes"
            print(f"⏰ {error_msg}")
            job.status = JobStatus.failed
            job.error = error_msg
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"💥 {error_msg}")
            job.status = JobStatus.failed
            job.error = error_msg
        
        db.commit()
        
    except Exception as e:
        print(f"💥 Critical error processing order {order_id}: {e}")
        import traceback
        traceback.print_exc()
        # Don't re-raise so worker stays alive
    finally:
        db.close()
        elapsed = time.time() - start_time
        print(f"🔄 Finished processing order {order_id} in {elapsed:.1f}s")


def process_all_pending_jobs() -> None:
    """Process all pending jobs - useful for startup/recovery"""
    db = SessionLocal()
    try:
        from .queue import enqueue_order_job
        
        # Find paid orders without completed jobs
        pending_orders = db.query(Order).filter(
            Order.status == OrderStatus.paid,
            ~Order.job.has(Job.status.in_([JobStatus.running, JobStatus.done]))
        ).all()
        
        print(f"🔍 Found {len(pending_orders)} pending orders")
        
        for order in pending_orders:
            print(f"⏳ Queuing order {order.id} for {order.customer_email}")
            enqueue_order_job(order.id)
            
    finally:
        db.close()


def run_enterprise_job(job_id: str) -> None:
    """
    Enterprise job processor:
    - loads EnterpriseJob + EnterpriseOrder
    - runs deliver_to_client.py
    - stores artifact path
    """
    db: Session = SessionLocal()
    start_time = time.time()
    try:
        from .enterprise_models import EnterpriseJob, EnterpriseOrder, JobStatus
        job = db.get(EnterpriseJob, job_id)
        if not job:
            print(f"❌ EnterpriseJob {job_id} not found")
            return

        job.status = JobStatus.running
        job.started_at = datetime.utcnow()
        db.commit()

        order = db.get(EnterpriseOrder, job.order_id)
        if not order:
            job.status = JobStatus.failed
            job.error = "EnterpriseOrder not found"
            db.commit()
            return

        # Enterprise: use order_id as client slug
        client_slug = str(order.id).replace("-", "")[:12]
        runs = int(order.iterations)
        tier = "premium"

        artifact_dir = Path(settings.ARTIFACT_ROOT) / "enterprise" / f"job_{client_slug}"
        artifact_dir.mkdir(parents=True, exist_ok=True)

        cmd = [
            sys.executable,
            str(Path.home() / "deliver_to_client.py"),
            client_slug,
            str(runs),
            tier,
        ]

        print(f"🏢 Enterprise job {job_id} running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            job.status = JobStatus.failed
            job.error = (result.stderr or result.stdout or "Unknown error")[:2000]
            job.finished_at = datetime.utcnow()
            job.processing_time_ms = int((time.time() - start_time) * 1000)
            db.commit()
            return

        # Find newest zip in deliverables with client_slug in name
        deliverables = Path.home() / "deliverables"
        zips = sorted(deliverables.glob(f"*{client_slug}*.zip"), key=lambda x: x.stat().st_mtime, reverse=True)
        if not zips:
            job.status = JobStatus.failed
            job.error = "No deliverable zip produced"
            job.finished_at = datetime.utcnow()
            job.processing_time_ms = int((time.time() - start_time) * 1000)
            db.commit()
            return

        dest = artifact_dir / zips[0].name
        shutil.copy2(zips[0], dest)

        job.status = JobStatus.done
        job.artifact_path = str(dest)
        job.runs_completed = runs
        job.finished_at = datetime.utcnow()
        job.processing_time_ms = int((time.time() - start_time) * 1000)
        db.commit()
        print(f"✅ Enterprise job {job_id} done -> {dest}")

    except Exception as e:
        try:
            from .enterprise_models import JobStatus
            job = db.get(EnterpriseJob, job_id)
            if job:
                job.status = JobStatus.failed
                job.error = str(e)[:2000]
                job.finished_at = datetime.utcnow()
                job.processing_time_ms = int((time.time() - start_time) * 1000)
                db.commit()
        except Exception:
            pass
        print(f"❌ Enterprise job {job_id} crashed: {e}")
    finally:
        db.close()

