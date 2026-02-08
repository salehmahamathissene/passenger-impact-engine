#!/bin/bash
echo "🔧 FIXING ENVIRONMENT FOR POSTGRESQL"
echo "===================================="

# Backup current .env.working
cp .env.working .env.working.backup

# Create new .env.working with CORRECT settings
cat > .env.working <<'ENV'
# PostgreSQL Database
export DATABASE_URL="postgresql://saleh:M00dle!!@localhost/passenger_impact_prod"

# Stripe Configuration
export STRIPE_SECRET_KEY="sk_test_REDACTED"
export STRIPE_PRICE_PRO_MONTHLY="price_1Sxwg1GTsbjFmuVQTy0qQbfh"
export STRIPE_WEBHOOK_SECRET="whsec_REDACTED_FROM_DASHBOARD"
export FRONTEND_BASE_URL="http://localhost:3000"

# Company and API Keys
export COMPANY_ID="fa2a2660-d89a-4437-a6ce-5f60397cf9c7"
export API_KEY="test_api_key_enterprise_789"

# Application
export JWT_SECRET="your-super-secret-jwt-key-change-in-production"
ENV

echo "✅ .env.working updated with CORRECT PostgreSQL URL"
echo "DATABASE_URL: postgresql://saleh:M00dle!!@localhost/passenger_impact_prod"
source .env.working
