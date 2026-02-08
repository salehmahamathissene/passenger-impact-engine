#!/bin/bash
echo "🚀 RESTARTING SERVER WITH POSTGRESQL"
echo "===================================="

# Kill existing server
pkill -f "uvicorn.*127.0.0.1.*8080" || true

# Source environment
source .env.working
export PYTHONPATH="$PWD/src"

# Start server
echo "Starting server..."
uvicorn pie.api.app:app --host 127.0.0.1 --port 8080 > /tmp/server_postgres.log 2>&1 &
SERVER_PID=$!

echo "Server PID: $SERVER_PID"
sleep 3

echo ""
echo "📋 Server log (last 5 lines):"
tail -n 5 /tmp/server_postgres.log

echo ""
echo "🔍 Testing endpoints with PostgreSQL backend:"
echo ""

# Test 1: Health endpoint
echo "1️⃣ Health check:"
curl -s "http://127.0.0.1:8080/health"
echo ""

# Test 2: Subscription endpoint
echo "2️⃣ Subscription status:"
curl -s "http://127.0.0.1:8080/enterprise/billing/subscription" \
  -H "X-Company-Id: $COMPANY_ID" \
  -H "X-Api-Key: $API_KEY" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print('Response:')
for key in ['status', 'plan', 'active', 'stripe_customer_id']:
    print(f'  {key}: {data.get(key)}')
"

# Test 3: Create checkout session
echo ""
echo "3️⃣ Testing checkout creation:"
curl -s -X POST "http://127.0.0.1:8080/enterprise/billing/checkout" \
  -H "Content-Type: application/json" \
  -H "X-Company-Id: $COMPANY_ID" \
  -H "X-Api-Key: $API_KEY" \
  -d '{"price_id": "'"$STRIPE_PRICE_PRO_MONTHLY"'"}' | python3 -c "
import json, sys
data = json.load(sys.stdin)
print('Checkout created:')
print(f'  URL: {data.get(\"url\", \"N/A\")[:50]}...')
print(f'  Customer ID: {data.get(\"customer_id\", \"N/A\")}')
"

echo ""
echo "✅ Server running with PostgreSQL!"
echo "Log file: /tmp/server_postgres.log"
