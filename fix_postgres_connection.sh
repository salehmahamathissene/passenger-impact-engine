#!/bin/bash
echo "🔧 FIXING POSTGRESQL CONNECTION"
echo "================================"

echo ""
echo "1️⃣ Testing PostgreSQL connection manually:"
echo "Attempting to connect to PostgreSQL..."

# Try different connection methods
python3 -c "
import psycopg2
import os

# Try connection without password first (peer auth)
try:
    conn = psycopg2.connect(
        dbname='passenger_impact_prod',
        user='saleh',
        host='localhost',
        port='5432'
    )
    print('✅ Connected via peer authentication')
    conn.close()
except Exception as e:
    print(f'❌ Peer auth failed: {e}')

# Try with postgres user
try:
    conn = psycopg2.connect(
        dbname='postgres',
        user='postgres',
        host='localhost',
        port='5432'
    )
    print('✅ Connected as postgres user')
    conn.close()
except Exception as e:
    print(f'❌ Postgres user failed: {e}')
"

echo ""
echo "2️⃣ Checking your db.py file..."
if [ -f "src/pie/pro/db.py" ]; then
    echo "📄 db.py content:"
    echo "================"
    cat src/pie/pro/db.py
else
    echo "❌ db.py not found!"
fi

echo ""
echo "3️⃣ Fixing database URL in .env.working..."
# Add password to DATABASE_URL or fix authentication
read -p "Enter PostgreSQL password for user 'saleh' (press Enter if using peer auth): " -s PG_PASSWORD
echo

if [ -n "$PG_PASSWORD" ]; then
    echo "Updating .env.working with password..."
    sed -i '/export DATABASE_URL/d' .env.working
    echo "export DATABASE_URL=\"postgresql://saleh:$PG_PASSWORD@localhost/passenger_impact_prod\"" >> .env.working
    echo "✅ Updated with password"
else
    echo "Using peer authentication (no password)"
    # Ensure DATABASE_URL doesn't have password
    sed -i '/export DATABASE_URL/d' .env.working
    echo "export DATABASE_URL=\"postgresql://localhost/passenger_impact_prod\"" >> .env.working
fi

source .env.working
echo "Current DATABASE_URL: $DATABASE_URL"
