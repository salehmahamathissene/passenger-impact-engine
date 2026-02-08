#!/bin/bash
echo "🔐 SETTING UP STRIPE FOR PRODUCTION PAYMENTS"
echo "============================================="
echo ""
echo "Step 1: Go to https://dashboard.stripe.com/test/apikeys"
echo "Step 2: Click 'Create test key' if you don't have one"
echo "Step 3: Copy your Secret key (starts with sk_test_)"
echo ""
echo "Step 4: For webhook secret, go to: Developers → Webhooks"
echo "Step 5: Click 'Add endpoint'"
echo "Step 6: Enter endpoint URL: http://YOUR_SERVER.com/pro/webhook"
echo "Step 7: Copy the 'Signing secret' (starts with whsec_)"
echo ""
echo "Step 8: Enter your keys below:"
echo ""

read -p "Enter Stripe Secret Key: " stripe_key
read -p "Enter Stripe Webhook Secret: " webhook_secret

# Update .env file
sed -i "s|STRIPE_SECRET_KEY=.*|STRIPE_SECRET_KEY=${stripe_key}|" .env
sed -i "s|STRIPE_WEBHOOK_SECRET=.*|STRIPE_WEBHOOK_SECRET=${webhook_secret}|" .env

echo ""
echo "✅ Stripe keys updated in .env file"
echo ""
echo "Step 9: Restart the API:"
echo "systemctl --user restart pie-api.service"
echo ""
echo "Step 10: Test a real payment:"
echo 'curl -X POST http://localhost:8080/pro/checkout \'
echo '  -H "Content-Type: application/json" \'
echo '  -d '\''{"email":"test@example.com","plan":"starter"}'\'' | jq .'
echo ""
echo "This will return a Stripe checkout URL for real payment testing!"
