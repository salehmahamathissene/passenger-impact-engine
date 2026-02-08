#!/bin/bash
echo "🔍 Checking after payment..."
echo "============================"

# Wait a moment for webhook processing
sleep 5

echo ""
echo "1. Checking subscription status:"
curl -s "http://127.0.0.1:8080/enterprise/billing/subscription" \
  -H "X-Company-Id: $COMPANY_ID" \
  -H "X-Api-Key: $API_KEY" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(f'   Status: {data.get(\"status\", \"unknown\")}')
    print(f'   Plan: {data.get(\"plan\", \"unknown\")}')
    print(f'   Active: {data.get(\"active\", False)}')
    if data.get('status') == 'active':
        print('   🎉 Subscription is active!')
    else:
        print('   ⏳ Subscription not active yet')
except:
    print('   Could not read subscription')
"

echo ""
echo "2. Creating a test page with the checkout link..."
cat > /tmp/test_payment.html <<HTML
<!DOCTYPE html>
<html>
<head>
    <title>Test Stripe Payment</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .container { background: #f5f5f5; padding: 20px; border-radius: 10px; }
        .card { background: white; padding: 15px; border-radius: 5px; margin: 10px 0; }
        button { background: #0066cc; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; }
        button:hover { background: #0055aa; }
    </style>
</head>
<body>
    <h1>💰 Test Stripe Payment</h1>
    
    <div class="container">
        <h2>Test Card Details</h2>
        <div class="card">
            <p><strong>Card Number:</strong> 4242 4242 4242 4242</p>
            <p><strong>Expiration:</strong> Any future date (e.g., 12/34)</p>
            <p><strong>CVC:</strong> Any 3 digits (e.g., 123)</p>
            <p><strong>ZIP:</strong> Any 5 digits (e.g., 12345)</p>
        </div>
        
        <h2>Checkout</h2>
        <button onclick="window.open('https://checkout.stripe.com/c/pay/cs_test_a1NLKcOV0EnlNvzOCAxkLHYEWztodFBvS4eE8Asc3MPConKYsybdAbVNQ2', '_blank')">
            Open Checkout Page
        </button>
        
        <h2>After Payment</h2>
        <p>After completing payment, run:</p>
        <pre>
curl -s "http://127.0.0.1:8080/enterprise/billing/subscription" \
  -H "X-Company-Id: \$COMPANY_ID" \
  -H "X-Api-Key: \$API_KEY" | jq .
        </pre>
    </div>
</body>
</html>
HTML

echo "   Test page created: /tmp/test_payment.html"
echo "   Open with: xdg-open /tmp/test_payment.html"
