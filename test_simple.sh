#!/bin/bash
set -euo pipefail

echo "🧪 TESTING ENTERPRISE API"
echo "========================="

BASE="http://127.0.0.1:8000"
KEY="test_admin_key_123"

# Test 1: Create Company
echo "1. Creating company..."
COMPANY_RESPONSE=$(curl -sS -X POST "$BASE/enterprise/companies" \
  -H "X-Admin-Key: $KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "legal_name": "Test Airline '$(date +%s)'",
    "tier": "mid",
    "industry": "airline",
    "country": "US"
  }')

echo "Response:"
echo "$COMPANY_RESPONSE" | python -m json.tool

# Extract company ID
CID=$(echo "$COMPANY_RESPONSE" | python -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data['id'])
except Exception as e:
    print('')
")

if [ -z "$CID" ]; then
    echo "❌ Failed to create company"
    exit 1
fi

echo "✅ Company ID: $CID"

# Test 2: Get Company
echo -e "\n2. Getting company details..."
curl -sS "$BASE/enterprise/companies/$CID" -H "X-Admin-Key: $KEY" | python -m json.tool

# Test 3: Create Contract
echo -e "\n3. Creating contract..."
CONTRACT_RESPONSE=$(curl -sS -X POST "$BASE/enterprise/companies/$CID/contracts" \
  -H "X-Admin-Key: $KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "contract_type": "standard",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "monthly_fee_eur": 1000
  }')

echo "Contract created:"
echo "$CONTRACT_RESPONSE" | python -m json.tool

# Test 4: Create CSV files
echo -e "\n4. Creating test CSV files..."
cat > schedule.csv << 'CSV'
flight_no,departure_airport,arrival_airport,departure_time,arrival_time
XY101,JFK,LHR,2024-01-15T08:00:00Z,2024-01-15T20:00:00Z
XY102,LHR,JFK,2024-01-16T10:00:00Z,2024-01-16T22:00:00Z
CSV

cat > bookings.csv << 'CSV'
booking_ref,flight_no,passenger_name,fare_class,fare_amount
BK001,XY101,John Doe,Economy,500
BK002,XY101,Jane Smith,Business,1500
BK003,XY102,Robert Brown,Economy,480
CSV

# Test 5: Upload Job
echo -e "\n5. Uploading job data..."
JOB_RESPONSE=$(curl -sS -X POST "$BASE/enterprise/companies/$CID/jobs/upload" \
  -H "X-Admin-Key: $KEY" \
  -F "job_type=revenue_analysis" \
  -F "schedule_file=@schedule.csv" \
  -F "bookings_file=@bookings.csv")

echo "Job created:"
echo "$JOB_RESPONSE" | python -m json.tool

# Extract job ID
JOB_ID=$(echo "$JOB_RESPONSE" | python -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data['job_id'])
except:
    print('')
")

# Wait for processing
echo -e "\n6. Waiting for job processing..."
sleep 3

# Test 6: Check Job Status
echo -e "\n7. Checking job status..."
curl -sS "$BASE/enterprise/jobs/$JOB_ID" -H "X-Admin-Key: $KEY" | python -m json.tool

# Test 7: Generate Invoice
echo -e "\n8. Generating invoice..."
curl -sS -X POST "$BASE/enterprise/companies/$CID/invoices/generate" \
  -H "X-Admin-Key: $KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "period_start": "2024-01-01",
    "period_end": "2024-01-31",
    "items": [
      {"description": "Monthly subscription", "quantity": 1, "unit_price_eur": 1000},
      {"description": "API usage", "quantity": 100, "unit_price_eur": 0.10}
    ]
  }' | python -m json.tool

# Test 8: Get Analytics
echo -e "\n9. Getting analytics..."
curl -sS "$BASE/enterprise/analytics/summary" -H "X-Admin-Key: $KEY" | python -m json.tool

# Test 9: Health Checks
echo -e "\n10. Health checks:"
curl -sS "$BASE/health" | python -c "import sys,json; print('  Root health:', json.load(sys.stdin)['status'])"
curl -sS "$BASE/enterprise/health" -H "X-Admin-Key: $KEY" | python -c "
import sys,json
data = json.load(sys.stdin)
print('  Enterprise health:', data['status'])
print('  Database:', data['database'])
"

# Cleanup
rm -f schedule.csv bookings.csv

echo -e "\n✅ ALL TESTS COMPLETED SUCCESSFULLY!"
echo "Company ID: $CID"
echo "Job ID: $JOB_ID"
