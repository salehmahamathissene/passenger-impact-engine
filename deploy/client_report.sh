#!/usr/bin/env bash
set -euo pipefail
OUT="${1:-out_client}"
CFG="${2:-configs/demo.yml}"

rm -rf "$OUT" && mkdir -p "$OUT"

pie simulate --config "$CFG" --out "$OUT" --audit ledger
pie merge-ledger --out "$OUT"
pie stats --out "$OUT" --top 50 --by segment,dtype --metric p95 --min-cost 200 --sample-size 2000
pie dashboard --out "$OUT" --top 50

echo "✅ Client report ready in: $OUT"
