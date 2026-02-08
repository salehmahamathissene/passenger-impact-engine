from __future__ import annotations

import csv
import gzip
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _read_csv_rows(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        out: list[dict[str, Any]] = []
        for i, row in enumerate(r):
            out.append(dict(row))
            if limit is not None and i + 1 >= limit:
                break
        return out


def _read_run_mode(out_dir: Path) -> str:
    p = out_dir / "RUN_MODE.txt"
    if p.exists():
        return p.read_text(encoding="utf-8").strip()
    return "unknown"


def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default


def _load_breakdown(cost_breakdown_csv: Path) -> dict[str, float]:
    rows = _read_csv_rows(cost_breakdown_csv)
    breakdown: dict[str, float] = {}
    for row in rows:
        k = str(row.get("component", "")).strip()
        v = _safe_float(row.get("value", 0.0))
        if k:
            breakdown[k] = v
    return breakdown


def _count_gz_lines(path: Path, max_lines: int = 2_000_000) -> int:
    if not path.exists():
        return 0
    n = 0
    with gzip.open(path, "rt", encoding="utf-8", newline="") as f:
        for _ in f:
            n += 1
            if n >= max_lines:
                break
    return n


def _make_table(rows: list[dict[str, Any]], max_cols: int = 10) -> Table:
    header = list(rows[0].keys())[:max_cols]
    data = [header]
    for r in rows:
        data.append([str(r.get(k, "")) for k in header])

    t = Table(data, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return t


def build_executive_pdf(out_dir: Path, pdf_path: Path | None = None) -> Path:
    """
    Generates: EXECUTIVE_REPORT.pdf
    Requires artifacts already exist in out_dir:
      - charts/*.png
      - tables/*.csv
      - tables/ledger.csv.gz
      - RUN_MODE.txt
    """
    out_dir = Path(out_dir)
    if pdf_path is None:
        pdf_path = out_dir / "EXECUTIVE_REPORT.pdf"
    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=2.0 * cm,
        rightMargin=2.0 * cm,
        topMargin=2.0 * cm,
        bottomMargin=2.0 * cm,
        title="Passenger Impact Engine — Executive Report",
        author="Passenger Impact Engine",
    )

    elems: list[Any] = []

    mode = _read_run_mode(out_dir)

    elems.append(Paragraph("Passenger Impact Engine (EU261) — Executive Report", styles["Title"]))
    elems.append(Spacer(1, 8))
    elems.append(Paragraph(f"Run mode: <b>{mode}</b>", styles["Normal"]))
    elems.append(Paragraph(f"Output folder: <b>{out_dir}</b>", styles["Normal"]))
    elems.append(Spacer(1, 12))

    # KPI section: computed from cost breakdown (mean per run)
    breakdown = _load_breakdown(out_dir / "tables" / "cost_breakdown.csv")
    total_mean = sum(breakdown.values())
    elems.append(Paragraph("Key results", styles["Heading2"]))
    elems.append(Paragraph(f"Mean total cost per run (from breakdown): <b>{total_mean:,.2f} EUR</b>", styles["Normal"]))
    elems.append(Spacer(1, 8))

    if breakdown:
        elems.append(Paragraph("Cost decomposition (mean per run)", styles["Heading3"]))
        bd_rows = [{"component": k, "value_eur": f"{v:,.2f}"} for k, v in breakdown.items()]
        elems.append(_make_table(bd_rows, max_cols=2))
        elems.append(Spacer(1, 12))

    # Charts
    elems.append(Paragraph("Charts", styles["Heading2"]))
    charts = [
        ("Cost decomposition", out_dir / "charts" / "01_cost_breakdown.png"),
        ("Top flights by expected cost", out_dir / "charts" / "02_top_flights.png"),
        ("Mean cost by cabin segment", out_dir / "charts" / "03_group_mean_cost.png"),
    ]
    for title, img_path in charts:
        if img_path.exists():
            elems.append(Paragraph(title, styles["Heading3"]))
            elems.append(Image(str(img_path), width=16.5 * cm, height=9.0 * cm))
            elems.append(Spacer(1, 10))

    # Tables (excerpts)
    def add_table(title: str, csv_path: Path, max_rows: int = 12) -> None:
        rows = _read_csv_rows(csv_path, limit=max_rows)
        if not rows:
            return
        elems.append(Paragraph(title, styles["Heading2"]))
        elems.append(_make_table(rows, max_cols=10))
        elems.append(Spacer(1, 12))

    add_table("Top flights (excerpt)", out_dir / "tables" / "top_flights.csv", max_rows=12)
    add_table("Top passengers (excerpt)", out_dir / "tables" / "top_passengers.csv", max_rows=12)
    add_table("Group statistics (excerpt)", out_dir / "tables" / "group_stats.csv", max_rows=12)

    # Audit trace
    elems.append(Paragraph("Audit trace", styles["Heading2"]))
    ledger_path = out_dir / "tables" / "ledger.csv.gz"
    if ledger_path.exists():
        n_lines = _count_gz_lines(ledger_path)
        elems.append(Paragraph(f"Ledger: <b>{ledger_path.name}</b> (lines incl header: {n_lines})", styles["Normal"]))
        elems.append(Paragraph("This file provides passenger-level cost components per simulated run.", styles["Normal"]))
    else:
        elems.append(Paragraph("Ledger not found.", styles["Normal"]))

    doc.build(elems)
    return pdf_path
