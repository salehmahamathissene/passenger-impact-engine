#!/usr/bin/env bash
set -euo pipefail

BASE_URL="http://127.0.0.1:8000"
ADMIN_KEY="test_admin_key_123"
H=(-H "X-Admin-Key: $ADMIN_KEY" -H "Content-Type: application/json")

echo "1) Create"
CREATE=$(curl -sS -X POST "$BASE_URL/enterprise/companies" "${H[@]}" -d '{
  "legal_name":"Test CRUD Airlines 1770485716",
  "trading_name":"CRUDAir",
  "tier":"mid",
  "industry":"airline",
  "country":"US",
  "employee_count":150
}')
echo "$CREATE" | python -m json.tool

ID=$(echo "$CREATE" | python - <<'PY'
import sys, json
print(json.load(sys.stdin)["id"])
PY
)

echo "2) Get"
curl -sS "$BASE_URL/enterprise/companies/$ID" -H "X-Admin-Key: $ADMIN_KEY" | python -m json.tool

echo "3) Update"
curl -sS -X PUT "$BASE_URL/enterprise/companies/$ID" "${H[@]}" -d '{
  "trading_name":"UpdatedCRUDAir",
  "employee_count":500
}' | python -m json.tool

echo "4) Delete"
curl -sS -X DELETE "$BASE_URL/enterprise/companies/$ID" -H "X-Admin-Key: $ADMIN_KEY" | python -m json.tool

echo "5) Verify 404"
curl -sS -o /dev/null -w "HTTP %{http_code}\n" \
  "$BASE_URL/enterprise/companies/$ID" -H "X-Admin-Key: $ADMIN_KEY"
