#!/usr/bin/env bash
set -euo pipefail

BASE="http://127.0.0.1:8000"
KEY="${ENTERPRISE_ADMIN_KEY:-test_admin_key_123}"

pretty() { python3 -m json.tool || cat; }

echo "🚀 COMPLETE PASSENGER IMPACT ENGINE TEST"
echo "========================================"
echo

echo "1) Root"
curl -sS "$BASE/" | pretty
echo

echo "2) Health"
curl -sS "$BASE/health" | pretty
echo

echo "3) Enterprise health"
curl -sS "$BASE/enterprise/health" -H "X-Admin-Key: $KEY" | pretty
echo

echo "4) Billing plans"
curl -sS "$BASE/billing/plans" | pretty
echo

echo "5) Create company (FORM)"
NAME="Demo Airline $(date +%s)"
COMPANY_JSON=$(curl -sS -X POST "$BASE/enterprise/companies" \
  -H "X-Admin-Key: $KEY" \
  -F "legal_name=$NAME" \
  -F "trading_name=DemoAir" \
  -F "tier=mid" \
  -F "industry=airline" \
  -F "country=US")

echo "$COMPANY_JSON" | pretty
COMPANY_ID=$(python3 - <<PY
import json
obj=json.loads('''$COMPANY_JSON''')
print(obj["id"])
PY
)
echo "Company ID: $COMPANY_ID"
echo

echo "6) Create contract (FORM)"
curl -sS -X POST "$BASE/enterprise/companies/$COMPANY_ID/contracts" \
  -H "X-Admin-Key: $KEY" \
  -F "plan=starter" \
  -F "starts_at=$(date +%Y-%m-%d)" | pretty
echo

echo "7) Create Stripe checkout session (JSON)"
curl -sS -X POST "$BASE/billing/create-checkout-session" \
  -H "Content-Type: application/json" \
  -d "{\"plan\":\"starter\",\"company_id\":\"$COMPANY_ID\",\"success_url\":\"http://localhost:8000/success\",\"cancel_url\":\"http://localhost:8000/cancel\"}" | pretty
echo

echo "✅ DONE"
