from __future__ import annotations

import argparse
from pathlib import Path

from pie.application.engine import EngineConfig
from pie.application.run_pipeline import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="pie", description="Passenger Impact Engine")
    sub = p.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="Run the pipeline and generate dashboard + artifacts")
    run_p.add_argument("--mode", choices=["auto", "real", "demo"], default="auto", help="Execution mode")
    run_p.add_argument("--runs", type=int, default=200, help="Number of Monte Carlo runs")
    run_p.add_argument("--tickets-per-flight", type=int, default=50, help="Tickets per flight")
    run_p.add_argument("--seed", type=int, default=42, help="Random seed (determinism)")
    run_p.add_argument("--out", type=str, default="out", help="Output directory")

    # ✅ PDF export
    run_p.add_argument("--pdf", action="store_true", help="Generate EXECUTIVE_REPORT.pdf in output folder")

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        cfg = EngineConfig(
            seed=args.seed,
            runs=args.runs,
            tickets_per_flight=args.tickets_per_flight,
            out_dir=Path(args.out),
            mode=args.mode,
            pdf=args.pdf,
        )
        dash = run_pipeline(cfg)
        print(f"✅ Dashboard generated: {dash}")
        if args.pdf:
            print(f"✅ PDF generated: {Path(args.out) / 'EXECUTIVE_REPORT.pdf'}")
        return 0

    parser.error("Unknown command")
    return 2
