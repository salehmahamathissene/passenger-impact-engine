BEGIN;

-- 1) Jobs (simulation runs)
CREATE TABLE IF NOT EXISTS enterprise_jobs (
  id uuid PRIMARY KEY,
  company_id uuid NOT NULL REFERENCES enterprise_companies(id) ON DELETE CASCADE,
  status varchar(20) NOT NULL DEFAULT 'queued', -- queued|running|succeeded|failed
  uploaded_schedule_blob text,
  uploaded_bookings_blob text,
  result_kpi_blob text,
  result_pdf_blob text,
  recommended_actions_blob text,
  error text,
  created_at timestamp without time zone NOT NULL DEFAULT now(),
  updated_at timestamp without time zone NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_jobs_company_created ON enterprise_jobs(company_id, created_at DESC);

-- 2) Contracts
CREATE TABLE IF NOT EXISTS enterprise_contracts (
  id uuid PRIMARY KEY,
  company_id uuid NOT NULL REFERENCES enterprise_companies(id) ON DELETE CASCADE,
  contract_number varchar(50) UNIQUE NOT NULL,
  status varchar(20) NOT NULL DEFAULT 'active', -- active|paused|ended
  price_per_job_eur numeric(14,2) NOT NULL DEFAULT 250.00,
  created_at timestamp without time zone NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_contracts_company ON enterprise_contracts(company_id);

-- 3) Invoices (simple)
CREATE TABLE IF NOT EXISTS enterprise_invoices (
  id uuid PRIMARY KEY,
  company_id uuid NOT NULL REFERENCES enterprise_companies(id) ON DELETE CASCADE,
  invoice_number varchar(50) UNIQUE NOT NULL,
  job_id uuid REFERENCES enterprise_jobs(id) ON DELETE SET NULL,
  amount_eur numeric(14,2) NOT NULL,
  status varchar(20) NOT NULL DEFAULT 'draft', -- draft|issued|paid|void
  created_at timestamp without time zone NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_invoices_company_created ON enterprise_invoices(company_id, created_at DESC);

COMMIT;
