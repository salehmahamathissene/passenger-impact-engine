#!/bin/bash

set -euo pipefail

echo "🚀 PROFESSIONAL DEPLOYMENT - Passenger Impact Engine"
echo "===================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="passenger-impact-engine"
APP_USER="${USER}"
APP_DIR="$(pwd)"
VENV_DIR="${APP_DIR}/.venv"
REQUIREMENTS="${APP_DIR}/requirements.txt"
SERVICE_FILE="/etc/systemd/system/${APP_NAME}.service"
ENV_FILE="${APP_DIR}/.env.production"
LOG_DIR="/var/log/${APP_NAME}"

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    echo -e "${RED}ERROR: Do not run as root. Run as regular user with sudo privileges.${NC}"
    exit 1
fi

echo -e "${YELLOW}📋 Deployment Checklist:${NC}"
echo "  1. Python 3.8+ installed"
echo "  2. PostgreSQL database available"
echo "  3. Redis (optional, for caching)"
echo "  4. Systemd for service management"
echo "  5. Nginx (optional, for reverse proxy)"

read -p "Continue with deployment? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 0
fi

echo -e "\n${GREEN}🔧 Step 1: Prerequisites Check${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 not found. Please install Python 3.8+.${NC}"
    exit 1
fi
echo "✅ Python3: $(python3 --version)"

# Check pip
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}❌ pip3 not found.${NC}"
    exit 1
fi
echo "✅ pip3: $(pip3 --version | cut -d' ' -f2)"

# Check PostgreSQL client
if ! command -v psql &> /dev/null; then
    echo -e "${YELLOW}⚠️  psql not found (PostgreSQL client). Database operations may be limited.${NC}"
else
    echo "✅ PostgreSQL client: available"
fi

echo -e "\n${GREEN}🔧 Step 2: Virtual Environment${NC}"

if [[ ! -d "${VENV_DIR}" ]]; then
    echo "Creating virtual environment..."
    python3 -m venv "${VENV_DIR}"
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
source "${VENV_DIR}/bin/activate"

echo -e "\n${GREEN}🔧 Step 3: Dependencies${NC}"

if [[ -f "${REQUIREMENTS}" ]]; then
    echo "Installing dependencies from requirements.txt..."
    pip install --upgrade pip
    pip install -r "${REQUIREMENTS}"
    echo "✅ Dependencies installed"
else
    echo "Installing core dependencies..."
    pip install --upgrade pip
    pip install fastapi uvicorn sqlalchemy psycopg2-binary python-dotenv
    echo "✅ Core dependencies installed"
fi

echo -e "\n${GREEN}🔧 Step 4: Environment Configuration${NC}"

if [[ ! -f "${ENV_FILE}" ]]; then
    echo "Creating production environment file..."
    
    # Generate secure admin key
    ADMIN_KEY=$(openssl rand -hex 32)
    
    cat > "${ENV_FILE}" << ENV_CONFIG
# Passenger Impact Engine - Production Environment
# ===============================================

# Database Configuration
DATABASE_URL=postgresql://username:password@hostname:port/database_name
# Example: DATABASE_URL=postgresql://pie:StrongPassword@db.example.com:5432/pie_production

# Security
ENTERPRISE_ADMIN_KEY=${ADMIN_KEY}

# Server Configuration
HOST=0.0.0.0
PORT=8000
WORKERS=4
RELOAD=false

# CORS (comma-separated)
CORS_ORIGINS=https://yourdomain.com,https://admin.yourdomain.com

# Logging
LOG_LEVEL=info

# Rate Limiting (requests per minute)
RATE_LIMIT=100

# Database Pool
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
ENV_CONFIG
    
    echo "✅ Environment file created at ${ENV_FILE}"
    echo -e "${YELLOW}⚠️  IMPORTANT: Edit ${ENV_FILE} with your production values before starting!${NC}"
else
    echo "✅ Environment file already exists"
fi

echo -e "\n${GREEN}🔧 Step 5: Systemd Service${NC}"

# Create log directory
echo "Creating log directory..."
sudo mkdir -p "${LOG_DIR}"
sudo chown "${APP_USER}:${APP_USER}" "${LOG_DIR}"

# Create systemd service file
echo "Creating systemd service..."
sudo tee "${SERVICE_FILE}" << SERVICE_FILE > /dev/null
[Unit]
Description=Passenger Impact Engine API
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=exec
User=${APP_USER}
Group=${APP_USER}
WorkingDirectory=${APP_DIR}
Environment="PATH=${VENV_DIR}/bin"
EnvironmentFile=${ENV_FILE}
ExecStart=${VENV_DIR}/bin/uvicorn src.pie.main:app \
  --host \${HOST} \
  --port \${PORT} \
  --workers \${WORKERS} \
  --no-reload \
  --log-level \${LOG_LEVEL}
Restart=always
RestartSec=10
StandardOutput=append:${LOG_DIR}/app.log
StandardError=append:${LOG_DIR}/error.log

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=${LOG_DIR} ${APP_DIR}

[Install]
WantedBy=multi-user.target
SERVICE_FILE

echo "✅ Systemd service file created"

echo -e "\n${GREEN}🔧 Step 6: Database Setup${NC}"

echo "Database setup instructions:"
echo "  1. Create a production PostgreSQL database"
echo "  2. Update DATABASE_URL in ${ENV_FILE}"
echo "  3. Run migrations if needed:"
echo "     source ${VENV_DIR}/bin/activate"
echo "     cd ${APP_DIR}"
echo "     alembic upgrade head"

echo -e "\n${GREEN}🔧 Step 7: Nginx Configuration (Optional)${NC}"

if command -v nginx &> /dev/null; then
    echo "Creating nginx configuration..."
    
    NGINX_CONF="/etc/nginx/sites-available/${APP_NAME}"
    
    sudo tee "${NGINX_CONF}" << NGINX_CONF > /dev/null
upstream ${APP_NAME} {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name yourdomain.com;
    
    # Redirect to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    # SSL certificates - configure with Certbot
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # SSL optimization
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # API Proxy
    location / {
        proxy_pass http://${APP_NAME};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
}
NGINX_CONF
    
    echo "✅ Nginx configuration created"
    echo "To enable: sudo ln -s ${NGINX_CONF} /etc/nginx/sites-enabled/"
    echo "Then: sudo nginx -t && sudo systemctl reload nginx"
else
    echo "ℹ️  Nginx not installed. For production, install nginx for reverse proxy and SSL."
fi

echo -e "\n${GREEN}🔧 Step 8: Final Steps${NC}"

echo "1. Edit production configuration:"
echo "   nano ${ENV_FILE}"
echo ""
echo "2. Enable and start the service:"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl enable ${APP_NAME}"
echo "   sudo systemctl start ${APP_NAME}"
echo ""
echo "3. Check service status:"
echo "   sudo systemctl status ${APP_NAME}"
echo "   tail -f ${LOG_DIR}/app.log"
echo ""
echo "4. Test the API:"
echo "   curl http://localhost:8000/health"
echo "   curl http://localhost:8000/enterprise/health -H 'X-Admin-Key: YOUR_ADMIN_KEY'"
echo ""
echo "5. Set up monitoring (optional):"
echo "   sudo apt install prometheus-node-exporter"
echo "   Configure firewall: sudo ufw allow 8000"
echo "   Set up log rotation"
echo ""
echo -e "${GREEN}🎉 DEPLOYMENT READY!${NC}"
echo ""
echo "📋 Next actions:"
echo "   • Configure database and update ${ENV_FILE}"
echo "   • Set up SSL certificates (Let's Encrypt)"
echo "   • Configure firewall and security groups"
echo "   • Set up monitoring and alerts"
echo "   • Create backup strategy"
echo ""
echo "🚀 For quick start after configuration:"
echo "   sudo systemctl start ${APP_NAME}"
echo "   sudo journalctl -u ${APP_NAME} -f"
