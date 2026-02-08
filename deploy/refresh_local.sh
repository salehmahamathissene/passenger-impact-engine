#!/usr/bin/env bash
set -euo pipefail

rm -rf out
mkdir -p out

echo "🚀 Running PIE pipeline (new CLI)..."
pie run --config configs/demo.yml --out out

echo "✅ Done. Outputs in out/"
find out -maxdepth 3 -type f || true
