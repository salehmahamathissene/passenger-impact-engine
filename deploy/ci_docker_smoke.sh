#!/usr/bin/env bash
set -euo pipefail

echo "🧪 Starting Docker CI smoke test..."

TEST_DIR="test_output_ci"
rm -rf "$TEST_DIR"
mkdir -p "$TEST_DIR"

echo "1. Building Docker image..."
docker build -t pie:ci .

echo "2. Running pipeline in container..."
docker run --rm \
  -v "$PWD/$TEST_DIR:/test_out" \
  pie:ci \
  bash -lc "
    set -e
    echo '=== Running PIE pipeline (new CLI) ==='
    pie run --config configs/demo.yml --out /test_out

    echo '=== Verifying output ==='
    if [[ -f /test_out/dashboard/index.html ]]; then
      echo '✅ Dashboard found'
      exit 0
    fi

    if [[ -f /test_out/report.pdf ]]; then
      echo '✅ PDF report found'
      exit 0
    fi

    echo '❌ No expected artifacts found in /test_out'
    echo 'Contents:'
    find /test_out -maxdepth 3 -type f || true
    exit 1
  "

echo "✅ Docker CI smoke test PASSED!"
echo "📦 Generated files:"
find "$TEST_DIR" -maxdepth 3 -type f || true
