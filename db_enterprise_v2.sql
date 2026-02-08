BEGIN;

CREATE TABLE IF NOT EXISTS enterprise_contracts (
  id uuid PRIMARY KEY,
  company_id uuid NOT NULL REFERENCES enterprise_companies(id) ON DELETE CASCADE,
  contract_number varchar(64) UNIQUE NOT NULL,
  plan varchar(32) NOT NULL DEFAULT 'starter',
  signed_at timestamp without time zone,
  starts_at date NOT NULL DEFAULT CURRENT_DATE,
  ends_at date,
  status varchar(16) NOT NULL DEFAULT 'active',
  created_at timestamp without time zone NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_contracts_company_id ON enterprise_contracts(company_id);

CREATE TABLE IF NOT EXISTS enterprise_jobs (
  id uuid PRIMARY KEY,
  company_id uuid NOT NULL REFERENCES enterprise_companies(id) ON DELETE CASCADE,
  status varchar(16) NOT NULL DEFAULT 'queued',
  created_at timestamp without time zone NOT NULL DEFAULT NOW(),
  started_at timestamp without time zone,
  finished_at timestamp without time zone,
  schedule_blob_path text,
  bookings_blob_path text,
  outputs_prefix text,
  error_message text
);
CREATE INDEX IF NOT EXISTS idx_jobs_company_id_created ON enterprise_jobs(company_id, created_at DESC);

CREATE TABLE IF NOT EXISTS enterprise_invoices (
  id uuid PRIMARY KEY,
  company_id uuid NOT NULL REFERENCES enterprise_companies(id) ON DELETE CASCADE,
  job_id uuid REFERENCES enterprise_jobs(id) ON DELETE SET NULL,
  invoice_number varchar(64) UNIQUE NOT NULL,
  amount_eur numeric(14,2) NOT NULL DEFAULT 0.00,
  currency varchar(8) NOT NULL DEFAULT 'EUR',
  status varchar(16) NOT NULL DEFAULT 'draft',
  issued_at timestamp without time zone,
  created_at timestamp without time zone NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_invoices_company_id_created ON enterprise_invoices(company_id, created_at DESC);

COMMIT;

