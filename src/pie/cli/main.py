from __future__ import annotations

import http.server
import json
import os
import socketserver
from pathlib import Path

import typer

from pie.application.dashboard import build_dashboard
from pie.application.merge_ledger import merge_ledger
from pie.application.simulate import run_monte_carlo
from pie.application.stats import compute_stats_v2, write_stats_artifacts_v2
from pie.application.verify import verify_run

app = typer.Typer(help="Passenger Impact Engine (EU261) — simulation CLI")


# --------------------------------------------------------------------------------------
# Version
# --------------------------------------------------------------------------------------
@app.command("version")
def version_cmd() -> None:
    typer.echo("Passenger Impact Engine v0.1.0")


# --------------------------------------------------------------------------------------
# Simulate
# --------------------------------------------------------------------------------------
@app.command("simulate")
def simulate_cmd(
    config: str = typer.Option("configs/demo.yml", help="Path to YAML config"),
    out: str = typer.Option("out", help="Output directory"),
    audit: str = typer.Option("both", help="summary|ledger|both"),
    ledger_mode: str = typer.Option("all", help="all|eligible|topk|sample"),
    ledger_topk: int = typer.Option(50, help="Top-K passengers per iteration when ledger_mode=topk"),
    ledger_sample: float = typer.Option(0.05, help="Sample fraction per iteration when ledger_mode=sample"),
    ledger_chunk_size: int = typer.Option(100, help="Chunk size (iterations) for ledger chunk files"),
    ledger_merge: bool = typer.Option(False, "--ledger-merge", help="Merge ledger chunks into out/entitlements.csv.gz"),
) -> None:
    """
    Run Monte Carlo simulation and optionally generate ledger artifacts.
    """
    df, summary = run_monte_carlo(
        config_path=config,
        out_dir=out,
        audit=audit,
        ledger_mode=ledger_mode,
        ledger_topk=ledger_topk,
        ledger_sample=ledger_sample,
        ledger_chunk_size=ledger_chunk_size,
    )

    typer.echo(f"✅ Done. Iterations={len(df)}")
    typer.echo(f"Mean total cost (EUR): {summary['mean_total_cost']:.2f}")
    typer.echo(f"P95 total cost (EUR): {summary['p95_total_cost']:.2f}")
    typer.echo(f"CVaR95 total cost (EUR): {summary['cvar95_total_cost']:.2f}")
    typer.echo(f"Artifacts written to: {out}")

    if ledger_merge:
        merged = merge_ledger(out_dir=out)
        typer.echo(f"✅ Merged ledger written: {merged}")


# --------------------------------------------------------------------------------------
# Verify
# --------------------------------------------------------------------------------------
@app.command("verify")
def verify_cmd(
    out: str = typer.Option("out", help="Output directory to verify"),
) -> None:
    """
    Verify that a simulation run produced valid artifacts.
    """
    res = verify_run(out)
    typer.echo(json.dumps(res, indent=2, ensure_ascii=False))


# --------------------------------------------------------------------------------------
# Merge Ledger
# --------------------------------------------------------------------------------------
@app.command("merge-ledger")
def merge_ledger_cmd(
    out: str = typer.Option("out", help="Output directory containing ledger chunks"),
) -> None:
    """
    Merge ledger chunk files into one entitlements.csv.gz.
    """
    merged = merge_ledger(out_dir=out)
    typer.echo(f"✅ Merged ledger written: {merged}")


# --------------------------------------------------------------------------------------
# Stats
# --------------------------------------------------------------------------------------
@app.command("stats")
def stats_cmd(
    out: str = typer.Option(
        "out",
        help="Output directory (expects entitlements.csv.gz OR ledger_index.json + ledger/)",
    ),
    top: int = typer.Option(20, help="Top N passengers"),
    by: str = typer.Option("segment", help="Grouping: none|segment|dtype|segment,dtype"),
    metric: str = typer.Option("mean", help="Ranking metric: mean|p50|p95|p99|max"),
    min_cost: float = typer.Option(0.0, help="Ignore rows with total_cost_eur < min_cost"),
    sample_size: int = typer.Option(5000, help="Reservoir size for quantile estimation"),
) -> None:
    """
    Compute grouped cost statistics + top passenger ranking.
    """
    res = compute_stats_v2(
        out_dir=out,
        top=top,
        by=by,
        metric=metric,
        min_cost=min_cost,
        sample_size=sample_size,
    )

    paths = write_stats_artifacts_v2(out, res)

    typer.echo(f"✅ Stats computed. total_rows={res['total_rows']}, groups={len(res['groups'])}")
    for p in paths:
        typer.echo(f"Written: {p}")


# --------------------------------------------------------------------------------------
# Dashboard build
# --------------------------------------------------------------------------------------
@app.command("dashboard")
def dashboard_cmd(
    out: str = typer.Option("out", help="Output directory"),
    top: int = typer.Option(20, help="Top N passengers to show"),
) -> None:
    """
    Generate dashboard HTML + assets under out/dashboard/.
    """
    paths = build_dashboard(out_dir=out, top=top)
    typer.echo(f"✅ Dashboard written: {paths.index_html}")


# --------------------------------------------------------------------------------------
# Serve dashboard (new)
# --------------------------------------------------------------------------------------
@app.command("serve")
def serve_cmd(
    out: str = typer.Option("out", help="Output directory (expects out/dashboard/index.html)"),
    host: str = typer.Option("0.0.0.0", help="Bind host"),
    port: int = typer.Option(8010, help="Port"),
) -> None:
    """
    Serve dashboard over HTTP. Good for VM + host browser.
    """
    dash_dir = Path(out) / "dashboard"
    index = dash_dir / "index.html"
    if not index.exists():
        raise typer.BadParameter(f"Missing {index}. Run: pie dashboard --out {out}")

    os.chdir(dash_dir)

    typer.echo(f"✅ Serving dashboard from: {dash_dir}")
    typer.echo(f"   URL: http://{host}:{port}/index.html")

    # Reuse address helps when you restart quickly
    class ReuseTCPServer(socketserver.TCPServer):
        allow_reuse_address = True

    with ReuseTCPServer((host, port), http.server.SimpleHTTPRequestHandler) as httpd:
        httpd.serve_forever()


if __name__ == "__main__":
    app()
