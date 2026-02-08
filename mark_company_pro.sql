UPDATE enterprise_companies
SET plan='pro',
    stripe_customer_id=:cus,
    stripe_subscription_id=:sub,
    current_period_end=to_timestamp(:cpe)
WHERE id=:company_id;
