#!/usr/bin/env bash
set -euo pipefail

# -------------------------
# EDIT ONLY THIS SECTION
# -------------------------
LOCATION="eastus"

RG="rg-pie-prod"
APP="pie-api-prod"
IMG="pie-api:1.0.0"

# MUST be globally unique (we append random)
ACR="acrpieprod$RANDOM"
PG_SERVER="pg-pie-prod-$RANDOM"
STORAGE="stpieprod$RANDOM"      # lowercase only
SB_NS="sb-pie-prod-$RANDOM"
KV="kv-pie-prod-$RANDOM"

PG_ADMIN="pieadmin"
PG_DB="pie_enterprise"
SB_QUEUE="pie-jobs"

# Allowed CORS origins (comma-separated)
CORS_ORIGINS="https://yourdomain.com"

# -------------------------
# DO NOT EDIT BELOW
# -------------------------

need_cmd() { command -v "$1" >/dev/null 2>&1 || { echo "❌ Missing command: $1"; exit 1; }; }

need_cmd az
need_cmd python
need_cmd docker

echo "==> Checking Azure login..."
az account show >/dev/null

ENTERPRISE_ADMIN_KEY="$(python - <<'PY'
import secrets
print(secrets.token_urlsafe(32))
PY
)"

PG_PASSWORD="$(python - <<'PY'
import secrets, string
alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
print("".join(secrets.choice(alphabet) for _ in range(24)))
PY
)"

echo "==> Creating resource group..."
az group create -n "$RG" -l "$LOCATION" 1>/dev/null

echo "==> Creating Log Analytics + App Insights..."
LAW="law-pie-prod-$RANDOM"
az monitor log-analytics workspace create -g "$RG" -n "$LAW" -l "$LOCATION" 1>/dev/null
LAW_ID="$(az monitor log-analytics workspace show -g "$RG" -n "$LAW" --query customerId -o tsv)"
LAW_KEY="$(az monitor log-analytics workspace get-shared-keys -g "$RG" -n "$LAW" --query primarySharedKey -o tsv)"

AI="ai-pie-prod-$RANDOM"
az monitor app-insights component create -g "$RG" -n "$AI" -l "$LOCATION" \
  --workspace "$LAW" --application-type web 1>/dev/null
AI_CONN="$(az monitor app-insights component show -g "$RG" -n "$AI" --query connectionString -o tsv)"

echo "==> Creating ACR..."
az acr create -g "$RG" -n "$ACR" --sku Basic --admin-enabled true 1>/dev/null
ACR_LOGIN_SERVER="$(az acr show -g "$RG" -n "$ACR" --query loginServer -o tsv)"

echo "==> Building + pushing image to ACR..."
az acr build -r "$ACR" -t "$IMG" . 1>/dev/null
FULL_IMAGE="${ACR_LOGIN_SERVER}/${IMG}"

echo "==> Creating Postgres Flexible Server..."
az postgres flexible-server create \
  -g "$RG" -n "$PG_SERVER" -l "$LOCATION" \
  --admin-user "$PG_ADMIN" --admin-password "$PG_PASSWORD" \
  --sku-name Standard_B1ms --storage-size 32 \
  --version 15 \
  --public-access 0.0.0.0 \
  1>/dev/null

echo "==> Creating database..."
az postgres flexible-server db create -g "$RG" -s "$PG_SERVER" -d "$PG_DB" 1>/dev/null
PG_FQDN="$(az postgres flexible-server show -g "$RG" -n "$PG_SERVER" --query fullyQualifiedDomainName -o tsv)"

DATABASE_URL="postgresql+psycopg://${PG_ADMIN}:${PG_PASSWORD}@${PG_FQDN}:5432/${PG_DB}?sslmode=require"

echo "==> Creating Storage Account + containers..."
az storage account create -g "$RG" -n "$STORAGE" -l "$LOCATION" --sku Standard_LRS 1>/dev/null
ST_KEY="$(az storage account keys list -g "$RG" -n "$STORAGE" --query '[0].value' -o tsv)"
az storage container create --account-name "$STORAGE" --account-key "$ST_KEY" -n uploads 1>/dev/null
az storage container create --account-name "$STORAGE" --account-key "$ST_KEY" -n outputs 1>/dev/null

echo "==> Creating Service Bus (queue)..."
az servicebus namespace create -g "$RG" -n "$SB_NS" -l "$LOCATION" --sku Basic 1>/dev/null
az servicebus queue create -g "$RG" --namespace-name "$SB_NS" -n "$SB_QUEUE" 1>/dev/null

echo "==> Creating Key Vault + saving secrets..."
az keyvault create -g "$RG" -n "$KV" -l "$LOCATION" 1>/dev/null
az keyvault secret set --vault-name "$KV" -n DATABASE-URL --value "$DATABASE_URL" 1>/dev/null
az keyvault secret set --vault-name "$KV" -n ENTERPRISE-ADMIN-KEY --value "$ENTERPRISE_ADMIN_KEY" 1>/dev/null
az keyvault secret set --vault-name "$KV" -n STORAGE-ACCOUNT-KEY --value "$ST_KEY" 1>/dev/null

echo "==> Installing containerapp extension (if needed)..."
az extension add --name containerapp --upgrade 1>/dev/null

echo "==> Creating Container Apps environment..."
CAE="cae-pie-prod-$RANDOM"
az containerapp env create -g "$RG" -n "$CAE" -l "$LOCATION" \
  --logs-workspace-id "$LAW_ID" --logs-workspace-key "$LAW_KEY" 1>/dev/null

echo "==> Creating Container App (API)..."
az containerapp create -g "$RG" -n "$APP" --environment "$CAE" \
  --image "$FULL_IMAGE" \
  --ingress external --target-port 8000 \
  --cpu 0.5 --memory 1.0Gi \
  --min-replicas 1 --max-replicas 3 \
  --env-vars \
    ENVIRONMENT=production \
    LOG_LEVEL=info \
    CORS_ORIGINS="$CORS_ORIGINS" \
    APPLICATIONINSIGHTS_CONNECTION_STRING="$AI_CONN" \
  1>/dev/null

echo "==> Enabling Managed Identity on Container App..."
az containerapp identity assign -g "$RG" -n "$APP" 1>/dev/null

echo "==> Loading KeyVault secrets and wiring into Container App..."
DBURL="$(az keyvault secret show --vault-name "$KV" -n DATABASE-URL --query value -o tsv)"
ADMKEY="$(az keyvault secret show --vault-name "$KV" -n ENTERPRISE-ADMIN-KEY --query value -o tsv)"

az containerapp secret set -g "$RG" -n "$APP" \
  --secrets \
    database-url="$DBURL" \
    enterprise-admin-key="$ADMKEY" \
  1>/dev/null

az containerapp update -g "$RG" -n "$APP" \
  --set-env-vars \
    DATABASE_URL=secretref:database-url \
    ENTERPRISE_ADMIN_KEY=secretref:enterprise-admin-key \
  1>/dev/null

FQDN="$(az containerapp show -g "$RG" -n "$APP" --query properties.configuration.ingress.fqdn -o tsv)"

echo
echo "✅ DEPLOYED"
echo "API URL: https://${FQDN}"
echo "Docs:    https://${FQDN}/docs"
echo
echo "SAVE THIS ADMIN KEY:"
echo "ENTERPRISE_ADMIN_KEY=${ENTERPRISE_ADMIN_KEY}"
echo
echo "Smoke tests:"
echo "  curl -sS https://${FQDN}/health"
echo "  curl -sS https://${FQDN}/enterprise/health -H \"X-Admin-Key: ${ENTERPRISE_ADMIN_KEY}\""
