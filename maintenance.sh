#!/bin/bash
echo "🔧 PIE MAINTENANCE"
echo "================="

# 1. Check disk space
echo "1. Disk space:"
df -h / | tail -1

# 2. Check PostgreSQL
echo ""
echo "2. PostgreSQL:"
sudo -u postgres psql -d pie -c "
SELECT 
    schemaname, 
    tablename, 
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname NOT IN ('pg_catalog', 'information_schema') 
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"

# 3. Check Redis
echo ""
echo "3. Redis:"
redis-cli info memory | grep used_memory_human

# 4. Check running processes
echo ""
echo "4. Running processes:"
ps aux | grep -E "(worker_run|uvicorn)" | grep -v grep

# 5. Recent logs
echo ""
echo "5. Recent API logs:"
journalctl --user -u pie-api.service -n 5 --no-pager | tail -5

# 6. Order statistics
echo ""
echo "6. Order statistics:"
./pie_cli.py status 2>/dev/null || echo "CLI not available"
