#!/bin/bash
echo "🔄 TESTING COMPLETE PAYMENT FLOW"
echo "================================"

# 1. Create checkout session
echo ""
echo "1️⃣ Creating checkout session..."
RESPONSE=$(curl -s -X POST "http://127.0.0.1:8080/enterprise/billing/checkout" \
  -H "Content-Type: application/json" \
  -H "X-Company-Id: $COMPANY_ID" \
  -H "X-Api-Key: $API_KEY" \
  -d '{"price_id": "'"$STRIPE_PRICE_PRO_MONTHLY"'"}')

echo "$RESPONSE" | python3 -c "
import json, sys
data = json.load(sys.stdin)
url = data.get('url') or data.get('checkout_url')
print('✅ Checkout URL:', url)
print('👤 Customer ID:', data.get('customer_id'))
print('📝 Session ID:', data.get('session_id'))
"

# 2. Check subscription status
echo ""
echo "2️⃣ Checking subscription status..."
curl -s "http://127.0.0.1:8080/enterprise/billing/subscription" \
  -H "X-Company-Id: $COMPANY_ID" \
  -H "X-Api-Key: $API_KEY" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print('Current subscription:')
print('  Plan:', data.get('plan'))
print('  Status:', data.get('status'))
print('  Stripe Customer ID:', data.get('stripe_customer_id'))
"

# 3. Check invoice count
echo ""
echo "3️⃣ Checking invoices..."
INVOICE_COUNT=$(curl -s "http://127.0.0.1:8080/enterprise/invoices" \
  -H "X-Company-Id: $COMPANY_ID" \
  -H "X-Api-Key: $API_KEY" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print('📊 Invoice count:', len(data.get('items', [])))
")

