#!/usr/bin/env bash
set -euo pipefail

echo "🧪 Starting Docker CI smoke test..."

TEST_DIR="test_output_ci"
rm -rf "$TEST_DIR"
mkdir -p "$TEST_DIR"

echo "1) Building Docker image..."
docker build -t pie:ci .

echo "2) Running pipeline in container..."
docker run --rm \
  --entrypoint bash \
  -v "$PWD/$TEST_DIR:/test_out" \
  pie:ci \
  -lc '
    set -euo pipefail

    echo "=== pie --help ==="
    pie --help || true

    echo "=== Running PIE pipeline ==="
    pie run --config configs/demo.yml --out /test_out

    echo "=== Listing outputs ==="
    find /test_out -maxdepth 4 -type f -print || true

    echo "=== Verifying output ==="
    if [[ -f /test_out/dashboard/index.html ]]; then
      echo "✅ Dashboard found"
      exit 0
    fi

    if [[ -f /test_out/report.pdf ]]; then
      echo "✅ PDF report found"
      exit 0
    fi

    echo "❌ No expected artifacts found"
    exit 1
  '

echo "✅ Docker CI smoke test PASSED!"
echo "📦 Host generated files:"
find "$TEST_DIR" -maxdepth 4 -type f -print || true
