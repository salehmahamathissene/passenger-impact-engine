#!/bin/bash
echo "🔑 FIXING POSTGRESQL USER AUTHENTICATION"
echo "========================================="

echo ""
echo "1️⃣ Checking PostgreSQL users:"
sudo -u postgres psql -c "\du" || {
    echo "❌ Cannot connect as postgres user"
    echo "Trying alternative method..."
}

echo ""
echo "2️⃣ Options to fix:"
echo ""
echo "OPTION A: Reset password for user 'saleh'"
echo "-----------------------------------------"
echo "Run: sudo -u postgres psql"
echo "Then execute:"
echo "  ALTER USER saleh WITH PASSWORD 'M00dle!!';"
echo ""
echo "OPTION B: Create new user with correct password"
echo "----------------------------------------------"
echo "Run: sudo -u postgres psql"
echo "Then execute:"
echo "  CREATE USER pieuser WITH PASSWORD 'piepass123';"
echo "  CREATE DATABASE pie OWNER pieuser;"
echo "  GRANT ALL PRIVILEGES ON DATABASE pie TO pieuser;"
echo ""
echo "OPTION C: Use Docker PostgreSQL (EASIEST)"
echo "----------------------------------------"
echo "Stop local PostgreSQL: sudo systemctl stop postgresql"
echo "Use Docker instead"
echo ""
echo "3️⃣ Quick Docker fix (recommended):"
cat > docker-compose.yml <<'DOCKER'
version: '3.8'
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: pieuser
      POSTGRES_PASSWORD: piepass123
      POSTGRES_DB: pie
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U pieuser"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
DOCKER

echo "Docker compose file created"
echo "Run: docker compose down && docker compose up -d"
