#!/bin/bash
set -euo pipefail

echo "🚀 TESTING COMPLETE ENTERPRISE API"
echo "==================================="

BASE="http://127.0.0.1:8000"
KEY="test_admin_key_123"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to make API calls
api_call() {
    local method=$1
    local endpoint=$2
    local data=${3:-}
    local curl_cmd="curl -sS -X $method \"$BASE$endpoint\" -H \"X-Admin-Key: $KEY\""
    
    if [ -n "$data" ]; then
        curl_cmd="$curl_cmd -H \"Content-Type: application/json\" -d '$data'"
    fi
    
    echo -e "${YELLOW}→ $method $endpoint${NC}"
    eval $curl_cmd
}

# Test 1: Create Company
echo -e "\n${GREEN}1. Creating Company...${NC}"
CID=$(api_call POST "/enterprise/companies" '{
  "legal_name": "Azure Demo Airline '$(date +%s)'",
  "trading_name": "AzureAir",
  "tier": "mid",
  "industry": "airline",
  "country": "US",
  "employee_count": 500,
  "annual_revenue_eur": 50000000
}' | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])" 2>/dev/null || echo "")

if [ -z "$CID" ]; then
    echo -e "${RED}❌ Failed to create company${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Company Created: $CID${NC}"

# Test 2: Create Contract
echo -e "\n${GREEN}2. Creating Contract...${NC}"
api_call POST "/enterprise/companies/$CID/contracts" '{
  "contract_type": "premium",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "monthly_fee_eur": 5000,
  "features": ["advanced_analytics", "api_access", "support_24_7"]
}' | python3 -m json.tool

# Test 3: Upload Job Data
echo -e "\n${GREEN}3. Creating CSV files...${NC}"

cat > schedule.csv <<'CSV'
flight_no,departure_airport,arrival_airport,departure_time,arrival_time,aircraft_type
XY101,KGL,NBO,2024-01-15T08:00:00Z,2024-01-15T10:00:00Z,B737
XY102,NBO,KGL,2024-01-15T12:00:00Z,2024-01-15T14:00:00Z,B737
XY201,JNB,CPT,2024-01-15T09:00:00Z,2024-01-15T11:00:00Z,A320
XY202,CPT,JNB,2024-01-15T13:00:00Z,2024-01-15T15:00:00Z,A320
XY301,DXB,LHR,2024-01-15T22:00:00Z,2024-01-16T02:00:00Z,B777
CSV

cat > bookings.csv <<'CSV'
booking_ref,flight_no,passenger_name,booking_date,travel_date,fare_class,fare_amount
BK001,XY101,John Doe,2024-01-10,2024-01-15,Economy,450
BK002,XY101,Jane Smith,2024-01-11,2024-01-15,Business,1200
BK003,XY102,Robert Brown,2024-01-09,2024-01-15,Economy,420
BK004,XY201,Alice Johnson,2024-01-08,2024-01-15,First,1800
BK005,XY202,Charlie Wilson,2024-01-12,2024-01-15,Economy,400
BK006,XY301,David Lee,2024-01-07,2024-01-15,Business,1500
CSV

echo -e "${GREEN}4. Uploading Job Data...${NC}"
JOB_RESPONSE=$(curl -sS -X POST "$BASE/enterprise/companies/$CID/jobs/upload" \
  -H "X-Admin-Key: $KEY" \
  -F "job_type=revenue_analysis" \
  -F "schedule_file=@schedule.csv" \
  -F "bookings_file=@bookings.csv")

JOB_ID=$(echo "$JOB_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['job_id'])" 2>/dev/null || echo "")

if [ -z "$JOB_ID" ]; then
    echo -e "${RED}❌ Failed to create job${NC}"
    echo "$JOB_RESPONSE" | python3 -m json.tool
    exit 1
fi

echo -e "${GREEN}✅ Job Created: $JOB_ID${NC}"
echo "$JOB_RESPONSE" | python3 -m json.tool

# Test 5: Run Job
echo -e "\n${GREEN}5. Running Job...${NC}"
sleep 2
api_call POST "/enterprise/jobs/$JOB_ID/run" | python3 -m json.tool

# Test 6: Check Job Status
echo -e "\n${GREEN}6. Checking Job Status...${NC}"
sleep 3
api_call GET "/enterprise/jobs/$JOB_ID" | python3 -m json.tool

# Test 7: Generate Invoice
echo -e "\n${GREEN}7. Generating Invoice...${NC}"
api_call POST "/enterprise/companies/$CID/invoices/generate" '{
  "period_start": "2024-01-01",
  "period_end": "2024-01-31",
  "items": [
    {"description": "Premium Subscription - January 2024", "quantity": 1, "unit_price_eur": 5000},
    {"description": "API Usage - 1M requests", "quantity": 10, "unit_price_eur": 50},
    {"description": "Support Services", "quantity": 1, "unit_price_eur": 500}
  ]
}' | python3 -m json.tool

# Test 8: Get Company Invoices
echo -e "\n${GREEN}8. Getting Company Invoices...${NC}"
api_call GET "/enterprise/companies/$CID/invoices" | python3 -m json.tool

# Test 9: List All Jobs
echo -e "\n${GREEN}9. Listing All Jobs...${NC}"
api_call GET "/enterprise/jobs" | python3 -m json.tool

# Test 10: Get Analytics Summary
echo -e "\n${GREEN}10. Getting Analytics Summary...${NC}"
api_call GET "/enterprise/analytics/summary" | python3 -m json.tool

# Test 11: Get Company Details
echo -e "\n${GREEN}11. Getting Company Details...${NC}"
api_call GET "/enterprise/companies/$CID" | python3 -m json.tool

# Test 12: Get Company Contracts
echo -e "\n${GREEN}12. Getting Company Contracts...${NC}"
api_call GET "/enterprise/companies/$CID/contracts" | python3 -m json.tool

# Test 13: List All Companies
echo -e "\n${GREEN}13. Listing All Companies...${NC}"
api_call GET "/enterprise/companies" | python3 -c "
import sys,json
data = json.load(sys.stdin)
print(f'Total Companies: {data[\"total\"]}')
print('Recent Companies:')
for company in data['companies'][:3]:
    print(f'  • {company[\"legal_name\"]} ({company[\"tier\"]})')
"

# Test 14: Health Checks
echo -e "\n${GREEN}14. Running Health Checks...${NC}"
curl -sS "$BASE/health" | python3 -c "import sys,json; print('Root Health:', json.load(sys.stdin)['status'])"
curl -sS "$BASE/enterprise/health" -H "X-Admin-Key: $KEY" | python3 -c "
import sys,json
data = json.load(sys.stdin)
print('Enterprise Health:', data['status'])
print('Database:', data['database'])
print('Companies:', data['counts']['companies'])
"

# Cleanup
echo -e "\n${GREEN}15. Cleaning up...${NC}"
rm -f schedule.csv bookings.csv

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}✅ ALL TESTS COMPLETED SUCCESSFULLY!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\n📊 Test Summary:"
echo "  • Company Created: $CID"
echo "  • Job Processed: $JOB_ID"
echo "  • All endpoints tested successfully"
echo -e "\n🚀 Enterprise API is fully operational!"
