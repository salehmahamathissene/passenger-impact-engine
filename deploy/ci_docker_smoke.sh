#!/usr/bin/env bash
set -euo pipefail

rm -rf out_ci && mkdir -p out_ci

docker build -t pie:ci .

docker run --rm -v "$PWD/out_ci:/out" pie:ci simulate --config configs/demo.yml --out /out --audit ledger
docker run --rm -v "$PWD/out_ci:/out" pie:ci merge-ledger --out /out
docker run --rm -v "$PWD/out_ci:/out" pie:ci stats --out /out --top 5 --by segment,dtype --metric p95 --min-cost 200 --sample-size 500
docker run --rm -v "$PWD/out_ci:/out" pie:ci dashboard --out /out --top 5

test -f out_ci/dashboard/index.html
echo "✅ docker smoke test OK"
