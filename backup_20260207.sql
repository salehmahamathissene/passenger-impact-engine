--
-- PostgreSQL database dump
--

\restrict cI4aibwPnV6cawbKaI32nv6pzPg5AZB95aPFT4mOk6fLqoIGs8Z8cmpGubP0oMp

-- Dumped from database version 16.11 (Debian 16.11-1.pgdg13+1)
-- Dumped by pg_dump version 16.11 (Ubuntu 16.11-0ubuntu0.24.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: billingcycle; Type: TYPE; Schema: public; Owner: pie
--

CREATE TYPE public.billingcycle AS ENUM (
    'monthly',
    'yearly'
);


ALTER TYPE public.billingcycle OWNER TO pie;

--
-- Name: companytier; Type: TYPE; Schema: public; Owner: pie
--

CREATE TYPE public.companytier AS ENUM (
    'small',
    'mid',
    'large'
);


ALTER TYPE public.companytier OWNER TO pie;

--
-- Name: contractstatus; Type: TYPE; Schema: public; Owner: pie
--

CREATE TYPE public.contractstatus AS ENUM (
    'draft',
    'active',
    'suspended',
    'terminated',
    'expired'
);


ALTER TYPE public.contractstatus OWNER TO pie;

--
-- Name: enterpriseorderstatus; Type: TYPE; Schema: public; Owner: pie
--

CREATE TYPE public.enterpriseorderstatus AS ENUM (
    'created',
    'approved',
    'running',
    'done',
    'failed'
);


ALTER TYPE public.enterpriseorderstatus OWNER TO pie;

--
-- Name: industrytype; Type: TYPE; Schema: public; Owner: pie
--

CREATE TYPE public.industrytype AS ENUM (
    'airline',
    'airport',
    'ground_handler',
    'other'
);


ALTER TYPE public.industrytype OWNER TO pie;

--
-- Name: invoicestatus; Type: TYPE; Schema: public; Owner: pie
--

CREATE TYPE public.invoicestatus AS ENUM (
    'draft',
    'sent',
    'paid',
    'overdue',
    'void'
);


ALTER TYPE public.invoicestatus OWNER TO pie;

--
-- Name: jobstatus; Type: TYPE; Schema: public; Owner: pie
--

CREATE TYPE public.jobstatus AS ENUM (
    'queued',
    'running',
    'done',
    'failed'
);


ALTER TYPE public.jobstatus OWNER TO pie;

--
-- Name: orderstatus; Type: TYPE; Schema: public; Owner: pie
--

CREATE TYPE public.orderstatus AS ENUM (
    'pending',
    'paid',
    'sponsored',
    'failed'
);


ALTER TYPE public.orderstatus OWNER TO pie;

--
-- Name: paymentmethod; Type: TYPE; Schema: public; Owner: pie
--

CREATE TYPE public.paymentmethod AS ENUM (
    'invoice',
    'card',
    'bank_transfer'
);


ALTER TYPE public.paymentmethod OWNER TO pie;

--
-- Name: subscriptionplan; Type: TYPE; Schema: public; Owner: pie
--

CREATE TYPE public.subscriptionplan AS ENUM (
    'basic',
    'pro',
    'enterprise'
);


ALTER TYPE public.subscriptionplan OWNER TO pie;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: pie
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO pie;

--
-- Name: enterprise_companies; Type: TABLE; Schema: public; Owner: pie
--

CREATE TABLE public.enterprise_companies (
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    legal_name character varying(200) NOT NULL,
    trading_name character varying(200),
    company_number character varying(50),
    vat_number character varying(50),
    tier public.companytier NOT NULL,
    industry public.industrytype NOT NULL,
    website character varying(200),
    phone character varying(50),
    support_email character varying(320),
    billing_email character varying(320),
    country character varying(100),
    employee_count integer,
    annual_revenue_eur numeric(14,2),
    is_active boolean NOT NULL,
    is_verified boolean NOT NULL,
    total_spent numeric(14,2) NOT NULL,
    notes text,
    api_key_hash character varying(255)
);


ALTER TABLE public.enterprise_companies OWNER TO pie;

--
-- Name: enterprise_contacts; Type: TABLE; Schema: public; Owner: pie
--

CREATE TABLE public.enterprise_contacts (
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    company_id uuid NOT NULL,
    first_name character varying(100) NOT NULL,
    last_name character varying(100) NOT NULL,
    email character varying(320) NOT NULL,
    phone character varying(50),
    mobile character varying(50),
    job_title character varying(100),
    department character varying(100),
    is_primary boolean NOT NULL,
    is_technical boolean NOT NULL,
    is_billing boolean NOT NULL,
    can_receive_emails boolean NOT NULL,
    can_receive_sms boolean NOT NULL
);


ALTER TABLE public.enterprise_contacts OWNER TO pie;

--
-- Name: enterprise_contracts; Type: TABLE; Schema: public; Owner: pie
--

CREATE TABLE public.enterprise_contracts (
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    company_id uuid NOT NULL,
    contract_number character varying(40) NOT NULL,
    status public.contractstatus NOT NULL,
    plan public.subscriptionplan NOT NULL,
    billing_cycle public.billingcycle NOT NULL,
    payment_method public.paymentmethod NOT NULL,
    monthly_rate_eur numeric(12,2) NOT NULL,
    setup_fee_eur numeric(12,2) NOT NULL,
    discount_percentage numeric(5,2) NOT NULL,
    start_date timestamp without time zone NOT NULL,
    end_date timestamp without time zone,
    auto_renew boolean NOT NULL,
    renewal_notice_days integer NOT NULL,
    max_monthly_simulations integer NOT NULL,
    max_concurrent_jobs integer NOT NULL,
    priority_support boolean NOT NULL,
    dedicated_account_manager boolean NOT NULL,
    sla_response_time_hours integer NOT NULL,
    sla_uptime_percentage numeric(5,2) NOT NULL
);


ALTER TABLE public.enterprise_contracts OWNER TO pie;

--
-- Name: enterprise_invoices; Type: TABLE; Schema: public; Owner: pie
--

CREATE TABLE public.enterprise_invoices (
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    company_id uuid NOT NULL,
    invoice_number character varying(40) NOT NULL,
    status public.invoicestatus NOT NULL,
    invoice_date timestamp without time zone NOT NULL,
    due_date timestamp without time zone NOT NULL,
    subtotal_eur numeric(12,2) NOT NULL,
    tax_rate numeric(5,2) NOT NULL,
    tax_number character varying(50),
    total_eur numeric(12,2) NOT NULL,
    line_items json NOT NULL,
    notes text,
    paid_at timestamp without time zone
);


ALTER TABLE public.enterprise_invoices OWNER TO pie;

--
-- Name: enterprise_jobs; Type: TABLE; Schema: public; Owner: pie
--

CREATE TABLE public.enterprise_jobs (
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    order_id uuid NOT NULL,
    status public.enterpriseorderstatus NOT NULL,
    artifact_path character varying(500),
    error text,
    processing_time_ms integer,
    runs_completed integer
);


ALTER TABLE public.enterprise_jobs OWNER TO pie;

--
-- Name: enterprise_orders; Type: TABLE; Schema: public; Owner: pie
--

CREATE TABLE public.enterprise_orders (
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    company_id uuid NOT NULL,
    contract_id uuid,
    description character varying(500) NOT NULL,
    simulation_type character varying(100) NOT NULL,
    iterations integer NOT NULL,
    priority integer NOT NULL,
    amount_eur numeric(12,2) NOT NULL,
    currency character varying(3) NOT NULL,
    parameters json NOT NULL,
    status public.enterpriseorderstatus NOT NULL
);


ALTER TABLE public.enterprise_orders OWNER TO pie;

--
-- Name: jobs; Type: TABLE; Schema: public; Owner: pie
--

CREATE TABLE public.jobs (
    id integer NOT NULL,
    order_id integer NOT NULL,
    created_at timestamp without time zone NOT NULL,
    started_at timestamp without time zone,
    completed_at timestamp without time zone,
    status public.jobstatus NOT NULL,
    artifact_path text,
    error text,
    processing_time_ms integer,
    runs_completed integer
);


ALTER TABLE public.jobs OWNER TO pie;

--
-- Name: jobs_id_seq; Type: SEQUENCE; Schema: public; Owner: pie
--

CREATE SEQUENCE public.jobs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.jobs_id_seq OWNER TO pie;

--
-- Name: jobs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pie
--

ALTER SEQUENCE public.jobs_id_seq OWNED BY public.jobs.id;


--
-- Name: orders; Type: TABLE; Schema: public; Owner: pie
--

CREATE TABLE public.orders (
    id integer NOT NULL,
    created_at timestamp without time zone NOT NULL,
    customer_email character varying(320) NOT NULL,
    plan character varying(50) NOT NULL,
    amount_cents integer NOT NULL,
    currency character varying(3) NOT NULL,
    status public.orderstatus NOT NULL,
    stripe_payment_intent_id character varying(100),
    stripe_checkout_session_id character varying(100),
    notes text
);


ALTER TABLE public.orders OWNER TO pie;

--
-- Name: orders_id_seq; Type: SEQUENCE; Schema: public; Owner: pie
--

CREATE SEQUENCE public.orders_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.orders_id_seq OWNER TO pie;

--
-- Name: orders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pie
--

ALTER SEQUENCE public.orders_id_seq OWNED BY public.orders.id;


--
-- Name: jobs id; Type: DEFAULT; Schema: public; Owner: pie
--

ALTER TABLE ONLY public.jobs ALTER COLUMN id SET DEFAULT nextval('public.jobs_id_seq'::regclass);


--
-- Name: orders id; Type: DEFAULT; Schema: public; Owner: pie
--

ALTER TABLE ONLY public.orders ALTER COLUMN id SET DEFAULT nextval('public.orders_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: pie
--

COPY public.alembic_version (version_num) FROM stdin;
036e05f877c7
\.


--
-- Data for Name: enterprise_companies; Type: TABLE DATA; Schema: public; Owner: pie
--

COPY public.enterprise_companies (id, created_at, updated_at, legal_name, trading_name, company_number, vat_number, tier, industry, website, phone, support_email, billing_email, country, employee_count, annual_revenue_eur, is_active, is_verified, total_spent, notes, api_key_hash) FROM stdin;
fd182a4b-ce5f-4871-870e-b32688474984	2026-02-07 12:08:32.571418	2026-02-07 13:08:39.192865	SALEH	\N	\N	\N	small	airline	\N	\N	\N	\N	\N	\N	\N	t	f	0.00	\N	de556e7e39e292fb526843cea92c360cfcfe21494a43ec52ee6f8f79b517f74d
\.


--
-- Data for Name: enterprise_contacts; Type: TABLE DATA; Schema: public; Owner: pie
--

COPY public.enterprise_contacts (id, created_at, company_id, first_name, last_name, email, phone, mobile, job_title, department, is_primary, is_technical, is_billing, can_receive_emails, can_receive_sms) FROM stdin;
\.


--
-- Data for Name: enterprise_contracts; Type: TABLE DATA; Schema: public; Owner: pie
--

COPY public.enterprise_contracts (id, created_at, updated_at, company_id, contract_number, status, plan, billing_cycle, payment_method, monthly_rate_eur, setup_fee_eur, discount_percentage, start_date, end_date, auto_renew, renewal_notice_days, max_monthly_simulations, max_concurrent_jobs, priority_support, dedicated_account_manager, sla_response_time_hours, sla_uptime_percentage) FROM stdin;
\.


--
-- Data for Name: enterprise_invoices; Type: TABLE DATA; Schema: public; Owner: pie
--

COPY public.enterprise_invoices (id, created_at, company_id, invoice_number, status, invoice_date, due_date, subtotal_eur, tax_rate, tax_number, total_eur, line_items, notes, paid_at) FROM stdin;
\.


--
-- Data for Name: enterprise_jobs; Type: TABLE DATA; Schema: public; Owner: pie
--

COPY public.enterprise_jobs (id, created_at, updated_at, order_id, status, artifact_path, error, processing_time_ms, runs_completed) FROM stdin;
\.


--
-- Data for Name: enterprise_orders; Type: TABLE DATA; Schema: public; Owner: pie
--

COPY public.enterprise_orders (id, created_at, company_id, contract_id, description, simulation_type, iterations, priority, amount_eur, currency, parameters, status) FROM stdin;
\.


--
-- Data for Name: jobs; Type: TABLE DATA; Schema: public; Owner: pie
--

COPY public.jobs (id, order_id, created_at, started_at, completed_at, status, artifact_path, error, processing_time_ms, runs_completed) FROM stdin;
\.


--
-- Data for Name: orders; Type: TABLE DATA; Schema: public; Owner: pie
--

COPY public.orders (id, created_at, customer_email, plan, amount_cents, currency, status, stripe_payment_intent_id, stripe_checkout_session_id, notes) FROM stdin;
\.


--
-- Name: jobs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pie
--

SELECT pg_catalog.setval('public.jobs_id_seq', 1, false);


--
-- Name: orders_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pie
--

SELECT pg_catalog.setval('public.orders_id_seq', 1, false);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: pie
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: enterprise_companies enterprise_companies_company_number_key; Type: CONSTRAINT; Schema: public; Owner: pie
--

ALTER TABLE ONLY public.enterprise_companies
    ADD CONSTRAINT enterprise_companies_company_number_key UNIQUE (company_number);


--
-- Name: enterprise_companies enterprise_companies_legal_name_key; Type: CONSTRAINT; Schema: public; Owner: pie
--

ALTER TABLE ONLY public.enterprise_companies
    ADD CONSTRAINT enterprise_companies_legal_name_key UNIQUE (legal_name);


--
-- Name: enterprise_companies enterprise_companies_pkey; Type: CONSTRAINT; Schema: public; Owner: pie
--

ALTER TABLE ONLY public.enterprise_companies
    ADD CONSTRAINT enterprise_companies_pkey PRIMARY KEY (id);


--
-- Name: enterprise_companies enterprise_companies_vat_number_key; Type: CONSTRAINT; Schema: public; Owner: pie
--

ALTER TABLE ONLY public.enterprise_companies
    ADD CONSTRAINT enterprise_companies_vat_number_key UNIQUE (vat_number);


--
-- Name: enterprise_contacts enterprise_contacts_pkey; Type: CONSTRAINT; Schema: public; Owner: pie
--

ALTER TABLE ONLY public.enterprise_contacts
    ADD CONSTRAINT enterprise_contacts_pkey PRIMARY KEY (id);


--
-- Name: enterprise_contracts enterprise_contracts_contract_number_key; Type: CONSTRAINT; Schema: public; Owner: pie
--

ALTER TABLE ONLY public.enterprise_contracts
    ADD CONSTRAINT enterprise_contracts_contract_number_key UNIQUE (contract_number);


--
-- Name: enterprise_contracts enterprise_contracts_pkey; Type: CONSTRAINT; Schema: public; Owner: pie
--

ALTER TABLE ONLY public.enterprise_contracts
    ADD CONSTRAINT enterprise_contracts_pkey PRIMARY KEY (id);


--
-- Name: enterprise_invoices enterprise_invoices_invoice_number_key; Type: CONSTRAINT; Schema: public; Owner: pie
--

ALTER TABLE ONLY public.enterprise_invoices
    ADD CONSTRAINT enterprise_invoices_invoice_number_key UNIQUE (invoice_number);


--
-- Name: enterprise_invoices enterprise_invoices_pkey; Type: CONSTRAINT; Schema: public; Owner: pie
--

ALTER TABLE ONLY public.enterprise_invoices
    ADD CONSTRAINT enterprise_invoices_pkey PRIMARY KEY (id);


--
-- Name: enterprise_jobs enterprise_jobs_order_id_key; Type: CONSTRAINT; Schema: public; Owner: pie
--

ALTER TABLE ONLY public.enterprise_jobs
    ADD CONSTRAINT enterprise_jobs_order_id_key UNIQUE (order_id);


--
-- Name: enterprise_jobs enterprise_jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: pie
--

ALTER TABLE ONLY public.enterprise_jobs
    ADD CONSTRAINT enterprise_jobs_pkey PRIMARY KEY (id);


--
-- Name: enterprise_orders enterprise_orders_pkey; Type: CONSTRAINT; Schema: public; Owner: pie
--

ALTER TABLE ONLY public.enterprise_orders
    ADD CONSTRAINT enterprise_orders_pkey PRIMARY KEY (id);


--
-- Name: jobs jobs_order_id_key; Type: CONSTRAINT; Schema: public; Owner: pie
--

ALTER TABLE ONLY public.jobs
    ADD CONSTRAINT jobs_order_id_key UNIQUE (order_id);


--
-- Name: jobs jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: pie
--

ALTER TABLE ONLY public.jobs
    ADD CONSTRAINT jobs_pkey PRIMARY KEY (id);


--
-- Name: orders orders_pkey; Type: CONSTRAINT; Schema: public; Owner: pie
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_pkey PRIMARY KEY (id);


--
-- Name: enterprise_contacts enterprise_contacts_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pie
--

ALTER TABLE ONLY public.enterprise_contacts
    ADD CONSTRAINT enterprise_contacts_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.enterprise_companies(id);


--
-- Name: enterprise_contracts enterprise_contracts_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pie
--

ALTER TABLE ONLY public.enterprise_contracts
    ADD CONSTRAINT enterprise_contracts_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.enterprise_companies(id);


--
-- Name: enterprise_invoices enterprise_invoices_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pie
--

ALTER TABLE ONLY public.enterprise_invoices
    ADD CONSTRAINT enterprise_invoices_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.enterprise_companies(id);


--
-- Name: enterprise_jobs enterprise_jobs_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pie
--

ALTER TABLE ONLY public.enterprise_jobs
    ADD CONSTRAINT enterprise_jobs_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.enterprise_orders(id);


--
-- Name: enterprise_orders enterprise_orders_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pie
--

ALTER TABLE ONLY public.enterprise_orders
    ADD CONSTRAINT enterprise_orders_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.enterprise_companies(id);


--
-- Name: enterprise_orders enterprise_orders_contract_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pie
--

ALTER TABLE ONLY public.enterprise_orders
    ADD CONSTRAINT enterprise_orders_contract_id_fkey FOREIGN KEY (contract_id) REFERENCES public.enterprise_contracts(id);


--
-- Name: jobs jobs_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pie
--

ALTER TABLE ONLY public.jobs
    ADD CONSTRAINT jobs_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict cI4aibwPnV6cawbKaI32nv6pzPg5AZB95aPFT4mOk6fLqoIGs8Z8cmpGubP0oMp

