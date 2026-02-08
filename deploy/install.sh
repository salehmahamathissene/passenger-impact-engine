#!/usr/bin/env bash
set -euo pipefail

cd /home/saleh/portfolio/passenger-impact-engine

# sanity checks
command -v docker >/dev/null
command -v docker-compose >/dev/null

# start web
docker-compose -f deploy/docker-compose.yml up -d pie-web

# initial refresh now
docker-compose -f deploy/docker-compose.yml run --rm pie-refresh

echo
echo "✅ PIE dashboard ready:"
echo "   http://<SERVER_IP>:8010/index.html"
echo "   (Basic Auth enabled)"
