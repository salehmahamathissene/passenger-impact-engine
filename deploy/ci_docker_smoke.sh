#!/usr/bin/env bash
set -euo pipefail

echo "🧪 Starting Docker CI smoke test..."

# Create test directory
TEST_DIR="test_output_ci"
rm -rf "$TEST_DIR"
mkdir -p "$TEST_DIR"

echo "1. Building Docker image..."
docker build -t pie:ci .

echo "2. Running pipeline in container..."

# Run all commands in one container session
docker run --rm \
  -v "$PWD/$TEST_DIR:/test_out" \
  pie:ci \
  bash -c "
    set -e
    echo '=== Running simulation ==='
    pie simulate --config configs/demo.yml --out /test_out --audit ledger --ledger-mode topk --ledger-topk 10 --ledger-chunk-size 100
    
    echo '=== Merging ledger ==='
    pie merge-ledger --out /test_out
    
    echo '=== Generating statistics ==='
    pie stats --out /test_out --top 5 --by segment,dtype --metric p95 --min-cost 200 --sample-size 500
    
    echo '=== Creating dashboard ==='
    pie dashboard --out /test_out --top 5
    
    echo '=== Verifying output ==='
    if [[ -f /test_out/dashboard/index.html ]]; then
      echo '✅ Pipeline completed successfully'
      exit 0
    else
      echo '❌ Dashboard not found'
      exit 1
    fi
  "

# Check result
if [[ $? -eq 0 ]] && [[ -f "$TEST_DIR/dashboard/index.html" ]]; then
    echo "✅ Docker CI smoke test PASSED!"
    echo "📊 Files generated in $TEST_DIR/:"
    ls -la "$TEST_DIR/dashboard/"
    exit 0
else
    echo "❌ Docker CI smoke test FAILED!"
    exit 1
fi
