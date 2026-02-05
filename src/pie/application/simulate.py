from __future__ import annotations

import heapq
import json
import math
import random
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from pie.domain.models import (
    DisruptionEvent,
    DisruptionType,
    EligibilityContext,
    Passenger,
    Segment,
)
from pie.domain.regulations.eu261 import EU261Config, assess_eu261
from pie.domain.runmeta import RunMeta, stable_hash
from pie.infrastructure.io.ledger import LedgerWriter


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _sample_normal(rng: random.Random, mean: float, std: float, lo: float, hi: float) -> float:
    # Box-Muller for stable deterministic sampling
    u1 = max(1e-12, rng.random())
    u2 = max(1e-12, rng.random())
    z = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
    return _clamp(mean + std * z, lo, hi)


def load_config(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def generate_population(cfg: dict, rng: random.Random) -> list[Passenger]:
    n = int(cfg["population"]["passengers"])
    mix = cfg["population"]["segments"]
    p_business = float(mix["business"])
    passengers: list[Passenger] = []

    for i in range(n):
        seg = Segment.BUSINESS if rng.random() < p_business else Segment.LEISURE
        fare = _sample_normal(
            rng,
            mean=320 if seg == Segment.LEISURE else 650,
            std=120 if seg == Segment.LEISURE else 220,
            lo=60,
            hi=2000,
        )
        refundable = True if seg == Segment.BUSINESS else (rng.random() < 0.20)
        passengers.append(
            Passenger(id=f"P{i:05d}", segment=seg, fare_paid=round(fare, 2), refundable=refundable)
        )
    return passengers


def sample_disruption(cfg: dict, rng: random.Random) -> DisruptionEvent:
    mix = cfg["scenario"]["disruption_mix"]
    p_delay = float(mix["delay"])
    if rng.random() < p_delay:
        dcfg = cfg["scenario"]["delay_minutes"]
        delay = int(round(_sample_normal(rng, dcfg["mean"], dcfg["std"], dcfg["min"], dcfg["max"])))
        return DisruptionEvent(dtype=DisruptionType.DELAY, delay_minutes=delay, cause="simulated")
    return DisruptionEvent(dtype=DisruptionType.CANCEL, delay_minutes=0, cause="simulated")


def run_monte_carlo(
    config_path: str,
    out_dir: str,
    audit: str = "both",
    ledger_mode: str = "all",
    ledger_topk: int = 50,
    ledger_sample: float = 0.05,
    ledger_chunk_size: int = 100,
) -> tuple[pd.DataFrame, dict[str, float]]:
    cfg = load_config(config_path)

    # --- validations ---
    if audit not in {"summary", "ledger", "both"}:
        raise ValueError(f"Invalid audit: {audit}")
    if ledger_mode not in {"all", "eligible", "topk", "sample"}:
        raise ValueError(f"Invalid ledger_mode: {ledger_mode}")
    if ledger_topk <= 0:
        raise ValueError("ledger_topk must be > 0")
    if not (0.0 < ledger_sample <= 1.0):
        raise ValueError("ledger_sample must be in (0, 1]")
    if ledger_chunk_size <= 0:
        raise ValueError("ledger_chunk_size must be > 0")

    seed = int(cfg["run"]["seed"])
    iterations = int(cfg["run"]["iterations"])

    config_hash = stable_hash(cfg)
    run_id = stable_hash(
        {
            "seed": seed,
            "iterations": iterations,
            "config_hash": config_hash,
            "audit": audit,
            "ledger_mode": ledger_mode,
            "ledger_topk": ledger_topk,
            "ledger_sample": ledger_sample,
            "ledger_chunk_size": ledger_chunk_size,
        }
    )

    rng = random.Random(seed)

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    run_meta = RunMeta(
        run_id=run_id,
        seed=seed,
        iterations=iterations,
        config_hash=config_hash,
        audit=audit,
    )
    (out / "run.json").write_text(
        json.dumps(run_meta.__dict__, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    passengers = generate_population(cfg, rng)

    s = cfg["scenario"]
    ctx = EligibilityContext(
        carrier_is_eu=bool(s["carrier_is_eu"]),
        dep_in_eu=bool(s["dep_in_eu"]),
        arr_in_eu=bool(s["arr_in_eu"]),
        distance_km=int(s["distance_km"]),
    )

    c = cfg["costs"]
    eu_cfg = EU261Config(
        meal_cost=float(c["meal_cost"]),
        hotel_cost_per_night=float(c["hotel_cost_per_night"]),
        ground_transport_cost=float(c["ground_transport_cost"]),
        refund_rate=float(c["refund_rate"]),
        rebooking_cost_mean=float(c["rebooking_cost_mean"]),
        rebooking_cost_std=float(c["rebooking_cost_std"]),
    )

    # --- audit log ---
    audit_path = out / "events.jsonl"
    audit_f = audit_path.open("w", encoding="utf-8")
    audit_f.write(json.dumps({"type": "run_start", "meta": run_meta.__dict__}, ensure_ascii=False) + "\n")

    # --- ledger setup (ONLY if audit includes ledger) ---
    ledger: LedgerWriter | None = None
    ledger_dir: Path | None = None
    ledger_path: Path | None = None
    current_chunk: int | None = None

    ledger_fields = [
        "run_id",
        "iteration",
        "seed",
        "passenger_id",
        "segment",
        "refundable",
        "dtype",
        "delay_minutes",
        "cash_comp_eur",
        "care_cost_eur",
        "refund_cost_eur",
        "rebooking_cost_eur",
        "total_cost_eur",
    ]

    # chunk/index bookkeeping
    ledger_rows_written = 0
    chunk_rows_written = 0
    chunk_start_it = 0
    chunks_meta: list[dict[str, Any]] = []

    def _open_ledger_for_chunk(chunk: int) -> None:
        nonlocal ledger, ledger_path
        assert ledger_dir is not None
        ledger_path = ledger_dir / f"entitlements_chunk_{chunk:05d}.csv.gz"
        ledger = LedgerWriter(ledger_path, ledger_fields).__enter__()

    def _close_and_record_chunk(chunk: int, end_iteration: int) -> None:
        """
        Close current ledger file and record metadata.
        We pass chunk explicitly so there is no filename parsing trap.
        """
        nonlocal ledger, ledger_path, chunk_rows_written, chunk_start_it

        assert ledger is not None
        assert ledger_path is not None

        ledger.__exit__(None, None, None)
        chunks_meta.append(
            {
                "chunk": chunk,
                "file": ledger_path.name,
                "start_iteration": chunk_start_it,
                "end_iteration": end_iteration,
                "rows_written": chunk_rows_written,
            }
        )
        chunk_rows_written = 0

    def _write_ledger_row(row: dict[str, Any]) -> None:
        nonlocal ledger_rows_written, chunk_rows_written
        assert ledger is not None
        ledger.write_row(row)
        ledger_rows_written += 1
        chunk_rows_written += 1

    if audit in {"ledger", "both"}:
        ledger_dir = out / "ledger"
        ledger_dir.mkdir(parents=True, exist_ok=True)
        current_chunk = 0
        chunk_start_it = 0
        _open_ledger_for_chunk(current_chunk)

    # --- simulation ---
    rows: list[dict[str, Any]] = []

    for it in range(iterations):
        # rotate chunk files (iteration-based)
        if ledger is not None:
            assert current_chunk is not None
            target_chunk = it // ledger_chunk_size
            if target_chunk != current_chunk:
                _close_and_record_chunk(chunk=current_chunk, end_iteration=it - 1)
                current_chunk = target_chunk
                chunk_start_it = it
                _open_ledger_for_chunk(current_chunk)

        event = sample_disruption(cfg, rng)

        rebook_cost = _sample_normal(
            rng,
            mean=eu_cfg.rebooking_cost_mean,
            std=eu_cfg.rebooking_cost_std,
            lo=0,
            hi=2000,
        )

        total_cost = 0.0
        cash = 0.0
        care = 0.0
        refund = 0.0
        rebook_total = 0.0

        # topk heap: store only K passenger rows for this iteration
        topk_heap: list[tuple[float, dict[str, Any]]] = []

        for p in passengers:
            outcome = assess_eu261(p, ctx, event, eu_cfg, sampled_rebooking_cost_eur=rebook_cost)

            total_cost += outcome.total_cost_eur
            cash += outcome.cash_comp_eur
            care += outcome.care_cost_eur
            refund += outcome.refund_cost_eur
            rebook_total += outcome.rebooking_cost_eur

            if ledger is None:
                continue

            ledger_row = {
                "run_id": run_id,
                "iteration": it,
                "seed": seed,
                "passenger_id": p.id,
                "segment": p.segment.value,
                "refundable": p.refundable,
                "dtype": event.dtype.value,
                "delay_minutes": event.delay_minutes,
                "cash_comp_eur": round(outcome.cash_comp_eur, 2),
                "care_cost_eur": round(outcome.care_cost_eur, 2),
                "refund_cost_eur": round(outcome.refund_cost_eur, 2),
                "rebooking_cost_eur": round(outcome.rebooking_cost_eur, 2),
                "total_cost_eur": round(outcome.total_cost_eur, 2),
            }

            eligible_flag = outcome.cash_comp_eur > 0

            # Streaming modes (no buffering):
            if ledger_mode == "all":
                _write_ledger_row(ledger_row)

            elif ledger_mode == "sample":
                if rng.random() < ledger_sample:
                    _write_ledger_row(ledger_row)

            elif ledger_mode == "eligible":
                if eligible_flag:
                    _write_ledger_row(ledger_row)

            elif ledger_mode == "topk":
                # Keep only K by total_cost_eur using min-heap
                cost_val = outcome.total_cost_eur
                if len(topk_heap) < ledger_topk:
                    heapq.heappush(topk_heap, (cost_val, ledger_row))
                else:
                    if cost_val > topk_heap[0][0]:
                        heapq.heapreplace(topk_heap, (cost_val, ledger_row))

        # Flush topk rows AFTER passenger loop
        if ledger is not None and ledger_mode == "topk":
            for _, r in sorted(topk_heap, key=lambda x: x[0], reverse=True):
                _write_ledger_row(r)

        row = {
            "iteration": it,
            "dtype": event.dtype.value,
            "delay_minutes": event.delay_minutes,
            "total_cost_eur": round(total_cost, 2),
            "cash_comp_eur": round(cash, 2),
            "care_cost_eur": round(care, 2),
            "refund_cost_eur": round(refund, 2),
            "rebooking_cost_eur": round(rebook_total, 2),
        }
        rows.append(row)

        audit_f.write(
            json.dumps(
                {"type": "iteration_result", "run_id": run_id, "seed": seed, "data": row},
                ensure_ascii=False,
            )
            + "\n"
        )

    # close last chunk
    if ledger is not None:
        assert current_chunk is not None
        _close_and_record_chunk(chunk=current_chunk, end_iteration=iterations - 1)

    # --- outputs ---
    df = pd.DataFrame(rows)
    df.to_csv(out / "cost_distribution.csv", index=False)

    summary = {
        "iterations": float(iterations),
        "mean_total_cost": float(df["total_cost_eur"].mean()),
        "p95_total_cost": float(df["total_cost_eur"].quantile(0.95)),
        "cvar95_total_cost": float(
            df[df["total_cost_eur"] >= df["total_cost_eur"].quantile(0.95)]["total_cost_eur"].mean()
        ),
        "p_loss_over_0": float((df["total_cost_eur"] > 0).mean()),
    }
    pd.DataFrame([summary]).to_csv(out / "summary.csv", index=False)

    # ledger index (deep metadata)
    if audit in {"ledger", "both"}:
        assert ledger_dir is not None
        index = {
            "run_id": run_id,
            "seed": seed,
            "iterations": iterations,
            "passengers": len(passengers),
            "config_hash": config_hash,
            "audit": audit,
            "ledger": {
                "mode": ledger_mode,
                "topk": ledger_topk,
                "sample": ledger_sample,
                "chunk_size_iterations": ledger_chunk_size,
                "dir": str(ledger_dir),
                "fields": ledger_fields,
                "total_rows_written": ledger_rows_written,
                "chunks": chunks_meta,
            },
        }
        (out / "ledger_index.json").write_text(json.dumps(index, indent=2), encoding="utf-8")

    # Run end marker
    audit_f.write(json.dumps({"type": "run_end", "run_id": run_id, "summary": summary}, ensure_ascii=False) + "\n")
    audit_f.close()

    report_html = f"""<!doctype html>
<html>
<head><meta charset="utf-8"><title>Passenger Impact Engine - EU261 Report</title></head>
<body>
<h1>Passenger Impact Engine (EU261) - Summary</h1>
<ul>
  <li>Iterations: {int(summary["iterations"])}</li>
  <li>Mean total cost (EUR): {summary["mean_total_cost"]:.2f}</li>
  <li>P(loss): {summary["p_loss_over_0"]:.3f}</li>
  <li>P95 total cost (EUR): {summary["p95_total_cost"]:.2f}</li>
  <li>CVaR95 total cost (EUR): {summary["cvar95_total_cost"]:.2f}</li>
</ul>
<p>Artifacts:</p>
<ul>
  <li>cost_distribution.csv</li>
  <li>summary.csv</li>
  <li>events.jsonl (audit log)</li>
  <li>ledger/entitlements_chunk_*.csv.gz (passenger ledger; if audit=ledger|both)</li>
  <li>ledger_index.json (ledger chunk index; if audit=ledger|both)</li>
</ul>
</body>
</html>"""
    (out / "report.html").write_text(report_html, encoding="utf-8")

    return df, summary
