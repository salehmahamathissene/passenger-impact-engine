#!/bin/bash
echo "🚀 RESTARTING SERVER WITH PROPER CONFIG"
echo "======================================="

# Kill existing server
pkill -f "uvicorn.*127.0.0.1.*8080" || true

# Source environment
source .env.working
export PYTHONPATH="$PWD/src"

echo "Environment:"
echo "  DATABASE_URL: ${DATABASE_URL:0:60}..."
echo "  COMPANY_ID: $COMPANY_ID"
echo "  API_KEY: ${API_KEY:0:10}..."
echo ""

# Start server with proper settings
echo "Starting uvicorn with production settings..."
uvicorn pie.api.app:app \
  --host 127.0.0.1 \
  --port 8080 \
  --workers 1 \
  --no-access-log \
  --log-level warning \
  > /tmp/server_proper.log 2>&1 &
SERVER_PID=$!

echo "Server PID: $SERVER_PID"
sleep 3

echo ""
echo "📊 Server status:"
if curl -s "http://127.0.0.1:8080/health" > /dev/null; then
    echo "✅ Server is running"
    echo "   Response: $(curl -s http://127.0.0.1:8080/health)"
else
    echo "❌ Server failed to start"
    echo "Last 10 lines of log:"
    tail -n 10 /tmp/server_proper.log
    exit 1
fi

echo ""
echo "🧪 Testing authentication..."
echo "============================="

# Test invoices endpoint (should work now)
echo "Testing /enterprise/invoices endpoint:"
INVOICE_RESPONSE=$(curl -s -i "http://127.0.0.1:8080/enterprise/invoices" \
  -H "X-Company-Id: $COMPANY_ID" \
  -H "X-Api-Key: $API_KEY")

STATUS_CODE=$(echo "$INVOICE_RESPONSE" | head -1 | cut -d' ' -f2)
echo "Status Code: $STATUS_CODE"

if [ "$STATUS_CODE" = "200" ]; then
    echo "✅ Authentication successful!"
    echo "Response body:"
    echo "$INVOICE_RESPONSE" | tail -1 | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if 'items' in data:
        print(f'   Found {len(data[\"items\"])} invoices')
    else:
        print('   Response:', data)
except:
    print('   Raw:', sys.stdin.read())
"
elif [ "$STATUS_CODE" = "401" ]; then
    echo "❌ Authentication failed"
    echo "Response:"
    echo "$INVOICE_RESPONSE" | tail -1
else
    echo "⚠️  Unexpected status: $STATUS_CODE"
fi

echo ""
echo "🧪 Testing billing endpoints..."
echo "==============================="

# Test subscription endpoint
echo "Testing /enterprise/billing/subscription:"
SUBSCRIPTION_RESPONSE=$(curl -s "http://127.0.0.1:8080/enterprise/billing/subscription" \
  -H "X-Company-Id: $COMPANY_ID" \
  -H "X-Api-Key: $API_KEY")

echo "$SUBSCRIPTION_RESPONSE" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print('   Plan:', data.get('plan'))
    print('   Active:', data.get('active'))
    print('   Status:', data.get('status'))
    print('   Stripe Customer ID:', data.get('stripe_customer_id'))
except Exception as e:
    print(f'   ❌ Error: {e}')
    print('   Raw:', sys.stdin.read())
"

# Test checkout endpoint
echo ""
echo "Testing /enterprise/billing/checkout (POST):"
CHECKOUT_RESPONSE=$(curl -s -X POST "http://127.0.0.1:8080/enterprise/billing/checkout" \
  -H "Content-Type: application/json" \
  -H "X-Company-Id: $COMPANY_ID" \
  -H "X-Api-Key: $API_KEY" \
  -d '{"price_id": "'"$STRIPE_PRICE_PRO_MONTHLY"'"}')

echo "$CHECKOUT_RESPONSE" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if 'url' in data:
        print('   ✅ Checkout endpoint working!')
        print(f'   URL: {data.get(\"url\", \"\")[:50]}...')
        print(f'   Customer ID: {data.get(\"customer_id\", \"N/A\")}')
        
        # Save URL
        with open('/tmp/checkout_pro_url.txt', 'w') as f:
            f.write(data.get('url', ''))
        print('   ✅ URL saved to /tmp/checkout_pro_url.txt')
    else:
        print('   ❌ No URL in response')
        print('   Response:', data)
except Exception as e:
    print(f'   ❌ Error: {e}')
    print('   Raw:', sys.stdin.read())
"

echo ""
echo "🎯 READY FOR PRODUCTION-LEVEL TESTING"
echo "===================================="
echo ""
echo "To test complete payment flow:"
echo "1. cat /tmp/checkout_pro_url.txt"
echo "2. Open URL in browser"
echo "3. Use test card: 4242 4242 4242 4242"
echo "4. Verify subscription updates"
echo ""
echo "📊 Monitor logs: tail -f /tmp/server_proper.log"
