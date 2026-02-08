-- Fix the enterprise_jobs table
ALTER TABLE enterprise_jobs 
DROP COLUMN IF EXISTS company_id,
ADD COLUMN IF NOT EXISTS company_id uuid REFERENCES enterprise_companies(id) ON DELETE CASCADE;

-- Fix the enterprise_invoices table
CREATE TABLE IF NOT EXISTS enterprise_invoices (
    id uuid PRIMARY KEY,
    company_id uuid NOT NULL REFERENCES enterprise_companies(id) ON DELETE CASCADE,
    invoice_number varchar(100) UNIQUE NOT NULL,
    amount_eur decimal(12,2) NOT NULL DEFAULT 0,
    period_start date NOT NULL,
    period_end date NOT NULL,
    status varchar(16) NOT NULL DEFAULT 'draft',
    created_at timestamp without time zone NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_invoices_company ON enterprise_invoices(company_id);
CREATE INDEX IF NOT EXISTS idx_invoices_created ON enterprise_invoices(created_at DESC);
