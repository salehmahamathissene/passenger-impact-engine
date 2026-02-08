#!/bin/bash
echo "🚀 SETTING UP POSTGRESQL (PRODUCTION DATABASE)"
echo "=============================================="

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL is not installed!"
    echo "Install with:"
    echo "  Ubuntu/Debian: sudo apt-get install postgresql postgresql-contrib"
    echo "  Mac: brew install postgresql"
    echo "  Then run: sudo -u postgres createuser --superuser \$USER"
    exit 1
fi

# Create database if it doesn't exist
DB_NAME="passenger_impact_prod"
echo "Creating database: $DB_NAME"
createdb $DB_NAME 2>/dev/null || echo "Database already exists or permission issue"

# Update .env.working with PostgreSQL URL
echo "Updating .env.working with PostgreSQL connection..."
cat >> .env.working <<'ENV'

# PRODUCTION DATABASE - POSTGRESQL
export DATABASE_URL="postgresql://localhost/passenger_impact_prod"
export DB_HOST="localhost"
export DB_PORT="5432"
export DB_NAME="passenger_impact_prod"
export DB_USER="$USER"
ENV

echo "✅ PostgreSQL configured!"
echo "Database URL: postgresql://localhost/passenger_impact_prod"
