#!/usr/bin/env bash
set -euo pipefail

echo "🧪 Starting Docker CI smoke test..."

# Use a temporary directory that Docker can write to
TEST_DIR="${TEST_OUTPUT:-$(mktemp -d)}"
echo "Test directory: $TEST_DIR"

# Function to cleanup
cleanup() {
    echo "Cleaning up..."
    docker run --rm -v "$TEST_DIR:/cleanup" alpine sh -c "rm -rf /cleanup/*" 2>/dev/null || true
    if [[ -z "${TEST_OUTPUT:-}" ]]; then
        rm -rf "$TEST_DIR"
    fi
}
trap cleanup EXIT

echo "1. Building Docker image..."
docker build -t pie:ci .

echo "2. Testing simulation pipeline..."
docker run --rm \
  -u "$(id -u):$(id -g)" \
  -v "$TEST_DIR:/out" \
  pie:ci simulate \
  --config configs/demo.yml \
  --out /out \
  --audit ledger

docker run --rm \
  -u "$(id -u):$(id -g)" \
  -v "$TEST_DIR:/out" \
  pie:ci merge-ledger --out /out

docker run --rm \
  -u "$(id -u):$(id -g)" \
  -v "$TEST_DIR:/out" \
  pie:ci stats \
  --out /out \
  --top 5 \
  --by segment,dtype \
  --metric p95 \
  --min-cost 200 \
  --sample-size 500

docker run --rm \
  -u "$(id -u):$(id -g)" \
  -v "$TEST_DIR:/out" \
  pie:ci dashboard --out /out --top 5

echo "3. Verifying output..."
if docker run --rm -v "$TEST_DIR:/check" alpine sh -c "ls -la /check/dashboard/index.html" >/dev/null 2>&1; then
    echo "✅ Dashboard generated successfully"
    echo "📊 Files created:"
    docker run --rm -v "$TEST_DIR:/list" alpine find /list -type f | wc -l | xargs echo "   Total files:"
else
    echo "❌ ERROR: Dashboard not created"
    exit 1
fi

echo "🎉 Docker CI smoke test PASSED!"
