#!/bin/bash
echo "🧪 TESTING PASSENGER IMPACT ENGINE WITH BILLING"
echo "==============================================="

BASE="http://127.0.0.1:8000"
KEY="test_admin_key_123"

# 1. Check root endpoint
echo -e "\n1. Root endpoint:"
curl -s "$BASE/" | python -m json.tool

# 2. Check health
echo -e "\n2. Health check:"
curl -s "$BASE/health" | python -m json.tool

# 3. Check billing plans
echo -e "\n3. Billing plans:"
curl -s "$BASE/billing/plans" | python -m json.tool

# 4. Create a test company
echo -e "\n4. Creating test company:"
COMPANY_RESPONSE=$(curl -s -X POST "$BASE/enterprise/companies" \
  -H "X-Admin-Key: $KEY" \
  -F "legal_name=Test Airline $(date +%s)" \
  -F "tier=mid" \
  -F "industry=airline" \
  -F "country=US")
echo "$COMPANY_RESPONSE" | python -m json.tool

# Extract company ID
COMPANY_ID=$(echo "$COMPANY_RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "Company ID: $COMPANY_ID"

# 5. Create a contract
echo -e "\n5. Creating contract:"
CONTRACT_RESPONSE=$(curl -s -X POST "$BASE/enterprise/companies/$COMPANY_ID/contracts" \
  -H "X-Admin-KEY: $KEY" \
  -H "Content-Type: application/json" \
  -d '{"plan": "starter", "starts_at": "2024-01-01"}')
echo "$CONTRACT_RESPONSE" | python -m json.tool

# 6. List companies
echo -e "\n6. Listing all companies:"
curl -s "$BASE/enterprise/companies" -H "X-Admin-Key: $KEY" | python -m json.tool

# 7. Create a checkout session (requires Stripe test keys)
echo -e "\n7. Creating checkout session (test):"
CHECKOUT_RESPONSE=$(curl -s -X POST "$BASE/billing/create-checkout-session" \
  -H "Content-Type: application/json" \
  -d "{\"plan\": \"starter\", \"company_id\": \"$COMPANY_ID\"}")
echo "$CHECKOUT_RESPONSE" | python -m json.tool

echo -e "\n✅ TEST COMPLETE!"
echo "To generate revenue, you need to:"
echo "1. Get Stripe API keys from https://dashboard.stripe.com/test/apikeys"
echo "2. Update STRIPE_SECRET_KEY and STRIPE_WEBHOOK_SECRET in .env"
echo "3. Create products in Stripe dashboard"
echo "4. Deploy: ./deploy_to_production.sh"
