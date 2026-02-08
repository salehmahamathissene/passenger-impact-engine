#!/usr/bin/env bash
set -euo pipefail

APP_NAME="passenger-impact-engine"
IMAGE="passenger-impact-engine:latest"
REGION="lax"

echo "🚀 DEPLOY (real script)"
echo "======================="
echo "App:    $APP_NAME"
echo "Image:  $IMAGE"
echo "Region: $REGION"
echo

need() { command -v "$1" >/dev/null 2>&1 || { echo "❌ Missing: $1"; exit 1; }; }

need docker

echo "🏗️  Building Docker image..."
docker build -t "$IMAGE" .
echo "✅ Build complete."
echo

echo "Choose platform:"
echo "1) Azure App Service (recommended)"
echo "2) Fly.io (flyctl)"
read -r -p "Enter 1 or 2: " choice
echo

if [[ "$choice" == "1" ]]; then
  need az
  echo "🟦 Azure deploy: use the Azure guide commands (below)."
  echo "Next: az login"
  exit 0
fi

if [[ "$choice" == "2" ]]; then
  need flyctl
  echo "🛫 Deploying to Fly.io..."
  flyctl apps list | grep -q "$APP_NAME" || flyctl apps create "$APP_NAME"
  flyctl deploy --app "$APP_NAME" --region "$REGION"
  echo
  echo "✅ Fly deploy done."
  echo "Set secrets with:"
  echo "flyctl secrets set -a $APP_NAME DATABASE_URL='...' ENTERPRISE_ADMIN_KEY='...' STRIPE_SECRET_KEY='...' STRIPE_WEBHOOK_SECRET='...'"
  exit 0
fi

echo "❌ Invalid choice. Enter 1 or 2."
exit 1
