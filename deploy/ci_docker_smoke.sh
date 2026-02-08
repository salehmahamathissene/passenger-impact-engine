#!/usr/bin/env bash
set -euo pipefail

echo "🧪 Starting Docker CI smoke test..."

TEST_DIR="test_output_ci"
ROOT_DIR="$(pwd)"
OUT_HOST="$ROOT_DIR/$TEST_DIR"

# If previous runs created root-owned files, clean them.
sudo rm -rf "$OUT_HOST"
mkdir -p "$OUT_HOST"

echo "1) Building Docker image..."
docker build -t pie:ci .

echo "2) Inspecting CLI in container..."
docker run --rm --entrypoint bash pie:ci -lc 'pie --help; echo; pie run --help'

echo "3) Running pipeline in container..."
docker run --rm \
  --user "$(id -u):$(id -g)" \
  -e HOME=/tmp \
  -e MPLCONFIGDIR=/tmp/mpl \
  --entrypoint bash \
  -v "$OUT_HOST:/test_out" \
  pie:ci \
  -lc '
    set -euo pipefail

    echo "=== Running PIE pipeline ==="
    pie run --mode demo --runs 50 --tickets-per-flight 5 --seed 123 --out /test_out --pdf

    echo "=== Listing outputs ==="
    find /test_out -maxdepth 6 -type f -print || true

    echo "=== Verifying output ==="
    if [[ -f /test_out/dashboard/index.html ]]; then
      echo "✅ dashboard/index.html exists"
    else
      echo "❌ dashboard/index.html missing"
      exit 1
    fi

    if [[ -f /test_out/EXECUTIVE_REPORT.pdf ]]; then
      echo "✅ EXECUTIVE_REPORT.pdf exists"
    else
      echo "❌ EXECUTIVE_REPORT.pdf missing"
      exit 1
    fi

    echo "✅ Smoke test passed"
  '
