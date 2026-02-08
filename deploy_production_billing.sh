#!/bin/bash
echo "🚀 PRODUCTION BILLING SYSTEM DEPLOYMENT"
echo "========================================"
echo ""

# Check prerequisites
echo "🔍 Checking prerequisites..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    exit 1
fi

if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL client is not installed"
    exit 1
fi

if ! command -v stripe &> /dev/null; then
    echo "⚠️ Stripe CLI not installed (optional for webhook testing)"
fi

# Load environment
echo "📁 Loading environment..."
if [ ! -f ".env.working" ]; then
    echo "❌ .env.working not found"
    exit 1
fi

source .env.working

# Check Docker
echo "🐳 Checking Docker..."
if ! docker compose ps | grep -q passenger-impact-engine; then
    echo "❌ Docker containers not running"
    echo "Starting Docker containers..."
    docker compose up -d
    sleep 10
fi

# Check database connection
echo "🗄️ Checking database..."
if ! PGPASSWORD=piepass psql -h 127.0.0.1 -p 55432 -U pie -d pie -c "SELECT 1" &> /dev/null; then
    echo "❌ Cannot connect to database"
    exit 1
fi

echo "✅ All prerequisites met"

# Deploy database schema
echo ""
echo "🗄️ Deploying database schema..."
PGPASSWORD=piepass psql -h 127.0.0.1 -p 55432 -U pie -d pie < update_database_schema.sql

# Restart application to pick up changes
echo "🔄 Restarting application..."
docker compose restart app

# Wait for application to start
echo "⏳ Waiting for application to start..."
sleep 5

# Run comprehensive test
echo ""
echo "🧪 Running comprehensive tests..."
python test_advanced_billing.py

# Show deployment status
echo ""
echo "📊 DEPLOYMENT STATUS"
echo "==================="

# Check application health
echo -n "🌐 Application Health: "
if curl -s http://127.0.0.1:8080/health | grep -q healthy; then
    echo "✅"
else
    echo "❌"
fi

# Check database
echo -n "🗄️ Database Connection: "
if PGPASSWORD=piepass psql -h 127.0.0.1 -p 55432 -U pie -d pie -c "SELECT 1" &> /dev/null; then
    echo "✅"
else
    echo "❌"
fi

# Check Stripe connection
echo -n "💳 Stripe Connection: "
python3 -c "
import os, stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
try:
    stripe.Customer.list(limit=1)
    print('✅')
except Exception as e:
    print(f'❌ ({str(e)[:30]}...)')
"

# Check subscription status
echo -n "💰 Subscription Status: "
API_KEY=$(grep API_SECRET .env.working | cut -d= -f2 | tr -d "'\"")
COMPANY_ID=$(grep COMPANY_ID .env.working | cut -d= -f2 | tr -d "'\"")
RESPONSE=$(curl -s -H "X-Company-Id: $COMPANY_ID" -H "X-Api-Key: $API_KEY" \
  http://127.0.0.1:8080/enterprise/billing/subscription)

if echo "$RESPONSE" | grep -q '"plan":"pro"'; then
    echo "✅ PRO PLAN ACTIVE"
else
    echo "⚠️ Not on PRO plan"
fi

echo ""
echo "🎯 PRODUCTION DEPLOYMENT COMPLETE"
echo ""
echo "📋 NEXT STEPS:"
echo "1. Set up Stripe webhooks for live updates:"
echo "   stripe listen --forward-to localhost:8080/enterprise/billing/webhook"
echo "2. Configure webhook secret in .env.working"
echo "3. Test complete checkout flow with test card"
echo "4. Set up monitoring and alerts"
echo "5. Implement backup strategy"
echo ""
echo "🔗 Useful URLs:"
echo "   - Health: http://127.0.0.1:8080/health"
echo "   - Subscription: http://127.0.0.1:8080/enterprise/billing/subscription"
echo "   - Checkout: Use POST /enterprise/billing/checkout"
echo "   - Billing Portal: Use POST /enterprise/billing/portal"
echo ""
echo "💳 Test Card: 4242 4242 4242 4242"
