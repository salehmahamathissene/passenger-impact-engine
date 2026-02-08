#!/usr/bin/env bash
set -euo pipefail

rm -rf out_tmp
mkdir -p out_tmp

echo "🚀 Running PIE pipeline (new CLI)..."
pie run --config configs/demo.yml --out out_tmp

echo "✅ Done. Outputs in out_tmp/"
find out_tmp -maxdepth 3 -type f || true
