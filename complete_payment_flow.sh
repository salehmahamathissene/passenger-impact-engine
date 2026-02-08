#!/bin/bash
echo "💰 COMPLETE PAYMENT FLOW TEST"
echo "============================="

source .env.working

echo ""
echo "1️⃣ Get Checkout URL:"
echo "==================="

if [ -f "/tmp/production_checkout/url.txt" ]; then
    CHECKOUT_URL=$(cat /tmp/production_checkout/url.txt)
    echo "Checkout URL found:"
    echo "$CHECKOUT_URL"
else
    echo "Creating new checkout session..."
    
    RESPONSE=$(curl -s -X POST "http://127.0.0.1:8080/enterprise/billing/checkout" \
      -H "Content-Type: application/json" \
      -H "X-Company-Id: $COMPANY_ID" \
      -H "X-Api-Key: $API_KEY" \
      -d '{"price_id": "'"$STRIPE_PRICE_PRO_MONTHLY"'"}')
    
    CHECKOUT_URL=$(echo "$RESPONSE" | python3 -c "import json, sys; data=json.load(sys.stdin); print(data.get('url', ''))")
    
    if [ -n "$CHECKOUT_URL" ]; then
        echo "Checkout URL:"
        echo "$CHECKOUT_URL"
        
        # Save it
        mkdir -p /tmp/production_checkout
        echo "$CHECKOUT_URL" > /tmp/production_checkout/url.txt
    else
        echo "❌ Failed to get checkout URL"
        exit 1
    fi
fi

echo ""
echo "2️⃣ Payment Instructions:"
echo "========================"
echo ""
echo "A. OPEN this URL in your browser:"
echo "   $CHECKOUT_URL"
echo ""
echo "B. USE these test card details:"
echo "   • Card number: 4242 4242 4242 4242"
echo "   • Expiry: Any future date (e.g., 12/34)"
echo "   • CVC: Any 3 digits (e.g., 123)"
echo "   • ZIP: Any 5 digits (e.g., 12345)"
echo ""
echo "C. CLICK 'Pay' to complete the payment"
echo ""
echo "3️⃣ After Payment Verification:"
echo "=============================="
echo ""
echo "Run this command to check subscription status:"
echo ""
echo "curl -s 'http://127.0.0.1:8080/enterprise/billing/subscription' \\"
echo "  -H 'X-Company-Id: $COMPANY_ID' \\"
echo "  -H 'X-Api-Key: $API_KEY'"
echo ""
echo "Expected result after successful payment:"
echo "  • plan: 'pro'"
echo "  • active: true"
echo "  • stripe_customer_id: (should be set)"
echo "  • stripe_subscription_id: (should be set)"
echo ""
echo "4️⃣ Webhook Configuration (IMPORTANT):"
echo "===================================="
echo ""
echo "For production, you need to set up Stripe webhooks:"
echo "1. Go to: https://dashboard.stripe.com/test/webhooks"
echo "2. Add endpoint: http://127.0.0.1:8080/enterprise/billing/webhook"
echo "3. Copy the 'Signing secret'"
echo "4. Update .env.working:"
echo "   export STRIPE_WEBHOOK_SECRET='whsec_...'"
echo ""
echo "Without webhooks, subscription won't update automatically."
echo "You can manually update the database:"
echo ""
cat > /tmp/manual_update.sql <<'SQL'
-- After payment, run this SQL to update subscription:
UPDATE enterprise_companies 
SET plan = 'pro',
    is_active = true,
    stripe_subscription_id = 'sub_mock_paid',
    current_period_end = NOW() + INTERVAL '30 days'
WHERE id = '$COMPANY_ID';
SQL

echo "Manual update SQL saved to: /tmp/manual_update.sql"
