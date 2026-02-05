# PIE Deployment (Docker)

This deployment runs:

- **pie-worker**: simulation + stats + dashboard generation (refreshes every 15 minutes)
- **pie-web (nginx)**: serves the generated dashboard

## Start

```bash
docker-compose -f deploy/docker-compose.yml up -d
```

Open in browser:

- http://localhost:8010/

## Verify

```bash
curl -s http://localhost:8010/ | grep -o '<title>[^<]*</title>'
docker-compose -f deploy/docker-compose.yml ps
docker-compose -f deploy/docker-compose.yml logs --tail=30 pie-worker
```

Expected:

- Title contains `PIE Dashboard`
- Both services show `Up (healthy)`

## Stop

```bash
docker-compose -f deploy/docker-compose.yml down
```
