from __future__ import annotations

from pathlib import Path

from pie.application.engine import EngineConfig
from pie.application.artifacts import plot_bar, write_csv, write_ledger_gz
from pie.application.dashboard import render_dashboard_html
from pie.application.demo_engine import run_demo


def run_pipeline(cfg: EngineConfig) -> Path:
    out = cfg.out_dir
    charts_dir = out / "charts"
    tables_dir = out / "tables"

    # Try REAL engine unless user forces demo
    result = None
    used_mode = "demo"

    if cfg.mode in ("auto", "real"):
        try:
            from pie.application.real_engine import run_real

            result = run_real(seed=cfg.seed, runs=cfg.runs, tickets_per_flight=cfg.tickets_per_flight)
            used_mode = "real"
        except Exception:
            if cfg.mode == "real":
                raise
            result = None

    if result is None:
        demo = run_demo(seed=cfg.seed)
        # shape it into the same structure
        result = type("R", (), {})()
        result.mean_total_cost = demo.mean_total_cost
        result.p95_total_cost = demo.p95_total_cost
        result.cvar95_total_cost = demo.cvar95_total_cost
        result.top_passengers = demo.top_passengers
        result.top_flights = [{"flight_id": "DEMO", "expected_cost": demo.mean_total_cost}]
        result.group_stats = demo.group_stats
        result.cost_breakdown = demo.cost_breakdown
        result.ledger_rows = []

    # ---- Write tables ----
    write_csv(tables_dir / "top_passengers.csv", result.top_passengers)
    write_csv(tables_dir / "top_flights.csv", result.top_flights)
    write_csv(tables_dir / "group_stats.csv", result.group_stats)
    write_csv(
        tables_dir / "cost_breakdown.csv",
        [{"component": k, "value": v} for k, v in result.cost_breakdown.items()],
    )

    # ---- Ledger (audit trace) ----
    write_ledger_gz(tables_dir / "ledger.csv.gz", getattr(result, "ledger_rows", []))

    # ---- Charts ----
    components = list(result.cost_breakdown.keys())
    values = [float(result.cost_breakdown[k]) for k in components]
    plot_bar(
        charts_dir / "01_cost_breakdown.png",
        labels=components,
        values=values,
        title="Cost decomposition (mean per run)",
        xlabel="Cost component",
        ylabel="Cost",
    )

    tf = result.top_flights[:10]
    plot_bar(
        charts_dir / "02_top_flights.png",
        labels=[x["flight_id"] for x in tf],
        values=[float(x["expected_cost"]) for x in tf],
        title="Top flights by expected disruption cost",
        xlabel="Flight",
        ylabel="Expected cost",
    )

    gs = result.group_stats
    plot_bar(
        charts_dir / "03_group_mean_cost.png",
        labels=[x["segment"] for x in gs],
        values=[float(x["mean_cost"]) for x in gs],
        title="Mean passenger cost by cabin segment",
        xlabel="Segment",
        ylabel="Mean cost",
    )

    # ---- Dashboard ----
    dash_path = out / "dashboard.html"
    render_dashboard_html(
        dash_path,
        kpis={
            "mean_total_cost": float(result.mean_total_cost),
            "p95_total_cost": float(result.p95_total_cost),
            "cvar95_total_cost": float(result.cvar95_total_cost),
        },
        image_paths={
            "cost_breakdown": "charts/01_cost_breakdown.png",
            "top_flights": "charts/02_top_flights.png",
            "group_stats": "charts/03_group_mean_cost.png",
        },
        csv_paths={
            "cost_breakdown": "tables/cost_breakdown.csv",
            "top_flights": "tables/top_flights.csv",
            "group_stats": "tables/group_stats.csv",
            "ledger": "tables/ledger.csv.gz",
        },
    )

    # Mode marker
    (out / "RUN_MODE.txt").write_text(f"{used_mode}\n", encoding="utf-8")

    # ---- PDF (EXECUTIVE_REPORT.pdf) ----
    if cfg.pdf:
        from pie.application.report_pdf import build_executive_pdf

        build_executive_pdf(out_dir=out)

    return dash_path
