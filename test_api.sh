#!/bin/bash

echo "🚀 Testing Passenger Impact Engine API"
echo "======================================"

BASE_URL="http://127.0.0.1:8000"
ADMIN_KEY="test_admin_key_123"

# Function to test endpoint
test_endpoint() {
    local method="$1"
    local endpoint="$2"
    local data="$3"
    local expected_code="$4"
    
    echo -n "  $method $endpoint: "
    
    if [ "$method" = "POST" ] && [ -n "$data" ]; then
        response_code=$(curl -s -o /dev/null -w "%{http_code}" \
            -X "$method" \
            "${BASE_URL}${endpoint}" \
            -H "X-Admin-Key: $ADMIN_KEY" \
            -H "Content-Type: application/json" \
            -d "$data" 2>/dev/null || echo "000")
    else
        response_code=$(curl -s -o /dev/null -w "%{http_code}" \
            -X "$method" \
            "${BASE_URL}${endpoint}" \
            -H "X-Admin-Key: $ADMIN_KEY" 2>/dev/null || echo "000")
    fi
    
    if [ "$response_code" = "$expected_code" ]; then
        echo "✅ HTTP $response_code"
        return 0
    else
        echo "❌ HTTP $response_code (expected $expected_code)"
        return 1
    fi
}

echo ""
echo "📡 Testing endpoints..."

# Test basic endpoints
echo "1. Basic endpoints:"
test_endpoint "GET" "/" "" "200"
test_endpoint "GET" "/health" "" "200"

# Test enterprise endpoints
echo ""
echo "2. Enterprise endpoints (with auth):"
test_endpoint "GET" "/enterprise/health" "" "200"

# Test without auth (should fail)
echo ""
echo "3. Enterprise endpoints (without auth - should fail):"
response_code=$(curl -s -o /dev/null -w "%{http_code}" \
    "${BASE_URL}/enterprise/health" 2>/dev/null || echo "000")
echo "  GET /enterprise/health (no auth): HTTP $response_code (should be 401)"

# Test company creation
echo ""
echo "4. Creating a test company:"
COMPANY_DATA='{
    "legal_name": "Global Airlines Inc",
    "trading_name": "GlobalAir",
    "tier": "large",
    "industry": "airline",
    "country": "US",
    "currency": "USD",
    "contact_email": "admin@globalair.com",
    "contact_phone": "+1-555-123-4567"
}'

response=$(curl -s -X POST \
    "${BASE_URL}/enterprise/companies" \
    -H "X-Admin-Key: $ADMIN_KEY" \
    -H "Content-Type: application/json" \
    -d "$COMPANY_DATA")

if echo "$response" | grep -q "Company created successfully"; then
    echo "  ✅ Company created successfully"
    COMPANY_ID=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
    echo "  Company ID: $COMPANY_ID"
else
    echo "  ❌ Failed to create company"
    echo "  Response: $response"
fi

# List companies
echo ""
echo "5. Listing companies:"
response=$(curl -s \
    "${BASE_URL}/enterprise/companies" \
    -H "X-Admin-Key: $ADMIN_KEY")

if echo "$response" | grep -q "companies"; then
    echo "  ✅ Retrieved companies list"
else
    echo "  ❌ Failed to list companies"
fi

echo ""
echo "🎉 API testing complete!"
echo ""
echo "Access Swagger UI: http://localhost:8000/docs"
echo "Admin Key: $ADMIN_KEY"
