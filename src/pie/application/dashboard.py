from __future__ import annotations

from pathlib import Path
from typing import Any


def render_dashboard_html(
    path: Path,
    kpis: dict[str, float],
    image_paths: dict[str, str],
    csv_paths: dict[str, str],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Passenger Impact Engine</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body {{ font-family: system-ui, Arial; margin: 24px; background:#0b1220; color:#e8eefc; }}
    .grid {{ display:grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap:16px; }}
    .card {{ background:#121b2e; border:1px solid #223052; border-radius:16px; padding:16px; }}
    h1 {{ margin: 0 0 16px; }}
    .kpi {{ font-size: 26px; font-weight: 700; }}
    .muted {{ color:#a9b7d8; font-size: 13px; }}
    a {{ color:#8ab4ff; }}
    img {{ width:100%; border-radius:12px; border:1px solid #223052; }}
  </style>
</head>
<body>
  <h1>Passenger Impact Engine — Contract-Ready Demo</h1>

  <div class="grid">
    <div class="card">
      <div class="muted">Mean total cost (per run)</div>
      <div class="kpi">{kpis["mean_total_cost"]:,.0f}</div>
    </div>
    <div class="card">
      <div class="muted">P95 total cost</div>
      <div class="kpi">{kpis["p95_total_cost"]:,.0f}</div>
    </div>
    <div class="card">
      <div class="muted">CVaR 95</div>
      <div class="kpi">{kpis["cvar95_total_cost"]:,.0f}</div>
    </div>
  </div>

  <div class="grid" style="margin-top:16px;">
    <div class="card">
      <div class="muted">Cost decomposition</div>
      <img src="{image_paths["cost_breakdown"]}" alt="Cost breakdown">
      <div class="muted" style="margin-top:10px;">
        Download CSV: <a href="{csv_paths["cost_breakdown"]}">cost_breakdown.csv</a>
      </div>
    </div>

    <div class="card">
      <div class="muted">Top flights by expected disruption cost</div>
      <img src="{image_paths["top_flights"]}" alt="Top flights">
      <div class="muted" style="margin-top:10px;">
        Download CSV: <a href="{csv_paths["top_flights"]}">top_flights.csv</a>
      </div>
    </div>

    <div class="card">
      <div class="muted">Passenger cost by cabin segment</div>
      <img src="{image_paths["group_stats"]}" alt="Group stats">
      <div class="muted" style="margin-top:10px;">
        Download CSV: <a href="{csv_paths["group_stats"]}">group_stats.csv</a>
      </div>
    </div>
  </div>

  <div class="card" style="margin-top:16px;">
    <div class="muted">Audit trace</div>
    <div style="margin-top:8px;">
      Download ledger: <a href="{csv_paths["ledger"]}">ledger.csv.gz</a>
      <span class="muted"> (passenger-level cost breakdown, per run)</span>
    </div>
  </div>

</body>
</html>
"""
    path.write_text(html, encoding="utf-8")
