#!/usr/bin/env bash
set -euo pipefail
cd /home/saleh/portfolio/passenger-impact-engine

rm -rf out_tmp
mkdir -p out_tmp

pie simulate --config configs/demo.yml --out out_tmp --audit ledger --ledger-mode topk --ledger-topk 10 --ledger-chunk-size 100 --ledger-merge
pie stats --out out_tmp --top 20 --by segment,dtype --metric p95 --min-cost 200 --sample-size 2000
pie dashboard --out out_tmp --top 20

rm -rf out_old || true
[ -d out ] && mv out out_old || true
mv out_tmp out

systemctl --user restart pie-dashboard.service
