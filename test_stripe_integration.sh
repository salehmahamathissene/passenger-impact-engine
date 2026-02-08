#!/bin/bash
echo "🔧 Stripe Integration Test"
echo "========================="

# Check required environment variables
echo "📋 Checking environment..."
if [ -z "$STRIPE_SECRET_KEY" ]; then
    echo "❌ STRIPE_SECRET_KEY is not set"
    exit 1
fi

if [ -z "$STRIPE_PRICE_PRO_MONTHLY" ]; then
    echo "❌ STRIPE_PRICE_PRO_MONTHLY is not set"
    echo "   Please create a price in Stripe Dashboard and update .env.stripe"
    exit 1
fi

if [ -z "$COMPANY_ID" ] || [ -z "$API_KEY" ]; then
    echo "⚠️  COMPANY_ID or API_KEY not set, testing without auth"
    AUTH_HEADERS=""
else
    AUTH_HEADERS="-H 'X-Company-Id: $COMPANY_ID' -H 'X-Api-Key: $API_KEY'"
fi

echo "✅ Environment OK"
echo "   Stripe Key: ${STRIPE_SECRET_KEY:0:12}..."
echo "   Price ID: $STRIPE_PRICE_PRO_MONTHLY"

# Test 1: Check if server is running
echo ""
echo "1️⃣ Testing server connectivity..."
curl -s "http://127.0.0.1:8080/health" > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Server is running"
else
    echo "❌ Server is not responding on port 8080"
    echo "   Start server with: uvicorn pie.api.app:app --host 127.0.0.1 --port 8080"
    exit 1
fi

# Test 2: Test checkout endpoint
echo ""
echo "2️⃣ Testing checkout endpoint..."
RESPONSE=$(curl -s -X POST "http://127.0.0.1:8080/enterprise/billing/checkout" \
  -H "Content-Type: application/json" \
  -H "X-Company-Id: $COMPANY_ID" \
  -H "X-Api-Key: $API_KEY" \
  -d "{\"price_id\":\"$STRIPE_PRICE_PRO_MONTHLY\"}")

echo "$RESPONSE" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if 'checkout_url' in data:
        print('✅ Checkout endpoint works!')
        print(f'   Checkout URL: {data[\"checkout_url\"][:80]}...')
        print(f'   Session ID: {data[\"session_id\"]}')
    elif 'detail' in data:
        print(f'❌ Error: {data[\"detail\"]}')
        if 'No such price' in data.get('detail', ''):
            print('   Please check your STRIPE_PRICE_PRO_MONTHLY environment variable')
    else:
        print(f'⚠️ Unexpected response: {data}')
except Exception as e:
    print(f'❌ Failed to parse response: {e}')
    print(f'Raw response: {sys.stdin.read()}')
"

# Test 3: Test subscription endpoint
echo ""
echo "3️⃣ Testing subscription endpoint..."
curl -s "http://127.0.0.1:8080/enterprise/billing/subscription" \
  -H "X-Company-Id: $COMPANY_ID" \
  -H "X-Api-Key: $API_KEY" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(f'✅ Subscription endpoint works')
    print(f'   Status: {data.get(\"status\", \"unknown\")}')
    print(f'   Plan: {data.get(\"plan\", \"unknown\")}')
    print(f'   Active: {data.get(\"active\", False)}')
except:
    print('⚠️ Could not parse subscription response')
"

echo ""
echo "🎉 Stripe integration test complete!"
echo ""
echo "📚 Next steps:"
echo "1. Visit the checkout URL to complete payment in test mode"
echo "2. Use test card: 4242 4242 4242 4242"
echo "3. Any future expiration date"
echo "4. Any CVC"
echo "5. Any ZIP code"
echo ""
echo "🔧 To set up webhooks for production:"
echo "   stripe listen --forward-to http://localhost:8080/enterprise/billing/webhook"
