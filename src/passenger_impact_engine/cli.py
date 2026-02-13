from __future__ import annotations

import csv
import gzip
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import typer
import yaml
import random

app = typer.Typer(help="Passenger Impact Engine (PIE) CLI")


# ----------------------------
# helpers
# ----------------------------
def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise typer.BadParameter(f"Config not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise typer.BadParameter("Config YAML must be a mapping/object at top-level")
    return data


def _write_json(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")


def _write_gzip_csv(path: Path, header: list[str], rows: list[list[Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def _read_gzip_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        raise typer.BadParameter(f"Missing file: {path}")
    with gzip.open(path, "rt", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        if r.fieldnames is None:
            raise typer.BadParameter(f"Invalid CSV (no header): {path}")
        rows = [row for row in r]
        return list(r.fieldnames), rows


def _percentile(sorted_vals: list[float], p: float) -> float:
    """Nearest-rank percentile for simplicity and stability."""
    if not sorted_vals:
        return 0.0
    if p <= 0:
        return sorted_vals[0]
    if p >= 100:
        return sorted_vals[-1]
    k = math.ceil((p / 100.0) * len(sorted_vals)) - 1
    k = max(0, min(k, len(sorted_vals) - 1))
    return sorted_vals[k]


# ----------------------------
# EU261 logic (simple + stable)
# ----------------------------
def eu261_amount_eur(distance_km: float) -> int:
    # EU261 bands: <=1500 => 250, 1500-3500 => 400, >3500 => 600
    if distance_km <= 1500:
        return 250
    if distance_km <= 3500:
        return 400
    return 600


def eu261_eligible(dtype: str, delay_min: int) -> bool:
    # MVP rule:
    # - cancel => eligible
    # - delay => eligible if delay >= 180 minutes (3h)
    if dtype == "cancel":
        return True
    if dtype == "delay":
        return delay_min >= 180
    return False


# ----------------------------
# config defaults
# ----------------------------
@dataclass(frozen=True)
class SimCfg:
    seed: int
    passengers: int
    dtype: str
    distance_km: float
    delay_min_mean: int
    delay_min_sd: int
    econ_share: float


def _simcfg_from_yaml(cfg: dict[str, Any]) -> SimCfg:
    # Works even if configs/demo.yml is minimal
    sim = cfg.get("simulation", {}) if isinstance(cfg.get("simulation", {}), dict) else {}

    seed = int(sim.get("seed", 42))
    passengers = int(sim.get("passengers", 1200))
    dtype = str(sim.get("dtype", "delay")).strip().lower()
    if dtype not in {"delay", "cancel"}:
        dtype = "delay"

    distance_km = float(sim.get("distance_km", 2100.0))
    delay_min_mean = int(sim.get("delay_min_mean", 220))
    delay_min_sd = int(sim.get("delay_min_sd", 60))
    econ_share = float(sim.get("econ_share", 0.85))
    econ_share = max(0.0, min(1.0, econ_share))

    return SimCfg(
        seed=seed,
        passengers=passengers,
        dtype=dtype,
        distance_km=distance_km,
        delay_min_mean=delay_min_mean,
        delay_min_sd=delay_min_sd,
        econ_share=econ_share,
    )


# ----------------------------
# commands
# ----------------------------
@app.command()
def simulate(
    config: str = typer.Option(..., help="Path to config YAML, e.g. configs/demo.yml"),
    out: str = typer.Option(..., help="Output directory, e.g. /out"),
    audit: str = typer.Option("", help="Audit mode: ledger (optional)"),
):
    out_dir = Path(out)
    _ensure_dir(out_dir)

    cfg_path = Path(config)
    cfg_raw = _read_yaml(cfg_path)
    simcfg = _simcfg_from_yaml(cfg_raw)

    # deterministic
    rng = random.Random(simcfg.seed)

    ledger_header = [
        "passenger_id",
        "segment",
        "dtype",
        "distance_km",
        "delay_min",
        "eligible",
        "entitlement_eur",
        "cost_eur",
    ]

    rows: list[list[Any]] = []
    for i in range(1, simcfg.passengers + 1):
        pid = f"P{i:06d}"
        segment = "ECON" if rng.random() < simcfg.econ_share else "BUS"
        dtype = simcfg.dtype

        # delay minutes: normal-ish but bounded
        if dtype == "delay":
            # Box-Muller-ish approximation using gauss
            delay = int(max(0, rng.gauss(simcfg.delay_min_mean, simcfg.delay_min_sd)))
        else:
            delay = 0

        eligible = 1 if eu261_eligible(dtype, delay) else 0
        entitlement = eu261_amount_eur(simcfg.distance_km) if eligible else 0

        # cost_eur can later include hotels/meals/rebooking; for now equal to entitlement
        cost = entitlement

        rows.append(
            [pid, segment, dtype, f"{simcfg.distance_km:.0f}", str(delay), str(eligible), str(entitlement), str(cost)]
        )

    ledger_path = out_dir / "ledger.csv.gz"
    _write_gzip_csv(ledger_path, ledger_header, rows)

    ledger_index = {
        "ok": True,
        "command": "simulate",
        "created_at": _utc_now(),
        "config": str(cfg_path),
        "seed": simcfg.seed,
        "passengers": simcfg.passengers,
        "ledger_files": ["ledger.csv.gz"],
        "schema": ledger_header,
    }
    _write_json(out_dir / "ledger_index.json", ledger_index)

    # run.json summary
    costs = [float(r[-1]) for r in rows]
    costs_sorted = sorted(costs)
    expected = float(sum(costs_sorted) / len(costs_sorted)) if costs_sorted else 0.0
    p50 = _percentile(costs_sorted, 50)
    p95 = _percentile(costs_sorted, 95)

    run_payload = {
        "ok": True,
        "command": "simulate",
        "created_at": _utc_now(),
        "config": str(cfg_path),
        "audit": audit,
        "meta": {"seed": simcfg.seed, "passengers": simcfg.passengers},
        "scenario": {
            "dtype": simcfg.dtype,
            "distance_km": simcfg.distance_km,
            "delay_min_mean": simcfg.delay_min_mean,
            "delay_min_sd": simcfg.delay_min_sd,
        },
        "results": {
            "expected_cost_eur": expected,
            "p50_cost_eur": p50,
            "p95_cost_eur": p95,
        },
        "artifacts": {"ledger": "ledger.csv.gz", "ledger_index": "ledger_index.json"},
    }
    _write_json(out_dir / "run.json", run_payload)

    typer.echo(f"✅ wrote {out_dir / 'run.json'}")
    typer.echo(f"✅ wrote {out_dir / 'ledger_index.json'}")
    typer.echo(f"✅ wrote {ledger_path}")


@app.command("merge-ledger")
def merge_ledger(out: str = typer.Option(..., help="Output directory, e.g. /out")):
    out_dir = Path(out)
    _ensure_dir(out_dir)

    ledger_path = out_dir / "ledger.csv.gz"
    _, rows = _read_gzip_csv(ledger_path)

    # entitlements.csv.gz (audit-friendly, but compact)
    out_rows: list[list[Any]] = []
    header = ["passenger_id", "segment", "dtype", "distance_km", "delay_min", "entitled", "entitlement_eur", "reason"]

    for r in rows:
        pid = r["passenger_id"]
        segment = r["segment"]
        dtype = r["dtype"]
        distance_km = float(r["distance_km"])
        delay_min = int(r["delay_min"])

        entitled = eu261_eligible(dtype, delay_min)
        amt = eu261_amount_eur(distance_km) if entitled else 0
        reason = "EU261_CANCEL" if dtype == "cancel" else ("EU261_DELAY_3H+" if delay_min >= 180 else "NOT_ELIGIBLE")

        out_rows.append([pid, segment, dtype, f"{distance_km:.0f}", str(delay_min), "1" if entitled else "0", str(amt), reason])

    ent_path = out_dir / "entitlements.csv.gz"
    _write_gzip_csv(ent_path, header, out_rows)
    typer.echo(f"✅ wrote {ent_path}")


@app.command()
def stats(
    out: str = typer.Option(..., help="Output directory, e.g. /out"),
    top: int = typer.Option(5),
    by: str = typer.Option("segment,dtype"),
    metric: str = typer.Option("p95"),
    min_cost: int = typer.Option(200),
    sample_size: int = typer.Option(500),
):
    out_dir = Path(out)
    _ensure_dir(out_dir)

    ent_path = out_dir / "entitlements.csv.gz"
    _, rows = _read_gzip_csv(ent_path)

    # Compute overall distribution from entitlement_eur
    costs = [float(r["entitlement_eur"]) for r in rows]
    costs_sorted = sorted(costs)
    expected = float(sum(costs_sorted) / len(costs_sorted)) if costs_sorted else 0.0
    p50 = _percentile(costs_sorted, 50)
    p95 = _percentile(costs_sorted, 95)

    stats_payload = {
        "ok": True,
        "command": "stats",
        "created_at": _utc_now(),
        "inputs": {"entitlements": "entitlements.csv.gz"},
        "summary": {
            "expected_eur": expected,
            "p50_eur": p50,
            "p95_eur": p95,
            "n_passengers": len(rows),
        },
        "params": {"top": top, "by": by, "metric": metric, "min_cost": min_cost, "sample_size": sample_size},
    }
    _write_json(out_dir / "stats.json", stats_payload)

    # group stats
    by_cols = [c.strip() for c in by.split(",") if c.strip()]
    if not by_cols:
        by_cols = ["segment", "dtype"]

    groups: dict[str, list[float]] = {}
    for r in rows:
        cost = float(r["entitlement_eur"])
        if cost < float(min_cost):
            continue
        key = "_".join(r.get(c, "") for c in by_cols)
        groups.setdefault(key, []).append(cost)

    groups_rows: list[list[Any]] = [["group", "metric", "value_eur", "n"]]
    for g, vals in sorted(groups.items()):
        vals_sorted = sorted(vals)
        if metric == "p50":
            v = _percentile(vals_sorted, 50)
        elif metric == "p95":
            v = _percentile(vals_sorted, 95)
        else:
            v = float(sum(vals_sorted) / len(vals_sorted)) if vals_sorted else 0.0
        groups_rows.append([g, metric, f"{v:.2f}", str(len(vals_sorted))])

    groups_path = out_dir / "stats_groups.csv"
    groups_path.write_text("", encoding="utf-8")  # ensure truncation on rerun
    with groups_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        for row in groups_rows:
            w.writerow(row)

    # top passengers by cost
    tops = sorted(
        ((r["passenger_id"], float(r["entitlement_eur"])) for r in rows),
        key=lambda x: x[1],
        reverse=True,
    )[: max(1, top)]

    top_path = out_dir / "stats_top_passengers.csv"
    with top_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["passenger_id", "cost_eur"])
        for pid, c in tops:
            w.writerow([pid, f"{c:.2f}"])

    typer.echo(f"✅ wrote {out_dir / 'stats.json'}")
    typer.echo(f"✅ wrote {groups_path}")
    typer.echo(f"✅ wrote {top_path}")


@app.command()
def dashboard(
    out: str = typer.Option(..., help="Output directory, e.g. /out"),
    top: int = typer.Option(5),
):
    out_dir = Path(out)
    dash_dir = out_dir / "dashboard"
    _ensure_dir(dash_dir)

    stats_json = json.loads((out_dir / "stats.json").read_text(encoding="utf-8"))
    groups_csv = (out_dir / "stats_groups.csv").read_text(encoding="utf-8")
    top_csv = (out_dir / "stats_top_passengers.csv").read_text(encoding="utf-8")

    summary = stats_json.get("summary", {})
    expected = summary.get("expected_eur", 0)
    p50 = summary.get("p50_eur", 0)
    p95 = summary.get("p95_eur", 0)
    n = summary.get("n_passengers", 0)

    html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>PIE Dashboard</title>
  <style>
    body {{ font-family: system-ui, Arial, sans-serif; margin: 24px; }}
    .kpi {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }}
    .card {{ border: 1px solid #ddd; border-radius: 12px; padding: 12px; }}
    pre {{ background: #f6f6f6; padding: 12px; border-radius: 12px; overflow-x: auto; }}
  </style>
</head>
<body>
  <h1>Passenger Impact Engine — Dashboard</h1>
  <p>Generated at: {_utc_now()}</p>

  <div class="kpi">
    <div class="card"><b>Passengers</b><br>{n}</div>
    <div class="card"><b>Expected</b><br>€{expected:,.2f}</div>
    <div class="card"><b>P50</b><br>€{p50:,.2f}</div>
    <div class="card"><b>P95</b><br>€{p95:,.2f}</div>
  </div>

  <h2>Group stats</h2>
  <pre>{groups_csv}</pre>

  <h2>Top passengers</h2>
  <pre>{top_csv}</pre>

  <p><small>Tip: this HTML is intentionally dependency-free for CI stability.</small></p>
</body>
</html>
"""
    (dash_dir / "index.html").write_text(html, encoding="utf-8")
    typer.echo(f"✅ wrote {dash_dir / 'index.html'}")
