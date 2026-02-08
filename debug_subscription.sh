#!/bin/bash
echo "🔧 DEBUGGING SUBSCRIPTION ISSUE"
echo "================================"

echo ""
echo "1️⃣ Checking company in database..."
python3 -c "
import os, sys
sys.path.append('$PWD/src')
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv('.env.working')
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///./pie.db')
engine = create_engine(DATABASE_URL)

company_id = os.environ.get('COMPANY_ID')
api_key = os.environ.get('API_KEY')

with engine.connect() as conn:
    # Check company
    result = conn.execute(
        text('SELECT id, name, stripe_customer_id FROM enterprise_companies WHERE id = :id'),
        {'id': company_id}
    ).fetchone()
    print('Company:', result)
    
    # Check subscription
    result = conn.execute(
        text('SELECT * FROM enterprise_subscriptions WHERE company_id = :id'),
        {'id': company_id}
    ).fetchone()
    print('Subscription:', result)
"

echo ""
echo "2️⃣ Testing billing routes directly..."
python3 -c "
import os, sys
sys.path.append('$PWD/src')
from fastapi.testclient import TestClient
from pie.api.app import app

client = TestClient(app)
headers = {
    'X-Company-Id': os.environ.get('COMPANY_ID'),
    'X-Api-Key': os.environ.get('API_KEY')
}

response = client.get('/enterprise/billing/subscription', headers=headers)
print('Subscription response:', response.json())
"
