#!/usr/bin/env bash
set -euo pipefail

cd /home/saleh/portfolio/passenger-impact-engine

echo "$(date): Starting PIE refresh..."

# Activate virtual environment if needed
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Clean and run simulation
rm -rf out
pie simulate --config configs/demo.yml --out out --audit ledger \
  --ledger-mode topk --ledger-topk 10 --ledger-chunk-size 100 --ledger-merge

pie stats --out out --top 20 --by segment,dtype --metric p95 --min-cost 200 --sample-size 2000
pie dashboard --out out --top 20

echo "$(date): ✅ Refresh completed successfully"
echo "Dashboard updated at: $(date)" > out/dashboard/LAST_REFRESH.txt
