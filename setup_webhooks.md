# Setting Up Stripe Webhooks

## Why Webhooks?
Webhooks allow Stripe to notify your server when events happen (payment success, subscription cancelled, etc.).

## Setup Steps:

### 1. Install Stripe CLI (for local testing)
```bash
# Install
curl -s https://stripe.com/docs/stripe-cli#install | bash

# Login
stripe login

# Forward webhooks to your server
stripe listen --forward-to http://localhost:8080/enterprise/billing/webhook
