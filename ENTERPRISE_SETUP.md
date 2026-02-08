# Passenger Impact Engine - Enterprise Setup

## API Base URL
http://127.0.0.1:8080

## Authentication
1. **Admin Key**: $ADMIN_KEY (X-Admin-Key header)
2. **Company API Keys**: Provisioned per company (X-Api-Key header + X-Company-Id)

## Workflow
1. Create company → POST /enterprise/companies
2. Get API key → POST /enterprise/companies/{id}/provision-api-key  
3. Create order → POST /enterprise/orders
4. Create invoice → POST /enterprise/invoices
5. Settle invoice → POST /enterprise/invoices/{id}/settle
6. Update database: mark order.is_paid = True
7. Execute order → POST /enterprise/orders/{id}/execute
8. Check jobs → GET /enterprise/jobs

## Database Notes
- Orders use `is_paid` boolean field (not `status`)
- Invoices link to orders via `invoice_id` field
- Jobs created when orders are executed
