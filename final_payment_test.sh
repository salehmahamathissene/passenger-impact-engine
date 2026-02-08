#!/bin/bash
echo "🎯 FINAL PAYMENT TEST"
echo "===================="

echo ""
echo "1️⃣ Creating new checkout session..."
echo "==================================="

RESPONSE=$(curl -s -X POST "http://127.0.0.1:8080/enterprise/billing/checkout" \
  -H "Content-Type: application/json" \
  -H "X-Company-Id: $COMPANY_ID" \
  -H "X-Api-Key: $API_KEY" \
  -d '{"price_id": "'"$STRIPE_PRICE_PRO_MONTHLY"'"}')

echo "$RESPONSE" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if 'url' in data or 'checkout_url' in data:
        url = data.get('url') or data.get('checkout_url')
        print('✅ Checkout session created!')
        print('')
        print('🔗 CHECKOUT URL:')
        print(url)
        print('')
        print('👤 Customer ID:', data.get('customer_id', 'N/A'))
        print('💰 Price ID:', data.get('price_id', 'N/A'))
        
        # Save URL
        with open('/tmp/checkout_final.txt', 'w') as f:
            f.write(url)
            
        print('')
        print('📝 URL saved to /tmp/checkout_final.txt')
    else:
        print('❌ Response:', data)
except Exception as e:
    print('❌ Error:', e)
    print('Raw:', sys.stdin.read()[:200])
"

echo ""
echo "2️⃣ Payment Instructions"
echo "========================"
echo ""
echo "To complete the test:"
echo ""
echo "A. Open the checkout URL above in your browser"
echo "B. Use these test card details:"
echo "   • Card number: 4242 4242 4242 4242"
echo "   • Expiry: Any future date (e.g., 12/34)"
echo "   • CVC: Any 3 digits (e.g., 123)"
echo "   • ZIP: Any 5 digits (e.g., 12345)"
echo ""
echo "C. After payment, verify:"
echo '   curl -s "http://127.0.0.1:8080/enterprise/invoices" \'
echo '     -H "X-Company-Id: $COMPANY_ID" \'
echo '     -H "X-Api-Key: $API_KEY" | jq ".items | length"'
echo ""
echo "   (Should show 4 invoices instead of 3 after successful payment)"
