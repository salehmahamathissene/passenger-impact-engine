from __future__ import annotations

import os
import secrets
import subprocess
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

APP_TITLE = "Passenger Impact Engine — Report Service"
REPORTS_DIR = Path(os.environ.get("PIE_REPORTS_DIR", "reports")).resolve()
API_KEY = os.environ.get("PIE_API_KEY")  # optional

app = FastAPI(title=APP_TITLE)

REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Serve reports as static files
app.mount("/reports", StaticFiles(directory=str(REPORTS_DIR)), name="reports")


def _require_key(provided: str | None) -> None:
    if API_KEY and provided != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


def _new_report_id() -> str:
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    token = secrets.token_hex(4)
    return f"{ts}_{token}"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/run")
async def run_report(
    key: str | None = Form(default=None),
    mode: str = Form(default="real"),
    runs: int = Form(default=500),
    tickets_per_flight: int = Form(default=120),
    seed: int = Form(default=42),
    pdf: bool = Form(default=True),
    # optional input files for later (you can accept airline CSVs here)
    flights_csv: UploadFile | None = File(default=None),
    tickets_csv: UploadFile | None = File(default=None),
):
    _require_key(key)

    report_id = _new_report_id()
    out_dir = REPORTS_DIR / report_id
    out_dir.mkdir(parents=True, exist_ok=True)

    # Save uploaded files (optional for now)
    uploads_dir = out_dir / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    if flights_csv is not None:
        (uploads_dir / "flights.csv").write_bytes(await flights_csv.read())
    if tickets_csv is not None:
        (uploads_dir / "tickets.csv").write_bytes(await tickets_csv.read())

    # Run the engine using your installed CLI
    cmd = [
        "pie",
        "run",
        "--mode",
        mode,
        "--runs",
        str(runs),
        "--tickets-per-flight",
        str(tickets_per_flight),
        "--seed",
        str(seed),
        "--out",
        str(out_dir),
    ]
    if pdf:
        cmd.append("--pdf")

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "PIE run failed",
                "stdout": e.stdout[-2000:],
                "stderr": e.stderr[-2000:],
                "cmd": cmd,
            },
        )

    return {
        "report_id": report_id,
        "dashboard_url": f"/reports/{report_id}/dashboard.html",
        "pdf_url": f"/reports/{report_id}/EXECUTIVE_REPORT.pdf" if pdf else None,
        "tables_url": f"/reports/{report_id}/tables/",
        "charts_url": f"/reports/{report_id}/charts/",
    }


@app.get("/download/{report_id}/pdf")
def download_pdf(report_id: str):
    pdf_path = REPORTS_DIR / report_id / "EXECUTIVE_REPORT.pdf"
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF not found")
    return FileResponse(str(pdf_path), filename=f"PIE_{report_id}.pdf", media_type="application/pdf")
