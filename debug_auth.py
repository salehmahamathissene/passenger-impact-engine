import os
import requests
import json

BASE_URL = "http://127.0.0.1:8080"
COMPANY_ID = os.environ.get("COMPANY_ID")
API_KEY = os.environ.get("API_KEY")

print("🔍 Debugging Authentication")
print("=" * 50)

headers = {"X-Company-Id": COMPANY_ID, "X-Api-Key": API_KEY}

# Test different endpoints
endpoints = [
    "/enterprise/billing/checkout",
    "/enterprise/billing/subscription", 
    "/enterprise/invoices",
    "/enterprise/jobs"
]

print(f"Using Company ID: {COMPANY_ID}")
print(f"Using API Key: {API_KEY[:10]}...")
print()

for endpoint in endpoints:
    if endpoint == "/enterprise/billing/checkout":
        # POST request for checkout
        response = requests.post(
            f"{BASE_URL}{endpoint}",
            headers={**headers, "Content-Type": "application/json"},
            json={"price_id": os.environ.get("STRIPE_PRICE_PRO_MONTHLY", "price_test")},
            timeout=5
        )
    else:
        # GET request for others
        response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=5)
    
    print(f"{endpoint}:")
    print(f"  Status: {response.status_code}")
    
    if response.status_code == 200:
        print(f"  ✅ Success")
        try:
            data = response.json()
            if isinstance(data, list):
                print(f"  Items: {len(data)}")
            elif isinstance(data, dict):
                if 'items' in data:
                    print(f"  Items: {len(data['items'])}")
                elif 'checkout_url' in data:
                    print(f"  Has checkout URL")
        except:
            pass
    elif response.status_code == 401:
        print(f"  ❌ Unauthorized")
        try:
            error = response.json()
            print(f"  Error: {error.get('detail', 'Unknown')}")
        except:
            print(f"  Raw: {response.text[:100]}")
    else:
        print(f"  ⚠️  Status: {response.status_code}")
    
    print()
