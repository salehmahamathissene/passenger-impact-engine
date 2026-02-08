#!/usr/bin/env bash
set -euo pipefail

CFG="${1:-configs/demo.yml}"
OUT="${2:-out_client}"

rm -rf "$OUT"
mkdir -p "$OUT"

echo "📄 Generating client report using PIE (new CLI)"
echo "Config: $CFG"
echo "Out:    $OUT"

pie run --config "$CFG" --out "$OUT"

echo "✅ Done. Files:"
find "$OUT" -maxdepth 3 -type f || true
