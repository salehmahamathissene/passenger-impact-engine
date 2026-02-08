#!/bin/bash
echo "🏭 PRODUCTION PAYMENT FLOW TEST"
echo "================================"

source .env.working
export PYTHONPATH="$PWD/src"

echo ""
echo "1️⃣ System Status:"
echo "================="

# Check Docker
echo "Docker PostgreSQL:"
docker compose ps

# Check server
echo -n "Server: "
if curl -s "http://127.0.0.1:8080/health" > /dev/null; then
    echo "✅ Running"
else
    echo "❌ Down"
    exit 1
fi

echo ""
echo "2️⃣ Create Checkout Session:"
echo "==========================="

RESPONSE=$(curl -s -X POST "http://127.0.0.1:8080/enterprise/billing/checkout" \
  -H "Content-Type: application/json" \
  -H "X-Company-Id: $COMPANY_ID" \
  -H "X-Api-Key: $API_KEY" \
  -d '{"price_id": "'"$STRIPE_PRICE_PRO_MONTHLY"'"}')

echo "$RESPONSE" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    
    if 'url' in data:
        print('✅ PRODUCTION CHECKOUT CREATED')
        print('')
        print('🔗 CHECKOUT URL:')
        print(data['url'])
        print('')
        print('📋 DETAILS:')
        print(f'   Customer ID: {data.get(\"customer_id\", \"N/A\")}')
        print(f'   Price ID: {data.get(\"price_id\", \"N/A\")}')
        print(f'   Stripe Session: {data.get(\"session_id\", \"N/A\")}')
        
        # Save to production file
        import os
        checkout_dir = '/tmp/production_checkout'
        os.makedirs(checkout_dir, exist_ok=True)
        
        with open(f'{checkout_dir}/url.txt', 'w') as f:
            f.write(data['url'])
        
        with open(f'{checkout_dir}/details.json', 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f'💾 Saved to {checkout_dir}/')
        
    else:
        print('❌ FAILED TO CREATE CHECKOUT')
        print('Response:', data)
        sys.exit(1)
        
except Exception as e:
    print(f'❌ ERROR: {e}')
    sys.exit(1)
"

echo ""
echo "3️⃣ Database Verification:"
echo "========================="

python3 -c "
import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.environ.get('DATABASE_URL')
engine = create_engine(DATABASE_URL)

company_id = os.environ.get('COMPANY_ID')

with engine.connect() as conn:
    # Check company
    result = conn.execute(
        text('''
            SELECT 
                legal_name, plan, is_active,
                stripe_customer_id, stripe_subscription_id,
                current_period_end
            FROM enterprise_companies 
            WHERE id = :id
        '''),
        {'id': company_id}
    ).fetchone()
    
    if result:
        print('✅ Company verified in database:')
        print(f'   Name: {result[0]}')
        print(f'   Plan: {result[1]}')
        print(f'   Active: {result[2]}')
        print(f'   Stripe Customer ID: {result[3] or \"Not set\"}')
        print(f'   Stripe Subscription ID: {result[4] or \"Not set\"}')
        
        if result[3]:
            print('   ✅ Stripe customer ID present')
        else:
            print('   ⚠️  Stripe customer ID not set (will be set after checkout)')
    else:
        print('❌ Company not found in database')
"

echo ""
echo "🎯 PRODUCTION TEST INSTRUCTIONS:"
echo "================================"
echo ""
echo "1. OPEN CHECKOUT URL (above)"
echo "2. USE STRIPE TEST CARD:"
echo "   • Number: 4242 4242 4242 4242"
echo "   • Expiry: Any future date"
echo "   • CVC: Any 3 digits"
echo "   • ZIP: Any 5 digits"
echo ""
echo "3. AFTER PAYMENT, VERIFY:"
echo "   curl -s 'http://127.0.0.1:8080/enterprise/billing/subscription' \\"
echo "     -H 'X-Company-Id: \$COMPANY_ID' \\"
echo "     -H 'X-Api-Key: \$API_KEY'"
echo ""
echo "   Should show: plan='pro', active=true"
echo ""
echo "4. CHECK DATABASE:"
echo "   SELECT plan, is_active FROM enterprise_companies WHERE id='\$COMPANY_ID';"
echo ""
echo "📁 Checkout files saved in: /tmp/production_checkout/"
