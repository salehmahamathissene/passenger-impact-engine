#!/bin/bash
echo "🏭 PRODUCTION BILLING SYSTEM TEST"
echo "================================"

source .env.working
export PYTHONPATH="$PWD/src"

echo ""
echo "1️⃣ System Status:"
echo "================="

# Check server
echo -n "Server: "
if curl -s "http://127.0.0.1:8080/health" > /dev/null; then
    echo "✅ Running"
else
    echo "❌ Down"
    exit 1
fi

# Check Stripe
echo -n "Stripe: "
python3 -c "
import os
import stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
try:
    stripe.Balance.retrieve()
    print('✅ Connected')
except:
    print('❌ Not connected')
"

echo ""
echo "2️⃣ Company Authentication:"
echo "=========================="

INVOICE_RESPONSE=$(curl -s -i "http://127.0.0.1:8080/enterprise/invoices" \
  -H "X-Company-Id: $COMPANY_ID" \
  -H "X-Api-Key: $API_KEY")

STATUS_CODE=$(echo "$INVOICE_RESPONSE" | head -1 | cut -d' ' -f2)
if [ "$STATUS_CODE" = "200" ]; then
    echo "✅ Authentication working"
    echo "   Status: $STATUS_CODE"
else
    echo "❌ Authentication failed"
    echo "   Status: $STATUS_CODE"
    echo "   Response: $(echo "$INVOICE_RESPONSE" | tail -1)"
fi

echo ""
echo "3️⃣ Subscription Status:"
echo "======================"

SUBSCRIPTION_RESPONSE=$(curl -s "http://127.0.0.1:8080/enterprise/billing/subscription" \
  -H "X-Company-Id: $COMPANY_ID" \
  -H "X-Api-Key: $API_KEY")

echo "$SUBSCRIPTION_RESPONSE" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print('   Current subscription:')
    print(f'     Plan: {data.get(\"plan\")}')
    print(f'     Active: {data.get(\"active\")}')
    print(f'     Status: {data.get(\"status\")}')
    print(f'     Stripe Customer ID: {data.get(\"stripe_customer_id\", \"Not set\")}')
    
    if data.get('plan') == 'free' and not data.get('active'):
        print('   ✅ Expected initial state (free, not active)')
    else:
        print('   ⚠️  Unexpected initial state')
except Exception as e:
    print(f'   ❌ Error: {e}')
"

echo ""
echo "4️⃣ CREATE REAL CHECKOUT SESSION:"
echo "================================"

CHECKOUT_RESPONSE=$(curl -s -X POST "http://127.0.0.1:8080/enterprise/billing/checkout" \
  -H "Content-Type: application/json" \
  -H "X-Company-Id: $COMPANY_ID" \
  -H "X-Api-Key: $API_KEY" \
  -d '{"price_id": "'"$STRIPE_PRICE_PRO_MONTHLY"'"}')

echo "$CHECKOUT_RESPONSE" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    
    if 'url' in data:
        print('🎉 REAL CHECKOUT SESSION CREATED!')
        print('')
        print('🔗 CHECKOUT URL:')
        print(data['url'])
        print('')
        print('📋 DETAILS:')
        print(f'   Customer ID: {data.get(\"customer_id\", \"N/A\")}')
        print(f'   Price ID: {data.get(\"price_id\", \"N/A\")}')
        print(f'   Session ID: {data.get(\"session_id\", \"N/A\")}')
        
        # Save to file
        import os
        checkout_dir = '/tmp/production_checkout'
        os.makedirs(checkout_dir, exist_ok=True)
        
        with open(f'{checkout_dir}/url.txt', 'w') as f:
            f.write(data['url'])
        
        with open(f'{checkout_dir}/details.json', 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f'')
        print(f'💾 Saved to {checkout_dir}/')
        
    else:
        print('❌ FAILED TO CREATE CHECKOUT')
        print('Response:', data)
        sys.exit(1)
        
except Exception as e:
    print(f'❌ ERROR: {e}')
    print('Raw response:', sys.stdin.read())
    sys.exit(1)
"

echo ""
echo "5️⃣ Database Verification:"
echo "========================="

python3 -c "
import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.environ.get('DATABASE_URL')
engine = create_engine(DATABASE_URL)

company_id = os.environ.get('COMPANY_ID')

with engine.connect() as conn:
    # Get company
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
        print('✅ Company in database:')
        print(f'   Name: {result[0]}')
        print(f'   Plan: {result[1]}')
        print(f'   Active: {result[2]}')
        print(f'   Stripe Customer ID: {result[3] or \"Not set\"}')
        print(f'   Stripe Subscription ID: {result[4] or \"Not set\"}')
        
        # Check if customer ID was saved
        if result[3]:
            print('   ✅ Stripe customer ID saved to database')
        else:
            print('   ⚠️  Stripe customer ID not in database (checkout may save it)')
    else:
        print('❌ Company not found in database')
"

echo ""
echo "🎯 PRODUCTION TEST READY!"
echo "========================"
echo ""
echo "📝 NEXT STEPS:"
echo "1. Open checkout URL above"
echo "2. Use Stripe test card: 4242 4242 4242 4242"
echo "3. Complete payment"
echo "4. Webhook will update subscription"
echo ""
echo "🔍 To verify after payment:"
echo "   curl -s 'http://127.0.0.1:8080/enterprise/billing/subscription' \\"
echo "     -H 'X-Company-Id: \$COMPANY_ID' \\"
echo "     -H 'X-Api-Key: \$API_KEY'"
echo ""
echo "💡 Quick access:"
echo "   cat /tmp/production_checkout/url.txt"
