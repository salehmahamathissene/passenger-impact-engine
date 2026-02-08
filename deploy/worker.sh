#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="${OUT_DIR:-out}"

rm -rf "${OUT_DIR}"
mkdir -p "${OUT_DIR}"

echo "👷 Worker: running PIE pipeline (new CLI)..."
pie run --config configs/demo.yml --out "${OUT_DIR}"

echo "✅ Worker finished. Files:"
find "${OUT_DIR}" -maxdepth 3 -type f || true
