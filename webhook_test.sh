#!/bin/bash
echo "🪝 TESTING WEBHOOK ENDPOINT"
echo "==========================="

# Test webhook endpoint exists
curl -s -X POST "http://127.0.0.1:8080/enterprise/billing/webhook" \
  -H "Content-Type: application/json" \
  -d '{"type": "test", "data": {"object": {"id": "test_123"}}}'

echo ""
echo "Webhook endpoint status: $?"

# Check if webhook secret is set
if [ -z "$STRIPE_WEBHOOK_SECRET" ]; then
  echo "❌ STRIPE_WEBHOOK_SECRET not set!"
  echo "   Get it from: Stripe Dashboard -> Developers -> Webhooks"
else
  echo "✅ Webhook secret is set"
fi
