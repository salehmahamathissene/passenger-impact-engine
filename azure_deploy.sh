#!/bin/bash
set -euo pipefail

echo "🚀 AZURE PRODUCTION DEPLOYMENT SCRIPT"
echo "====================================="

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI not found. Installing..."
    
    # Install Azure CLI
    curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
    
    echo "✅ Azure CLI installed"
    echo "Please run: az login"
    echo "Then run this script again"
    exit 1
fi

# Check if logged in
if ! az account show &> /dev/null; then
    echo "❌ Not logged into Azure. Please run: az login"
    exit 1
fi

# Configuration
LOCATION="eastus"
RG="rg-pie-prod-$(date +%s)"
APP="pie-api-prod-$(date +%s)"
PG_SERVER="pg-pie-$(date +%s)"
PG_ADMIN="pieadmin"
PG_PASSWORD="$(openssl rand -base64 16 | tr -dc 'A-Za-z0-9!@#$%^&*' | head -c 16)"
ENTERPRISE_ADMIN_KEY="$(openssl rand -base64 32 | tr -dc 'A-Za-z0-9' | head -c 32)"

echo "📋 Deployment Configuration:"
echo "  Location: $LOCATION"
echo "  Resource Group: $RG"
echo "  App Name: $APP"
echo "  PostgreSQL Server: $PG_SERVER"

# Create Resource Group
echo -e "\n1. Creating Resource Group..."
az group create --name "$RG" --location "$LOCATION" --output table

# Create PostgreSQL Flexible Server
echo -e "\n2. Creating PostgreSQL Database..."
az postgres flexible-server create \
  --resource-group "$RG" \
  --name "$PG_SERVER" \
  --location "$LOCATION" \
  --admin-user "$PG_ADMIN" \
  --admin-password "$PG_PASSWORD" \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --storage-size 32 \
  --version 14 \
  --database-name "pie_enterprise" \
  --yes \
  --output table

# Get database host
PG_HOST=$(az postgres flexible-server show \
  --resource-group "$RG" \
  --name "$PG_SERVER" \
  --query fullyQualifiedDomainName \
  --output tsv)

# Create database schema
echo -e "\n3. Creating database schema..."
DATABASE_URL="postgresql://${PG_ADMIN}:${PG_PASSWORD}@${PG_HOST}/pie_enterprise?sslmode=require"

# Use psql to create schema
cat > /tmp/schema.sql << 'SQL'
CREATE TABLE IF NOT EXISTS enterprise_companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    legal_name VARCHAR(255) NOT NULL UNIQUE,
    trading_name VARCHAR(255),
    tier VARCHAR(50) NOT NULL CHECK (tier IN ('small', 'mid', 'large')),
    industry VARCHAR(50) NOT NULL CHECK (industry IN ('airline', 'airport', 'ground_handler', 'other')),
    country VARCHAR(2),
    phone VARCHAR(50),
    support_email VARCHAR(255),
    billing_email VARCHAR(255),
    website VARCHAR(255),
    employee_count INTEGER CHECK (employee_count > 0),
    annual_revenue_eur DECIMAL(15, 2),
    total_spent DECIMAL(15, 2) DEFAULT 0.00,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS enterprise_contracts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL,
    contract_type VARCHAR(50) NOT NULL CHECK (contract_type IN ('standard', 'premium', 'enterprise')),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    monthly_fee_eur DECIMAL(15, 2) NOT NULL CHECK (monthly_fee_eur > 0),
    features JSONB DEFAULT '[]'::jsonb,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES enterprise_companies(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS enterprise_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL,
    job_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    parameters JSONB DEFAULT '{}'::jsonb,
    result JSONB DEFAULT '{}'::jsonb,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES enterprise_companies(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS enterprise_invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL,
    invoice_number VARCHAR(100) UNIQUE NOT NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    total_amount_eur DECIMAL(15, 2) NOT NULL CHECK (total_amount_eur >= 0),
    items JSONB DEFAULT '[]'::jsonb,
    is_paid BOOLEAN DEFAULT FALSE,
    paid_at TIMESTAMP WITH TIME ZONE,
    due_date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES enterprise_companies(id) ON DELETE CASCADE
);
SQL

# Install psql if not present
if ! command -v psql &> /dev/null; then
    sudo apt-get update && sudo apt-get install -y postgresql-client
fi

# Execute schema
PGPASSWORD="$PG_PASSWORD" psql -h "$PG_HOST" -U "$PG_ADMIN" -d pie_enterprise -f /tmp/schema.sql

# Create Azure Container App Environment
echo -e "\n4. Creating Container App Environment..."
az containerapp env create \
  --name "$APP-env" \
  --resource-group "$RG" \
  --location "$LOCATION" \
  --logs-destination none \
  --output table

# Build Docker image locally
echo -e "\n5. Building Docker image..."
docker build -t "$APP:latest" .

# Create Container App
echo -e "\n6. Creating Container App..."
az containerapp create \
  --name "$APP" \
  --resource-group "$RG" \
  --environment "$APP-env" \
  --image "$APP:latest" \
  --target-port 8000 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 3 \
  --cpu 0.5 \
  --memory 1Gi \
  --env-vars \
    DATABASE_URL="$DATABASE_URL" \
    ENTERPRISE_ADMIN_KEY="$ENTERPRISE_ADMIN_KEY" \
    PYTHONPATH=/app/src \
  --output table

# Get the public URL
FQDN=$(az containerapp show \
  --name "$APP" \
  --resource-group "$RG" \
  --query properties.configuration.ingress.fqdn \
  --output tsv)

echo -e "\n✅ DEPLOYMENT COMPLETE!"
echo "====================================="
echo "🌐 Public URL: https://$FQDN"
echo "🔑 Admin Key: $ENTERPRISE_ADMIN_KEY"
echo "🗄️  Database: $PG_HOST"
echo ""
echo "📋 Quick Test:"
echo "  # Test health endpoint"
echo "  curl https://$FQDN/health"
echo ""
echo "  # Create a company"
echo "  curl -X POST https://$FQDN/enterprise/companies \\"
echo "    -H \"X-Admin-Key: $ENTERPRISE_ADMIN_KEY\" \\"
echo "    -H \"Content-Type: application/json\" \\"
echo "    -d '{\"legal_name\":\"Test Airline\",\"tier\":\"mid\",\"industry\":\"airline\",\"country\":\"US\"}'"
echo ""
echo "🔧 Management:"
echo "  # View logs"
echo "  az containerapp logs show --name $APP --resource-group $RG"
echo ""
echo "  # Scale up"
echo "  az containerapp update --name $APP --resource-group $RG --min-replicas 2 --max-replicas 5"
