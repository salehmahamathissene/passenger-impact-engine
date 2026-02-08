#!/bin/bash
echo "🔧 UPDATING STRIPE API KEY"
echo "=========================="

# Backup current .env.working
cp .env.working .env.working.backup.$(date +%Y%m%d_%H%M%S)

echo ""
echo "Current STRIPE_SECRET_KEY:"
grep "STRIPE_SECRET_KEY" .env.working

echo ""
read -p "Enter your valid Stripe test secret key (starts with 'sk_test_'): " STRIPE_KEY

if [[ -z "$STRIPE_KEY" ]]; then
    echo "❌ No key provided"
    exit 1
fi

if [[ ! "$STRIPE_KEY" =~ ^sk_test_ ]]; then
    echo "⚠️  Warning: Key doesn't start with 'sk_test_'"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted"
        exit 1
    fi
fi

# Update the key
sed -i "s|export STRIPE_SECRET_KEY=.*|export STRIPE_SECRET_KEY=\"$STRIPE_KEY\"|" .env.working

echo ""
echo "✅ Updated .env.working"
echo "New STRIPE_SECRET_KEY:"
grep "STRIPE_SECRET_KEY" .env.working

echo ""
echo "🔄 Reloading environment..."
source .env.working

echo ""
echo "🧪 Testing new key..."
python3 -c "
import os
import stripe

stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
try:
    # Test with a simple API call
    balance = stripe.Balance.retrieve()
    print('✅ Stripe API key is VALID!')
    print(f'   Available balance: \${balance.available[0].amount/100:.2f} {balance.available[0].currency}')
except stripe.error.AuthenticationError as e:
    print(f'❌ Authentication failed: {e}')
except Exception as e:
    print(f'⚠️  Error: {e}')
"
