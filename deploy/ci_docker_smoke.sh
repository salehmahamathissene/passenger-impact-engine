#!/usr/bin/env bash
set -euo pipefail

UIDGID="$(id -u):$(id -g)"
OUT="$PWD/out_ci"

# clean even if previous run wrote root-owned files
sudo rm -rf "$OUT"
mkdir -p "$OUT"

docker build -t pie:ci .

docker run --rm -u "$UIDGID" -v "$OUT:/out" pie:ci simulate --config configs/demo.yml --out /out --audit ledger
docker run --rm -u "$UIDGID" -v "$OUT:/out" pie:ci merge-ledger --out /out
docker run --rm -u "$UIDGID" -v "$OUT:/out" pie:ci stats --out /out --top 5 --by segment,dtype --metric p95 --min-cost 200 --sample-size 500
docker run --rm -u "$UIDGID" -v "$OUT:/out" pie:ci dashboard --out /out --top 5

test -f out_ci/dashboard/index.html
echo "✅ docker smoke test OK"
