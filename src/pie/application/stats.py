from __future__ import annotations

import csv
import gzip
import json
import math
import random
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path


def _parse_by(by: str) -> list[str]:
    by = by.strip().lower()
    if by in {"", "none"}:
        return []
    parts = [p.strip() for p in by.split(",") if p.strip()]
    allowed = {"segment", "dtype"}
    bad = [p for p in parts if p not in allowed]
    if bad:
        raise ValueError(f"Invalid --by value(s): {bad}. Allowed: none|segment|dtype|segment,dtype")
    out: list[str] = []
    for p in parts:
        if p not in out:
            out.append(p)
    return out


def _source_path(out_dir: str) -> Path:
    out = Path(out_dir)
    merged = out / "entitlements.csv.gz"
    if merged.exists():
        return merged

    idx = out / "ledger_index.json"
    if idx.exists():
        raise FileNotFoundError(
            "Missing out/entitlements.csv.gz. Run: pie merge-ledger --out out "
            "(or simulate with --ledger-merge)."
        )
    raise FileNotFoundError("No entitlements.csv.gz and no ledger_index.json found in out dir.")


def _iter_rows_gz(path: Path) -> Iterator[dict[str, str]]:
    with gzip.open(path, "rt", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError(f"Missing header in {path}")
        yield from reader


def _q_from_sorted(sorted_vals: list[float], q: float) -> float:
    if not sorted_vals:
        return float("nan")
    if q <= 0:
        return float(sorted_vals[0])
    if q >= 1:
        return float(sorted_vals[-1])
    n = len(sorted_vals)
    pos = (n - 1) * q
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return float(sorted_vals[lo])
    w = pos - lo
    return float(sorted_vals[lo] * (1 - w) + sorted_vals[hi] * w)


@dataclass
class Reservoir:
    k: int
    rng: random.Random
    n: int = 0
    data: list[float] = None  # type: ignore

    def __post_init__(self) -> None:
        self.data = []

    def add(self, x: float) -> None:
        self.n += 1
        if self.k <= 0:
            return
        if len(self.data) < self.k:
            self.data.append(x)
            return
        j = self.rng.randint(1, self.n)
        if j <= self.k:
            self.data[j - 1] = x

    def quantiles(self) -> dict[str, float]:
        if not self.data:
            return {"p50": float("nan"), "p95": float("nan"), "p99": float("nan")}
        s = sorted(self.data)
        return {
            "p50": _q_from_sorted(s, 0.50),
            "p95": _q_from_sorted(s, 0.95),
            "p99": _q_from_sorted(s, 0.99),
        }


@dataclass
class GroupAgg:
    rows: int = 0
    sum_total: float = 0.0
    min_total: float = float("inf")
    max_total: float = float("-inf")

    sum_cash: float = 0.0
    sum_care: float = 0.0
    sum_refund: float = 0.0
    sum_rebook: float = 0.0

    res: Reservoir = None  # type: ignore

    def as_dict(self) -> dict[str, float]:
        if self.res is None:
            q = {"p50": float("nan"), "p95": float("nan"), "p99": float("nan")}
        else:
            q = self.res.quantiles()

        mean = self.sum_total / self.rows if self.rows else float("nan")

        return {
            "rows": float(self.rows),
            "mean_total_cost_eur": float(mean),
            "sum_total_cost_eur": float(self.sum_total),
            "min_total_cost_eur": float(self.min_total if self.rows else float("nan")),
            "max_total_cost_eur": float(self.max_total if self.rows else float("nan")),
            "p50_total_cost_eur": float(q["p50"]),
            "p95_total_cost_eur": float(q["p95"]),
            "p99_total_cost_eur": float(q["p99"]),
            "sum_cash_comp_eur": float(self.sum_cash),
            "sum_care_cost_eur": float(self.sum_care),
            "sum_refund_cost_eur": float(self.sum_refund),
            "sum_rebooking_cost_eur": float(self.sum_rebook),
        }


@dataclass
class PassengerAgg:
    rows: int = 0
    sum_total: float = 0.0
    max_total: float = float("-inf")
    res: Reservoir = None  # type: ignore

    def score(self, metric: str) -> float:
        if self.rows == 0:
            return float("-inf")
        if metric == "mean":
            return self.sum_total / self.rows
        if metric == "sum":
            return self.sum_total
        if metric == "max":
            return self.max_total
        if metric == "p95":
            qs = self.res.quantiles() if self.res is not None else {"p95": float("nan")}
            return float(qs["p95"])
        raise ValueError(f"Invalid metric: {metric}")

    def as_row(self, passenger_id: str) -> dict[str, float | str]:
        mean = self.sum_total / self.rows if self.rows else float("nan")
        if self.res is None:
            qs = {"p50": float("nan"), "p95": float("nan"), "p99": float("nan")}
        else:
            qs = self.res.quantiles()

        return {
            "passenger_id": passenger_id,
            "rows": float(self.rows),
            "mean_total_cost_eur": float(mean),
            "sum_total_cost_eur": float(self.sum_total),
            "max_total_cost_eur": float(self.max_total if self.rows else float("nan")),
            "p50_total_cost_eur": float(qs["p50"]),
            "p95_total_cost_eur": float(qs["p95"]),
            "p99_total_cost_eur": float(qs["p99"]),
        }


def compute_stats_v2(
    out_dir: str,
    top: int = 20,
    by: str = "segment",
    metric: str = "mean",
    fmt: str = "both",
    min_cost: float = 0.0,
    sample_size: int = 5000,
    seed: int = 1337,
) -> dict:
    metric = metric.strip().lower()
    if metric not in {"mean", "sum", "max", "p95"}:
        raise ValueError("metric must be one of: mean|sum|max|p95")

    fmt = fmt.strip().lower()
    if fmt not in {"json", "csv", "both"}:
        raise ValueError("format must be one of: json|csv|both")

    if top <= 0:
        raise ValueError("--top must be > 0")
    if min_cost < 0:
        raise ValueError("--min-cost must be >= 0")
    if sample_size < 0:
        raise ValueError("--sample-size must be >= 0")

    keys = _parse_by(by)
    src = _source_path(out_dir)

    rng = random.Random(seed)

    groups: dict[str, GroupAgg] = {}
    pax: dict[str, PassengerAgg] = {}

    total_rows = 0
    kept_rows = 0

    for row in _iter_rows_gz(src):
        total_rows += 1

        try:
            total = float(row["total_cost_eur"])
        except (KeyError, ValueError) as e:
            raise ValueError(f"Bad total_cost_eur at row {total_rows}: {e}") from e

        if total < min_cost:
            continue
        kept_rows += 1

        if not keys:
            gkey = "all"
        else:
            parts = [f"{k}={row.get(k, '')}" for k in keys]
            gkey = "|".join(parts)

        if gkey not in groups:
            groups[gkey] = GroupAgg(res=Reservoir(k=sample_size, rng=rng))
        g = groups[gkey]

        g.rows += 1
        g.sum_total += total
        g.min_total = min(g.min_total, total)
        g.max_total = max(g.max_total, total)
        g.res.add(total)

        # Fix B023: don't close over loop var in nested function
        def _f(r: dict[str, str], name: str) -> float:
            try:
                return float(r.get(name, "0") or 0)
            except ValueError:
                return 0.0

        g.sum_cash += _f(row, "cash_comp_eur")
        g.sum_care += _f(row, "care_cost_eur")
        g.sum_refund += _f(row, "refund_cost_eur")
        g.sum_rebook += _f(row, "rebooking_cost_eur")

        pid = row.get("passenger_id", "")
        if pid:
            if pid not in pax:
                pax[pid] = PassengerAgg(res=Reservoir(k=min(sample_size, 2000), rng=rng))
            pa = pax[pid]
            pa.rows += 1
            pa.sum_total += total
            pa.max_total = max(pa.max_total, total)
            pa.res.add(total)

    top_items: list[tuple[float, str, PassengerAgg]] = []
    for pid, pa in pax.items():
        top_items.append((pa.score(metric), pid, pa))
    top_items.sort(key=lambda x: x[0], reverse=True)
    top_items = top_items[:top]

    top_passengers = []
    for sc, pid, pa in top_items:
        r = pa.as_row(pid)
        r["score"] = float(sc)
        r["metric"] = metric
        top_passengers.append(r)

    groups_out = {k: v.as_dict() for k, v in groups.items()}

    return {
        "ok": True,
        "out_dir": out_dir,
        "source": str(src),
        "by": by,
        "metric": metric,
        "format": fmt,
        "min_cost": float(min_cost),
        "sample_size": int(sample_size),
        "total_rows": int(total_rows),
        "kept_rows": int(kept_rows),
        "groups": groups_out,
        "top_passengers": top_passengers,
    }


def write_stats_artifacts_v2(out_dir: str, stats: dict) -> dict[str, str]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    stats_json = out / "stats.json"
    groups_csv = out / "stats_groups.csv"
    top_csv = out / "stats_top_passengers.csv"

    stats_json.write_text(json.dumps(stats, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    group_rows: list[dict] = []
    for gname, g in stats["groups"].items():
        row = {"group": gname}
        row.update(g)
        group_rows.append(row)

    if group_rows:
        fieldnames = list(group_rows[0].keys())
        with groups_csv.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            for r in group_rows:
                w.writerow(r)
    else:
        groups_csv.write_text("group\n", encoding="utf-8")

    if stats["top_passengers"]:
        fieldnames = list(stats["top_passengers"][0].keys())
        with top_csv.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            for r in stats["top_passengers"]:
                w.writerow(r)
    else:
        top_csv.write_text("passenger_id\n", encoding="utf-8")

    return {
        "stats_json": str(stats_json),
        "groups_csv": str(groups_csv),
        "top_passengers_csv": str(top_csv),
    }
