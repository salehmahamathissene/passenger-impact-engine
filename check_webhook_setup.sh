#!/bin/bash
echo "🪝 WEBHOOK CONFIGURATION CHECK"
echo "=============================="

source .env.working

echo ""
echo "1️⃣ Current Webhook Secret:"
WEBHOOK_SECRET=$(echo "$STRIPE_WEBHOOK_SECRET" | head -c 20)
echo "   Secret: ${WEBHOOK_SECRET}..."
echo "   Length: ${#STRIPE_WEBHOOK_SECRET} characters"

if [ "$STRIPE_WEBHOOK_SECRET" = "whsec_REDACTED_FROM_DASHBOARD" ] || [ -z "$STRIPE_WEBHOOK_SECRET" ]; then
    echo "   ⚠️  NOT configured - using placeholder"
else
    echo "   ✅ Configured"
fi

echo ""
echo "2️⃣ Webhook Endpoint Test:"
echo "Testing webhook endpoint..."
curl -s -X POST "http://127.0.0.1:8080/enterprise/billing/webhook" \
  -H "Content-Type: application/json" \
  -H "Stripe-Signature: test" \
  -d '{"type": "test", "data": {"object": {"id": "test_123"}}}' | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print('   Response:', data)
except:
    print('   Raw:', sys.stdin.read())
"

echo ""
echo "3️⃣ Required Webhook Events:"
echo "For complete billing, enable these events in Stripe Dashboard:"
echo ""
echo "   • checkout.session.completed"
echo "   • customer.subscription.created"
echo "   • customer.subscription.updated"
echo "   • customer.subscription.deleted"
echo "   • invoice.payment_succeeded"
echo "   • invoice.payment_failed"
echo ""
echo "4️⃣ How to Set Up Webhooks:"
echo "=========================="
echo "1. Go to: https://dashboard.stripe.com/test/webhooks"
echo "2. Click 'Add endpoint'"
echo "3. Enter URL: http://127.0.0.1:8080/enterprise/billing/webhook"
echo "4. Select events (or 'Select all events')"
echo "5. Copy the 'Signing secret'"
echo "6. Update .env.working:"
echo "   export STRIPE_WEBHOOK_SECRET='whsec_...'"
echo "7. Restart server"
echo ""
echo "5️⃣ Without Webhooks:"
echo "===================="
echo "If you can't set up webhooks now, you can:"
echo "1. Complete payment in browser"
echo "2. Manually update database:"
echo ""
echo "   UPDATE enterprise_companies SET"
echo "     plan = 'pro',"
echo "     is_active = true,"
echo "     stripe_subscription_id = 'sub_[id_from_stripe]',"
echo "     current_period_end = NOW() + INTERVAL '30 days'"
echo "   WHERE id = '$COMPANY_ID';"
