#!/bin/bash
echo "🚀 SETTING UP PRODUCTION POSTGRESQL DATABASE"

# 1. Install PostgreSQL
sudo apt update
sudo apt install -y postgresql postgresql-contrib libpq-dev

# 2. Start PostgreSQL
sudo systemctl enable --now postgresql
sudo systemctl status postgresql --no-pager

# 3. Create database and user
echo "📦 Creating database and user..."
sudo -u postgres psql <<SQL
-- Drop existing if needed
DROP DATABASE IF EXISTS pie;
DROP USER IF EXISTS pie;

-- Create production user with proper permissions
CREATE USER pie WITH PASSWORD 'pie123';
CREATE DATABASE pie OWNER pie;
ALTER USER pie CREATEDB;
ALTER USER pie WITH SUPERUSER;  -- For development only, restrict in production

-- Grant all privileges
GRANT ALL PRIVILEGES ON DATABASE pie TO pie;

-- Connect to database and set up
\c pie;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Show connection info
\conninfo
SQL

echo "✅ PostgreSQL setup complete!"
echo ""
echo "📊 CONNECTION INFO:"
echo "   Database: pie"
echo "   User: pie"
echo "   Password: pie123"
echo "   Host: localhost"
echo "   Port: 5432"
echo "   URL: postgresql+psycopg://pie:pie123@localhost:5432/pie"
