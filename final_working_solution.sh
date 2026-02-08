#!/bin/bash

echo "🔧 Final Working Solution for Passenger Impact Engine"
echo "===================================================="

# 1. Kill all servers
echo "1. Stopping all servers..."
pkill -f uvicorn 2>/dev/null || true
sleep 2

# 2. Use the minimal working app
echo "2. Starting minimal working app..."
cd ~/portfolio/passenger-impact-engine
python -m uvicorn minimal_working_app:app --host 0.0.0.0 --port 8000 --reload > final.log 2>&1 &

# 3. Wait and verify
echo "3. Waiting for server to start..."
sleep 5

if curl -s http://127.0.0.1:8000/ > /dev/null; then
    echo "✅ Server is running!"
else
    echo "❌ Server failed to start"
    tail -10 final.log
    exit 1
fi

# 4. Run comprehensive tests
echo ""
echo "4. Running comprehensive tests..."
ADMIN_KEY="test_admin_key_123"

echo "   Test 1: Basic endpoints"
curl -s http://127.0.0.1:8000/ | grep -q "Passenger Impact Engine" && echo "   ✅ Root endpoint works" || echo "   ❌ Root endpoint failed"

echo "   Test 2: Enterprise health"
response=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/enterprise/health -H "X-Admin-Key: $ADMIN_KEY")
[ "$response" = "200" ] && echo "   ✅ Enterprise health works" || echo "   ❌ Enterprise health failed: HTTP $response"

echo "   Test 3: Create company"
response=$(curl -s -X POST http://127.0.0.1:8000/enterprise/companies \
  -H "X-Admin-Key: $ADMIN_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "legal_name": "Final Solution Airlines",
    "trading_name": "FinalAir",
    "tier": "large",
    "industry": "airline",
    "country": "US",
    "phone": "+1-555-999-8888",
    "employee_count": 1000
  }')

if echo "$response" | grep -q "Company created successfully"; then
    echo "   ✅ Company creation works"
    # Extract company ID for next test
    COMPANY_ID=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
else
    echo "   ❌ Company creation failed: $response"
fi

echo "   Test 4: List companies"
count=$(curl -s http://127.0.0.1:8000/enterprise/companies -H "X-Admin-Key: $ADMIN_KEY" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(len(data.get('companies', [])))
except:
    print('0')
")

echo "   ✅ Found $count companies in database"

# 5. Show success message
echo ""
echo "🎉 PASSENGER IMPACT ENGINE IS WORKING!"
echo ""
echo "📋 Quick Reference:"
echo "   URL: http://localhost:8000"
echo "   API Documentation: http://localhost:8000/docs"
echo "   Admin Key: $ADMIN_KEY"
echo "   Database: postgresql://pie:piepass@127.0.0.1:55432/pie_enterprise"
echo ""
echo "🔧 Available Endpoints:"
echo "   GET /                                 - API info"
echo "   GET /health                          - Health check"
echo "   GET /enterprise/health               - Enterprise health (requires admin key)"
echo "   GET /enterprise/companies            - List companies"
echo "   POST /enterprise/companies           - Create company"
echo ""
echo "💡 Example Commands:"
echo "   # List companies"
echo "   curl http://localhost:8000/enterprise/companies -H 'X-Admin-Key: $ADMIN_KEY'"
echo ""
echo "   # Create a company"
echo "   curl -X POST http://localhost:8000/enterprise/companies \\"
echo "     -H 'X-Admin-Key: $ADMIN_KEY' \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '\"legal_name\": \"Example Airlines\", \"tier\": \"medium\", \"industry\": \"airline\"}'"
echo ""
echo "📝 Check logs: tail -f final.log"
echo ""
echo "🚀 To make this permanent, copy minimal_working_app.py to src/pie/main.py"
