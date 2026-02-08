#!/usr/bin/env bash
set -euo pipefail

echo "== Start stack =="
docker-compose -f deploy/docker-compose.yml up -d

echo
echo "== Status (wait until healthy) =="
for i in {1..30}; do
  out="$(docker-compose -f deploy/docker-compose.yml ps)"
  echo "$out" | sed -n '1,10p'
  echo "$out" | grep -q "healthy" && break
  sleep 2
done

echo
echo "== Verify dashboard title =="
curl -s http://localhost:8010/ | grep -o '<title>[^<]*</title>'

echo
echo "== Worker logs (last 15 lines) =="
docker logs --tail 15 --timestamps pie-worker

echo
echo "== Done. Open: http://localhost:8010/ =="
