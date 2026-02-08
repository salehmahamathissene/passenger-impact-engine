#!/bin/bash
echo "🔍 DEBUGGING POSTGRESQL DATABASE"
echo "================================"

echo ""
echo "1️⃣ Database Connection Info:"
echo "   DATABASE_URL: $DATABASE_URL"
echo "   DB_NAME: $DB_NAME"

echo ""
echo "2️⃣ Checking PostgreSQL service:"
if pg_isready &> /dev/null; then
    echo "✅ PostgreSQL is running"
else
    echo "❌ PostgreSQL is NOT running"
    echo "Start with: pg_ctl start"
fi

echo ""
echo "3️⃣ Querying database directly:"
python3 -c "
import os
import sys
sys.path.append('$PWD/src')
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv('.env.working')
engine = create_engine('$DATABASE_URL')

with engine.connect() as conn:
    # Check all tables
    print('📊 All tables in database:')
    result = conn.execute(text(\"\"\"
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    \"\"\"))
    for row in result:
        print(f'  - {row[0]}')
    
    # Check company data
    print('\\n👤 Company data:')
    result = conn.execute(
        text('SELECT id, name, stripe_customer_id FROM enterprise_companies'),
    )
    companies = result.fetchall()
    if companies:
        for company in companies:
            print(f'  ID: {company[0]}')
            print(f'  Name: {company[1]}')
            print(f'  Stripe Customer ID: {company[2]}')
            print('  ---')
    else:
        print('  No companies found in database!')
        
    # Check subscription data
    print('\\n💰 Subscription data:')
    result = conn.execute(
        text('SELECT * FROM enterprise_subscriptions'),
    )
    subscriptions = result.fetchall()
    if subscriptions:
        for sub in subscriptions:
            print(f'  Company ID: {sub[0]}')
            print(f'  Plan: {sub[1]}')
            print(f'  Status: {sub[2]}')
            print('  ---')
    else:
        print('  No subscriptions found in database!')
        
    # Check row counts
    print('\\n📈 Row counts:')
    tables = ['enterprise_companies', 'enterprise_subscriptions', 'enterprise_invoices']
    for table in tables:
        try:
            result = conn.execute(text(f'SELECT COUNT(*) FROM {table}'))
            count = result.scalar()
            print(f'  {table}: {count} rows')
        except:
            print(f'  {table}: Table does not exist')
"

echo ""
echo "4️⃣ Testing API with real PostgreSQL backend:"
curl -s "http://127.0.0.1:8080/enterprise/billing/subscription" \
  -H "X-Company-Id: $COMPANY_ID" \
  -H "X-Api-Key: $API_KEY" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print('Current subscription via API:')
for key, value in data.items():
    print(f'  {key}: {value}')
print('')
if data.get('plan') == 'free':
    print('⚠️  WARNING: Still showing free plan!')
    print('   The subscription endpoint needs to query PostgreSQL')
    print('   Check billing_routes.py implementation')
"
