#!/usr/bin/env bash
set -euo pipefail

log() { echo "[$(date -Is)] $*"; }

OUT_DIR="/app/out"
SITE_DIR="/app/site"

log "🚀 PIE worker starting"

while true; do
  log "=== cycle start ==="

  pie simulate \
    --config /app/configs/demo.yml \
    --out "${OUT_DIR}" \
    --audit ledger \
    --ledger-mode topk \
    --ledger-topk 10 \
    --ledger-chunk-size 100

  pie merge-ledger --out "${OUT_DIR}" || log "⚠️ merge-ledger skipped"

  pie stats \
    --out "${OUT_DIR}" \
    --top 20 \
    --by segment,dtype \
    --metric p95 \
    --min-cost 200 \
    --sample-size 2000

  pie dashboard --out "${OUT_DIR}" --top 20

  # Atomic publish to nginx volume
  if [[ -f "${OUT_DIR}/dashboard/index.html" ]]; then
    log "Publishing dashboard (atomic)"
    tmp="${SITE_DIR}.tmp"
    rm -rf "${tmp}"
    mkdir -p "${tmp}"
    cp -r "${OUT_DIR}/dashboard/"* "${tmp}/"
    rm -rf "${SITE_DIR:?}/"*
    mv "${tmp}/"* "${SITE_DIR}/"
    rm -rf "${tmp}"
    log "✅ dashboard published"
  else
    log "❌ dashboard missing: ${OUT_DIR}/dashboard/index.html"
  fi

  log "=== cycle complete; sleeping 900s ==="
  sleep 900
done
