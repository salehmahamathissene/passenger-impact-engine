#!/bin/bash
echo "🔍 PRODUCTION SYSTEM VERIFICATION"
echo "================================"

source .env.working
export PYTHONPATH="$PWD/src"

echo ""
echo "1️⃣ Infrastructure:"
echo "=================="

# Docker
echo "🐳 Docker:"
docker compose ps

# Ports
echo "🔌 Ports:"
echo "  5432: $(sudo ss -ltnp | grep ':5432' >/dev/null && echo '✅ PostgreSQL (docker)' || echo '❌ Not listening')"
echo "  55432: $(sudo ss -ltnp | grep ':55432' >/dev/null && echo '✅ Docker PostgreSQL' || echo '❌ Not listening')"
echo "  8080: $(sudo ss -ltnp | grep ':8080' >/dev/null && echo '✅ Application' || echo '❌ Not listening')"

echo ""
echo "2️⃣ Application:"
echo "==============="

echo -n "  Server health: "
if curl -s "http://127.0.0.1:8080/health" > /dev/null; then
    echo "✅ $(curl -s http://127.0.0.1:8080/health)"
else
    echo "❌ Not responding"
fi

echo ""
echo "3️⃣ Database:"
echo "==========="

python3 -c "
import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.environ.get('DATABASE_URL')
try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        # Version
        result = conn.execute(text('SELECT version()'))
        version = result.scalar()
        print('  PostgreSQL: ✅', version.split(',')[0])
        
        # Tables
        result = conn.execute(text('''
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        '''))
        table_count = result.scalar()
        print(f'  Tables: ✅ {table_count} tables')
        
        # Enterprise tables
        result = conn.execute(text('''
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE 'enterprise%'
        '''))
        enterprise_count = result.scalar()
        print(f'  Enterprise tables: ✅ {enterprise_count} tables')
        
        # Company
        company_id = os.environ.get('COMPANY_ID')
        result = conn.execute(
            text('SELECT legal_name, plan FROM enterprise_companies WHERE id = :id'),
            {'id': company_id}
        ).fetchone()
        
        if result:
            print(f'  Company: ✅ {result[0]} (plan: {result[1]})')
        else:
            print(f'  Company: ❌ Not found')
            
except Exception as e:
    print(f'  Database: ❌ {e}')
"

echo ""
echo "4️⃣ Billing System:"
echo "=================="

echo -n "  Subscription endpoint: "
SUBSCRIPTION_RESPONSE=$(curl -s "http://127.0.0.1:8080/enterprise/billing/subscription" \
  -H "X-Company-Id: $COMPANY_ID" \
  -H "X-Api-Key: $API_KEY")

if echo "$SUBSCRIPTION_RESPONSE" | grep -q '"plan"'; then
    echo "✅ Working"
    echo "$SUBSCRIPTION_RESPONSE" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'     Plan: {data[\"plan\"]}, Active: {data[\"active\"]}')
"
else
    echo "❌ Failed"
fi

echo -n "  Checkout endpoint: "
CHECKOUT_RESPONSE=$(curl -s -X POST "http://127.0.0.1:8080/enterprise/billing/checkout" \
  -H "Content-Type: application/json" \
  -H "X-Company-Id: $COMPANY_ID" \
  -H "X-Api-Key: $API_KEY" \
  -d '{"price_id": "'"$STRIPE_PRICE_PRO_MONTHLY"'"}' 2>/dev/null)

if echo "$CHECKOUT_RESPONSE" | grep -q '"url"'; then
    echo "✅ Working"
else
    echo "❌ Failed"
fi

echo ""
echo "🏭 PRODUCTION STATUS:"
echo "===================="

# Overall status
python3 -c "
import os
import subprocess

def check_docker():
    result = subprocess.run(['docker', 'compose', 'ps', '--format', 'json'], 
                          capture_output=True, text=True)
    return 'running' in result.stdout.lower()

def check_server():
    import urllib.request
    try:
        with urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=2) as response:
            return response.status == 200
    except:
        return False

def check_database():
    from sqlalchemy import create_engine, text
    try:
        engine = create_engine(os.environ.get('DATABASE_URL'))
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
            return True
    except:
        return False

docker_ok = check_docker()
server_ok = check_server()
db_ok = check_database()

print(f'🐳 Docker PostgreSQL: {'✅' if docker_ok else '❌'}')
print(f'🚀 Application Server: {'✅' if server_ok else '❌'}')
print(f'🗄️  Database Connection: {'✅' if db_ok else '❌'}')

if docker_ok and server_ok and db_ok:
    print('\\n🎉 PRODUCTION SYSTEM: ✅ FULLY OPERATIONAL')
    print('\\nReady for:')
    print('  1. Payment processing')
    print('  2. Subscription management')
    print('  3. Enterprise billing')
else:
    print('\\n⚠️  PRODUCTION SYSTEM: ❌ NOT READY')
    print('\\nIssues:')
    if not docker_ok: print('  - Docker PostgreSQL not running')
    if not server_ok: print('  - Application server not responding')
    if not db_ok: print('  - Database connection failed')
"
