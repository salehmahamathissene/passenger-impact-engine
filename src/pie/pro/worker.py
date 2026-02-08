from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
import traceback
import json
import hashlib

from pie.pro.db import SessionLocal
from pie.pro.enterprise_models import EnterpriseJob, EnterpriseOrder, EnterpriseInvoice, EnterpriseCompany, JobStatus, InvoiceStatus
from pie.pro.pdf_report import ExecutiveReport, render_executive_report_pdf

def _utcnow():
    return datetime.now(timezone.utc)

def run_enterprise_job(job_id: str) -> None:
    """
    Runs an enterprise job created by /enterprise/orders/{id}/execute.
    Updates enterprise_jobs.status, started_at, finished_at, artifact_path, error.
    """
    db = SessionLocal()
    try:
        job = db.query(EnterpriseJob).filter(EnterpriseJob.id == job_id).one()

        job.started_at = _utcnow().replace(tzinfo=None)
        job.status = JobStatus.running
        db.commit()

        # Create executive report artifact (PDF)
        # Load linked order + invoice + company for report
        order = db.query(EnterpriseOrder).filter(EnterpriseOrder.id == job.order_id).one()
        company = db.query(EnterpriseCompany).filter(EnterpriseCompany.id == order.company_id).one()
        invoice = None
        if order.invoice_id:
            invoice = db.query(EnterpriseInvoice).filter(EnterpriseInvoice.id == order.invoice_id).first()

        out_dir = Path("out/enterprise") / str(job_id)
        out_dir.mkdir(parents=True, exist_ok=True)

        out_pdf = out_dir / "EXECUTIVE_REPORT.pdf"

        report = ExecutiveReport(
            job_id=str(job.id),
            order_id=str(order.id),
            company_id=str(company.id),
            description=order.description,
            iterations=order.iterations,
            amount_eur=str(invoice.total_eur) if invoice else "N/A",
            paid_at=invoice.paid_at.isoformat() if (invoice and invoice.status == InvoiceStatus.paid and invoice.paid_at) else None,
            started_at=job.started_at.isoformat() if job.started_at else None,
            finished_at=None,
            kpis={
                "status": "completed",
                "note": "Replace this KPI block with real simulation metrics next.",
            },
        )

        render_executive_report_pdf(out_pdf, report)
        # Write manifest + checksums (enterprise auditability)
        manifest = {
            "job_id": str(job.id),
            "order_id": str(order.id),
            "company_id": str(company.id),
            "invoice_id": str(order.invoice_id) if order.invoice_id else None,
            "description": order.description,
            "iterations": order.iterations,
            "generated_at_utc": _utcnow().isoformat(),
            "artifact": {
                "executive_report_pdf": str(out_pdf),
            },
        }
        (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        def sha256_file(fp: Path) -> str:
            h = hashlib.sha256()
            with fp.open("rb") as f:
                for chunk in iter(lambda: f.read(1024 * 1024), b""):
                    h.update(chunk)
            return h.hexdigest()

        checksums = []
        for fp in [out_pdf, out_dir / "manifest.json"]:
            checksums.append(f"{sha256_file(fp)}  {fp.name}")
        (out_dir / "checksums.sha256").write_text("\n".join(checksums) + "\n", encoding="utf-8")

        job.finished_at = _utcnow().replace(tzinfo=None)
        job.artifact_path = str(out_pdf)
        job.status = JobStatus.done  # Changed from "succeeded" to "done"
        job.error = None
        db.commit()
        
        print(f"Enterprise job {job_id} completed successfully")

    except Exception as e:
        print(f"Error processing enterprise job {job_id}: {e}")
        traceback.print_exc()
        job.finished_at = _utcnow().replace(tzinfo=None)
        job.status = JobStatus.failed
        job.error = str(e)
        db.commit()
        raise
    finally:
        db.close()

def run_order_job(order_id: str) -> None:
    """
    Runs a regular order job.
    """
    print(f"Processing order job: {order_id}")
    # Add your order processing logic here
    pass
