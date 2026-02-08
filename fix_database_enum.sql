-- FIX DATABASE ENUM ISSUES - REAL FIX

-- First, drop the view that's causing issues
DROP VIEW IF EXISTS subscription_analytics;

-- Drop the trigger
DROP TRIGGER IF EXISTS audit_billing_trigger ON enterprise_companies;
DROP FUNCTION IF EXISTS audit_billing_changes();

-- Drop the function that depends on the type
DROP FUNCTION IF EXISTS check_subscription_health();

-- Now we can alter the type
-- First add 'free' to the enum if it doesn't exist
ALTER TYPE subscriptionstatus ADD VALUE IF NOT EXISTS 'free';

-- Update the table to use the enum
UPDATE enterprise_companies 
SET subscription_status = 'free'::subscriptionstatus 
WHERE subscription_status IS NULL OR subscription_status = '';

ALTER TABLE enterprise_companies 
ALTER COLUMN subscription_status TYPE subscriptionstatus 
USING subscription_status::subscriptionstatus;

-- Recreate the functions and views
CREATE OR REPLACE FUNCTION check_subscription_health()
RETURNS TABLE(
    company_id UUID,
    legal_name VARCHAR,
    plan VARCHAR,
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
            WHEN c.subscription_status = 'free' THEN 'free'
            ELSE 'unknown'
        END as health_status
    FROM enterprise_companies c
    WHERE c.subscription_status IS NOT NULL;
END;
$$ LANGUAGE plpgsql;

-- Recreate view
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

-- Update your company to proper status
UPDATE enterprise_companies 
SET 
    subscription_status = 'active'::subscriptionstatus,
    plan = 'pro',
    current_period_end = NOW() + INTERVAL '30 days'
WHERE id = 'fa2a2660-d89a-4437-a6ce-5f60397cf9c7';

-- Verify
SELECT * FROM check_subscription_health();
