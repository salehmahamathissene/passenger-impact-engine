import os
import requests
import json

BASE_URL = "http://127.0.0.1:8080"
COMPANY_ID = os.environ.get("COMPANY_ID")
API_KEY = os.environ.get("API_KEY")

headers = {"X-Company-Id": COMPANY_ID, "X-Api-Key": API_KEY}

# Get company info
response = requests.get(f"{BASE_URL}/enterprise/company", headers=headers)
if response.status_code == 200:
    company = response.json()
    print(f"🏢 Company: {company.get('legal_name', 'Unknown')}")
    print(f"   ID: {company.get('id')}")
    print(f"   Email: {company.get('contact_email', 'No email')}")
    print(f"   Stripe Customer ID: {company.get('stripe_customer_id', 'None')}")
else:
    print(f"❌ Failed to get company: {response.status_code}")
    print(response.text)
