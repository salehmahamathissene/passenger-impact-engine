#!/bin/bash
echo "🧪 TESTING REAL BILLING SYSTEM"
echo "==============================="

source .env.working

echo "1. Testing authentication..."
curl -s -H "X-Company-Id: $COMPANY_ID" -H "X-Api-Key: $API_SECRET" \
  http://127.0.0.1:8080/enterprise/billing/subscription | python3 -m json.tool

echo ""
echo "2. Testing health..."
curl -s http://127.0.0.1:8080/health

echo ""
echo ""
echo "3. Testing checkout session creation..."
curl -s -X POST \
  -H "X-Company-Id: $COMPANY_ID" \
  -H "X-Api-Key: $API_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"plan": "pro"}' \
  http://127.0.0.1:8080/enterprise/billing/checkout | python3 -m json.tool

echo ""
echo "4. Testing invoices..."
curl -s -H "X-Company-Id: $COMPANY_ID" -H "X-Api-Key: $API_SECRET" \
  http://127.0.0.1:8080/enterprise/billing/invoices | python3 -m json.tool

echo ""
echo "5. Testing success endpoint..."
curl -s http://127.0.0.1:8080/enterprise/billing/success

echo ""
echo ""
echo "🎯 REAL SYSTEM STATUS:"
echo "====================="

# Check if endpoints exist
echo -n "✅ /health: "
curl -s http://127.0.0.1:8080/health | grep -q healthy && echo "WORKING" || echo "FAILED"

echo -n "✅ /enterprise/billing/subscription: "
curl -s -H "X-Company-Id: $COMPANY_ID" -H "X-Api-Key: $API_SECRET" \
  http://127.0.0.1:8080/enterprise/billing/subscription | grep -q "plan" && echo "WORKING" || echo "FAILED"

echo -n "✅ /enterprise/billing/checkout: "
curl -s -X POST -H "X-Company-Id: $COMPANY_ID" -H "X-Api-Key: $API_SECRET" \
  -H "Content-Type: application/json" -d '{"plan":"pro"}' \
  http://127.0.0.1:8080/enterprise/billing/checkout | grep -q "session_id" && echo "WORKING" || echo "FAILED"

echo ""
echo "💡 NEXT STEPS:"
echo "1. Use the checkout URL with test card: 4242 4242 4242 4242"
echo "2. Set up Stripe webhooks for automatic updates"
echo "3. Monitor database for subscription changes"
