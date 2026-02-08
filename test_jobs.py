import requests
import json

url = "http://127.0.0.1:8080/enterprise/jobs"
headers = {
    "X-Company-Id": "$COMPANY_ID",
    "X-Api-Key": "$API_KEY"
}

try:
    response = requests.get(url, headers=headers, timeout=5)
    print(f"Status: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print(f"Response text (first 500 chars):")
    print(response.text[:500])
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
