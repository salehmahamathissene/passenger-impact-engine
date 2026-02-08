#!/bin/bash

set -e

echo "🔧 Setting up environment..."
export ENTERPRISE_ADMIN_KEY="test_admin_key_123"
export DATABASE_URL="postgresql://pie:piepass@127.0.0.1:55432/pie_enterprise"

BASE_URL="http://127.0.0.1:8000"
ADMIN_HEADER="X-Admin-Key: $ENTERPRISE_ADMIN_KEY"

echo ""
echo "📋 Testing Enterprise API Workflow"
echo "=================================="

echo ""
echo "1. Testing health endpoint..."
curl -s "$BASE_URL/enterprise/health" -H "$ADMIN_HEADER" | python -m json.tool
echo ""

echo "2. Creating a company..."
COMPANY_RESPONSE=$(curl -s -X POST "$BASE_URL/enterprise/companies" \
  -H "$ADMIN_HEADER" \
  -H "Content-Type: application/json" \
  -d '{
    "legal_name": "Global Airlines Inc",
    "trading_name": "GlobalAir",
    "tier": "large",
    "industry": "airline",
    "country": "US",
    "currency": "USD",
    "contact_email": "admin@globalair.com",
    "contact_phone": "+1-555-123-4567"
  }')

echo "$COMPANY_RESPONSE" | python -m json.tool
COMPANY_ID=$(echo "$COMPANY_RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "Created company with ID: $COMPANY_ID"
echo ""

echo "3. Creating a contact for the company..."
CONTACT_RESPONSE=$(curl -s -X POST "$BASE_URL/enterprise/companies/$COMPANY_ID/contacts" \
  -H "$ADMIN_HEADER" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Smith",
    "email": "john.smith@globalair.com",
    "phone": "+1-555-987-6543",
    "role": "operations_manager",
    "department": "operations"
  }')

echo "$CONTACT_RESPONSE" | python -m json.tool
CONTACT_ID=$(echo "$CONTACT_RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "Created contact with ID: $CONTACT_ID"
echo ""

echo "4. Creating a contract..."
CONTRACT_RESPONSE=$(curl -s -X POST "$BASE_URL/enterprise/contracts" \
  -H "$ADMIN_HEADER" \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "'"$COMPANY_ID"'",
    "contact_id": "'"$CONTACT_ID"'",
    "name": "Premium Impact Analysis Package",
    "type": "monthly_subscription",
    "status": "active",
    "billing_frequency": "monthly",
    "price_per_unit": 2999.99,
    "currency": "USD",
    "start_date": "2025-02-01",
    "end_date": "2026-02-01",
    "renewal_auto": true,
    "terms": "Standard enterprise terms apply",
    "notes": "Includes priority support and custom reporting"
  }')

echo "$CONTRACT_RESPONSE" | python -m json.tool
CONTRACT_ID=$(echo "$CONTRACT_RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "Created contract with ID: $CONTRACT_ID"
echo ""

echo "5. Listing all companies..."
curl -s "$BASE_URL/enterprise/companies" -H "$ADMIN_HEADER" | python -m json.tool | head -50
echo ""

echo "6. Creating an invoice..."
INVOICE_RESPONSE=$(curl -s -X POST "$BASE_URL/enterprise/invoices" \
  -H "$ADMIN_HEADER" \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "'"$COMPANY_ID"'",
    "contact_id": "'"$CONTACT_ID"'",
    "contract_id": "'"$CONTRACT_ID"'",
    "invoice_number": "INV-2025-001",
    "status": "draft",
    "due_date": "2025-02-28",
    "items": [
      {
        "description": "Enterprise Impact Analysis - February 2025",
        "quantity": 1,
        "unit_price": 2999.99,
        "currency": "USD"
      }
    ],
    "notes": "Thank you for your business!"
  }')

echo "$INVOICE_RESPONSE" | python -m json.tool
INVOICE_ID=$(echo "$INVOICE_RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "Created invoice with ID: $INVOICE_ID"
echo ""

echo "7. Testing PDF invoice generation..."
curl -s -X POST "$BASE_URL/enterprise/invoices/$INVOICE_ID/generate-pdf" \
  -H "$ADMIN_HEADER" \
  -H "Content-Type: application/json" \
  -d '{}' > /tmp/invoice_test.pdf

if [ -s /tmp/invoice_test.pdf ]; then
    echo "✅ PDF generated successfully! Size: $(stat -c%s /tmp/invoice_test.pdf) bytes"
    echo "   PDF saved to /tmp/invoice_test.pdf"
else
    echo "❌ PDF generation failed or returned empty"
fi
echo ""

echo "8. Testing search endpoint..."
curl -s "$BASE_URL/enterprise/search?q=Global" -H "$ADMIN_HEADER" | python -m json.tool
echo ""

echo "🎯 Enterprise API Test Completed!"
echo "=================================="
