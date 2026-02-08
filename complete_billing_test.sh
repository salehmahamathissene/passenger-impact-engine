#!/bin/bash
echo "🚀 Complete Billing System Test"
echo "==============================="

# Load environment
source .env.working 2>/dev/null || echo "⚠️  .env.working not found"

echo ""
echo "1️⃣ Testing Stripe Configuration"
echo "================================"

# Test Stripe key
python3 - <<'PY'
import os
import stripe

stripe_key = os.environ.get("STRIPE_SECRET_KEY", "")
price_id = os.environ.get("STRIPE_PRICE_PRO_MONTHLY", "")

print(f"Stripe Key: {'✅ Set' if stripe_key else '❌ Not set'}")
print(f"Price ID: {'✅ Set' if price_id else '❌ Not set'}")

if stripe_key:
    stripe.api_key = stripe_key
    try:
        # Test key
        customer = stripe.Customer.list(limit=1)
        print("✅ Stripe API key is valid")
        
        # Test price
        if price_id:
            try:
                price = stripe.Price.retrieve(price_id)
                print(f"✅ Price exists: ${price.unit_amount/100:.2f} {price.currency}")
            except:
                print(f"❌ Price {price_id} not found")
    except:
        print("❌ Stripe API key is invalid")
PY

echo ""
echo "2️⃣ Testing Authentication"
echo "=========================="

# Test with current credentials
curl -s "http://127.0.0.1:8080/enterprise/billing/subscription" \
  -H "X-Company-Id: $COMPANY_ID" \
  -H "X-Api-Key: $API_KEY" \
  -w "Status: %{http_code}\n" -o /tmp/sub_test.txt > /dev/null

echo "Billing subscription endpoint: $(tail -1 /tmp/sub_test.txt)"

echo ""
echo "3️⃣ Creating Checkout Session"
echo "============================="

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
        print('✅ Checkout session created!')
        print('')
        print('🔗 Checkout URL:')
        print(data['checkout_url'])
        print('')
        print('📋 Session ID:', data['session_id'])
        print('👤 Customer ID:', data.get('customer_id', 'N/A'))
        
        # Save URL to file
        with open('/tmp/latest_checkout.txt', 'w') as f:
            f.write(data['checkout_url'])
    else:
        print('❌ Failed to create checkout')
        print(data)
except Exception as e:
    print('❌ Error:', e)
"

echo ""
echo "4️⃣ Next Steps"
echo "============="
echo "1. Visit the checkout URL above"
echo "2. Use test card: 4242 4242 4242 4242"
echo "3. Complete the payment"
echo "4. Check subscription status:"
echo '   curl -s "http://127.0.0.1:8080/enterprise/billing/subscription" \'
echo '     -H "X-Company-Id: $COMPANY_ID" \'
echo '     -H "X-Api-Key: $API_KEY" | jq .'
echo ""
echo "💰 Test card details:"
echo "   • Number: 4242 4242 4242 4242"
echo "   • Expiry: Any future date"
echo "   • CVC: Any 3 digits"
echo "   • ZIP: Any 5 digits"
