#!/bin/bash
echo "🚀 Complete Billing Setup"
echo "========================"

echo ""
echo "1️⃣ Checking prerequisites..."
echo "==========================="

# Check if server is running
if ! curl -s "http://127.0.0.1:8080/health" > /dev/null; then
    echo "❌ Server not running on port 8080"
    echo "   Start with: uvicorn pie.api.app:app --host 127.0.0.1 --port 8080"
    exit 1
fi
echo "✅ Server is running"

# Check credentials
if [ -z "$COMPANY_ID" ] || [ -z "$API_KEY" ]; then
    echo "❌ COMPANY_ID or API_KEY not set"
    echo "   Use: source .env.working"
    exit 1
fi
echo "✅ Credentials set"

# Test authentication
echo ""
echo "2️⃣ Testing authentication..."
echo "============================"
AUTH_TEST=$(curl -s "http://127.0.0.1:8080/enterprise/invoices" \
  -H "X-Company-Id: $COMPANY_ID" \
  -H "X-Api-Key: $API_KEY" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if 'items' in data:
        print(f'SUCCESS:{len(data[\"items\"])}')
    else:
        print('FAILED:Invalid response')
except:
    print('FAILED:Auth failed')
")

if [[ "$AUTH_TEST" == SUCCESS* ]]; then
    INVOICE_COUNT=${AUTH_TEST#SUCCESS:}
    echo "✅ Authentication successful ($INVOICE_COUNT invoices found)"
else
    echo "❌ Authentication failed: ${AUTH_TEST#FAILED:}"
    exit 1
fi

echo ""
echo "3️⃣ Checking Stripe configuration..."
echo "==================================="

if [ -z "$STRIPE_SECRET_KEY" ]; then
    echo "❌ STRIPE_SECRET_KEY not set"
    exit 1
fi

if [[ "$STRIPE_SECRET_KEY" == *"REPLACE"* ]] || [[ "$STRIPE_SECRET_KEY" == *"changeme"* ]]; then
    echo "❌ STRIPE_SECRET_KEY appears to be a placeholder"
    echo "   Update .env.working with your real Stripe key"
    exit 1
fi
echo "✅ Stripe key looks valid"

if [ -z "$STRIPE_PRICE_PRO_MONTHLY" ]; then
    echo "❌ STRIPE_PRICE_PRO_MONTHLY not set"
    echo "   Create a price in Stripe Dashboard and update .env.working"
    exit 1
fi

if [[ "$STRIPE_PRICE_PRO_MONTHLY" == *"REPLACE"* ]] || [[ "$STRIPE_PRICE_PRO_MONTHLY" == *"test_"* ]]; then
    echo "⚠️  STRIPE_PRICE_PRO_MONTHLY appears to be a test placeholder"
    echo "   You need a real price ID from Stripe"
    echo ""
    echo "   To create one:"
    echo "   1. Go to https://dashboard.stripe.com/test/products"
    echo "   2. Create product → Add price ($99/month)"
    echo "   3. Copy the Price ID (looks like price_1Qb...)"
    echo "   4. Update .env.working"
    echo ""
    read -p "Continue with test price? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "4️⃣ Testing billing endpoint..."
echo "=============================="

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
        print('✅ Billing endpoint works!')
        print('')
        print('🎉 SETUP COMPLETE!')
        print('')
        print('📋 Next steps:')
        print('   1. Visit checkout URL to test payment')
        print('   2. Use test card: 4242 4242 4242 4242')
        print('   3. Complete payment to activate subscription')
        print('')
        print(f'🔗 Checkout URL: {data[\"checkout_url\"]}')
    elif 'detail' in data:
        error = data['detail']
        print(f'❌ Error: {error}')
        if 'No such price' in error:
            print('   Your price ID is invalid')
            print('   Create a real price in Stripe Dashboard')
        elif 'Stripe error' in error:
            print('   Stripe API error - check your key and permissions')
    else:
        print(f'⚠️  Unexpected: {data}')
except Exception as e:
    print(f'❌ Parse error: {e}')
    print(f'Raw: {sys.stdin.read()}')
"

echo ""
echo "5️⃣ Additional tests..."
echo "======================"

echo "Testing subscription endpoint:"
curl -s "http://127.0.0.1:8080/enterprise/billing/subscription" \
  -H "X-Company-Id: $COMPANY_ID" \
  -H "X-Api-Key: $API_KEY" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(f'   Status: {data.get(\"status\", \"unknown\")}')
    print(f'   Plan: {data.get(\"plan\", \"unknown\")}')
    print(f'   Active: {data.get(\"active\", False)}')
except:
    print('   Could not read subscription')
"
