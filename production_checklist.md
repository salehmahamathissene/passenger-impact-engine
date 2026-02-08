# Production Checklist

## Before Going Live:

### 1. Stripe Configuration
- [ ] Switch from test to live API keys
- [ ] Update webhook endpoint to production URL
- [ ] Set up proper webhook signing secret
- [ ] Configure success/cancel URLs

### 2. Environment Variables (Production)
```bash
# .env.production
export STRIPE_SECRET_KEY="sk_live_..."
export STRIPE_WEBHOOK_SECRET="whsec_REDACTED_..."
export FRONTEND_BASE_URL="https://yourdomain.com"
export STRIPE_PRICE_PRO_MONTHLY="price_live_..."
