#!/bin/bash
echo "🔧 UPDATING ENVIRONMENT FOR DOCKER POSTGRESQL"
echo "============================================="

# Update .env.working with Docker PostgreSQL connection
cat > .env.working <<'ENV'
# DOCKER PostgreSQL Database
export DATABASE_URL="postgresql://pieuser:piepass123@localhost:5432/pie"

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

source .env.working
echo "✅ Updated .env.working with Docker PostgreSQL"
echo "DATABASE_URL: $DATABASE_URL"
