# Passenger Impact Engine (PIE)
**Forecast airline disruption cost exposure (EU261 compensation risk) with Monte Carlo simulation.**

PIE helps airline teams answer:
> “If Flight X is delayed/cancelled today, what is our expected compensation exposure — and how bad can it get (P95)?”

## Who this is for
- Operations Control Center (OCC) / Disruption Management
- Risk & Compliance
- Finance / Revenue Management
- Customer Experience (rebooking + compensation exposure)

## What PIE outputs (operator language)
For a disruption scenario, PIE estimates:
- **Expected EU261 compensation exposure (€)**
- **Percentiles (P50 / P95) worst-case exposure (€)**
- Payout distribution (risk curve)
- Scenario comparison (delay vs cancel vs mitigation action)

### Example (illustrative)
- Expected exposure: **€380,000**
- P95 worst-case exposure: **€1,050,000**
- Mitigation scenario savings: **5–8%**

> These are illustrative demo numbers. Replace with your real outputs once the scenario runner is finalized.

## MVP scope (narrow on purpose)
PIE MVP = **EU261 Exposure Forecast** for one disruption event.  
See: `docs/MVP_WORKFLOW.md`

## Docs
- Buyer pitch: `docs/BUYER_PITCH.md`
- MVP workflow: `docs/MVP_WORKFLOW.md`
- Demo output: `docs/DEMO_OUTPUT.md`

## Environment variables
PIE reads secrets from environment variables (never committed to git):

- `STRIPE_SECRET_KEY`
- `STRIPE_PUBLIC_KEY`
- `STRIPE_WEBHOOK_SECRET` (optional)
- `DATABASE_URL` (optional)
- `ADMIN_API_KEY` (optional)

## Quick start (dev)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# run API (adjust command to your entrypoint)
python -m src.pie.main
