# Passenger Impact Engine API

## Quick Start
```bash
curl -X POST https://api.passengerimpact.com/enterprise/companies \
  -H "X-Admin-Key: your-key" \
  -F "legal_name=Your Airline" \
  -F "tier=mid" \
  -F "industry=airline"
