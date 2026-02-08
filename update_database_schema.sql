-- ADVANCED BILLING SYSTEM DATABASE SCHEMA
-- Run this to update your database with enterprise features

-- Add ENUM types if they don't exist
DO $$ 
BEGIN
    -- Subscription Status ENUM
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'subscriptionstatus') THEN
        CREATE TYPE subscriptionstatus AS ENUM (
            'trialing',
            'active',
            'past_due',
            'canceled',
            'unpaid',
            'incomplete',
            'incomplete_expired'
        );
    END IF;

    -- Billing Plan ENUM
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'billingplan') THEN
        CREATE TYPE billingplan AS ENUM (
            'free',
            'basic',
            'pro',
            'enterprise'
        );
    END IF;
END $$;

-- Update enterprise_companies table with advanced billing features
ALTER TABLE enterprise_companies 
    ALTER COLUMN plan TYPE billingplan 
    USING CASE 
        WHEN plan = 'free' THEN 'free'::billingplan
        WHEN plan = 'basic' THEN 'basic'::billingplan
        WHEN plan = 'pro' THEN 'pro'::billingplan
        WHEN plan = 'enterprise' THEN 'enterprise'::billingplan
        ELSE 'free'::billingplan
    END;

ALTER TABLE enterprise_companies 
    ALTER COLUMN subscription_status TYPE subscriptionstatus 
    USING subscription_status::subscriptionstatus;

-- Add new billing columns
ALTER TABLE enterprise_companies
    ADD COLUMN IF NOT EXISTS billing_email VARCHAR(200),
    ADD COLUMN IF NOT EXISTS tax_id VARCHAR(100),
    ADD COLUMN IF NOT EXISTS invoice_prefix VARCHAR(10) DEFAULT 'INV',
    ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb;

-- Update enterprise_invoices table with Stripe fields
ALTER TABLE enterprise_invoices
    ADD COLUMN IF NOT EXISTS stripe_invoice_id VARCHAR(255),
    ADD COLUMN IF NOT EXISTS stripe_payment_intent_id VARCHAR(255),
    ADD COLUMN IF NOT EXISTS hosted_invoice_url VARCHAR(500),
    ADD COLUMN IF NOT EXISTS invoice_pdf VARCHAR(500),
    ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb;

-- Update enterprise_orders table with Stripe fields
ALTER TABLE enterprise_orders
    ADD COLUMN IF NOT EXISTS stripe_session_id VARCHAR(255),
    ADD COLUMN IF NOT EXISTS stripe_payment_intent_id VARCHAR(255),
    ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_enterprise_companies_subscription_status 
    ON enterprise_companies(subscription_status);

CREATE INDEX IF NOT EXISTS idx_enterprise_companies_current_period_end 
    ON enterprise_companies(current_period_end);

CREATE INDEX IF NOT EXISTS idx_enterprise_invoices_stripe_invoice_id 
    ON enterprise_invoices(stripe_invoice_id);

CREATE INDEX IF NOT EXISTS idx_enterprise_invoices_status 
    ON enterprise_invoices(status);

-- Create function to generate invoice number
CREATE OR REPLACE FUNCTION generate_invoice_number(
    company_id UUID,
    prefix VARCHAR DEFAULT 'INV'
) RETURNS VARCHAR AS $$
DECLARE
    seq_number INTEGER;
    invoice_number VARCHAR;
    year_month VARCHAR;
BEGIN
    year_month := TO_CHAR(CURRENT_DATE, 'YYYYMM');
    
    -- Get next sequence number for this company/month
    SELECT COALESCE(MAX(SUBSTRING(invoice_number FROM '\d+$')::INTEGER), 0) + 1
    INTO seq_number
    FROM enterprise_invoices
    WHERE company_id = $1
    AND invoice_number LIKE prefix || '-' || year_month || '-%';
    
    invoice_number := prefix || '-' || year_month || '-' || LPAD(seq_number::TEXT, 5, '0');
    
    RETURN invoice_number;
END;
$$ LANGUAGE plpgsql;

-- Create view for subscription analytics
CREATE OR REPLACE VIEW subscription_analytics AS
SELECT 
    c.plan,
    c.subscription_status,
    COUNT(*) as company_count,
    COUNT(CASE WHEN c.current_period_end >= NOW() THEN 1 END) as active_subscriptions,
    COUNT(CASE WHEN c.current_period_end < NOW() THEN 1 END) as expired_subscriptions,
    AVG(EXTRACT(EPOCH FROM (c.updated_at - c.created_at))/86400)::INTEGER as avg_days_active,
    MIN(c.created_at) as first_subscription,
    MAX(c.created_at) as latest_subscription
FROM enterprise_companies c
WHERE c.subscription_status IS NOT NULL
GROUP BY c.plan, c.subscription_status
ORDER BY c.plan, company_count DESC;

-- Create audit trigger for billing changes
CREATE OR REPLACE FUNCTION audit_billing_changes()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'UPDATE' THEN
        IF OLD.plan != NEW.plan OR OLD.subscription_status != NEW.subscription_status THEN
            INSERT INTO billing_audit_log (
                company_id,
                old_plan,
                new_plan,
                old_status,
                new_status,
                changed_at
            ) VALUES (
                NEW.id,
                OLD.plan,
                NEW.plan,
                OLD.subscription_status,
                NEW.subscription_status,
                NOW()
            );
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create billing audit log table
CREATE TABLE IF NOT EXISTS billing_audit_log (
    id SERIAL PRIMARY KEY,
    company_id UUID NOT NULL REFERENCES enterprise_companies(id),
    old_plan billingplan,
    new_plan billingplan,
    old_status subscriptionstatus,
    new_status subscriptionstatus,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create trigger for billing changes
DROP TRIGGER IF EXISTS audit_billing_trigger ON enterprise_companies;
CREATE TRIGGER audit_billing_trigger
    AFTER UPDATE OF plan, subscription_status ON enterprise_companies
    FOR EACH ROW
    EXECUTE FUNCTION audit_billing_changes();

-- Create function to check subscription health
CREATE OR REPLACE FUNCTION check_subscription_health()
RETURNS TABLE(
    company_id UUID,
    legal_name VARCHAR,
    plan billingplan,
    subscription_status subscriptionstatus,
    days_until_end INTEGER,
    health_status VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.id,
        c.legal_name,
        c.plan,
        c.subscription_status,
        CASE 
            WHEN c.current_period_end IS NOT NULL 
            THEN EXTRACT(DAY FROM c.current_period_end - NOW())::INTEGER
            ELSE NULL
        END as days_until_end,
        CASE
            WHEN c.subscription_status = 'active' AND c.current_period_end > NOW() + INTERVAL '7 days' THEN 'healthy'
            WHEN c.subscription_status = 'active' AND c.current_period_end <= NOW() + INTERVAL '7 days' THEN 'expiring_soon'
            WHEN c.subscription_status = 'past_due' THEN 'past_due'
            WHEN c.subscription_status = 'canceled' THEN 'canceled'
            WHEN c.subscription_status = 'unpaid' THEN 'unpaid'
            ELSE 'unknown'
        END as health_status
    FROM enterprise_companies c
    WHERE c.subscription_status IS NOT NULL;
END;
$$ LANGUAGE plpgsql;

-- Update your company to have proper subscription status
UPDATE enterprise_companies 
SET 
    subscription_status = 'active'::subscriptionstatus,
    current_period_end = NOW() + INTERVAL '30 days',
    plan = 'pro'::billingplan
WHERE id = 'fa2a2660-d89a-4437-a6ce-5f60397cf9c7';

-- Verify the update
SELECT 
    id,
    legal_name,
    plan,
    subscription_status,
    current_period_end,
    days_until_end
FROM check_subscription_health();
