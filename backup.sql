--
-- PostgreSQL database dump
--

\restrict VxOFa3fR7n56GbpZhnZRl8irlwmWdIhngka9kHp56kH1DasoHnMO97Uw82EU5sE

-- Dumped from database version 16.11 (Ubuntu 16.11-0ubuntu0.24.04.1)
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

SET default_tablespace = '';

SET default_table_access_method = heap;

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
-- Data for Name: jobs; Type: TABLE DATA; Schema: public; Owner: pie
--

COPY public.jobs (id, order_id, created_at, started_at, completed_at, status, artifact_path, error, processing_time_ms, runs_completed) FROM stdin;
1	1	2026-02-06 13:15:50.36521	2026-02-06 13:15:50.36912	2026-02-06 13:15:50.482374	done	artifacts/order_000001/PRO_complete_test_20260206_151550.zip	\N	145	50000
2	3	2026-02-06 13:34:08.507251	2026-02-06 13:34:08.516657	2026-02-06 13:34:08.738367	done	artifacts/order_000003/PRO_pay_test_1770384579_20260206_153408.zip	\N	269	50000
3	2	2026-02-06 13:34:09.188658	2026-02-06 13:34:09.19347	2026-02-06 13:34:09.370057	done	artifacts/order_000002/PRO_test_1770384579_20260206_153409.zip	\N	217	10000
4	4	2026-02-06 13:35:56.378627	2026-02-06 13:35:56.383275	2026-02-06 13:35:56.552687	done	artifacts/order_000004/PRO_airline_20260206_153556.zip	\N	195	50000
5	5	2026-02-06 13:35:56.602547	2026-02-06 13:35:56.606493	2026-02-06 13:35:56.712657	done	artifacts/order_000005/PRO_customer_20260206_153556.zip	\N	137	10000
6	6	2026-02-06 13:38:18.607358	2026-02-06 13:38:18.610511	2026-02-06 13:38:18.716536	done	artifacts/order_000006/PRO_customer_20260206_153818.zip	\N	133	10000
7	16	2026-02-06 14:14:38.81219	2026-02-06 14:14:38.819702	2026-02-06 14:14:39.041959	done	artifacts/order_000016/PRO_business_test__6741769649017155023_20260206_161439.zip	\N	272	50000
8	17	2026-02-06 14:15:04.550887	2026-02-06 14:15:04.556864	2026-02-06 14:15:04.714847	done	artifacts/order_000017/PRO_regional_airline_0_20260206_161504.zip	\N	199	10000
9	19	2026-02-06 14:15:06.156776	2026-02-06 14:15:06.161774	2026-02-06 14:15:06.313102	done	artifacts/order_000019/PRO_international_airline_2_20260206_161506.zip	\N	195	200000
10	22	2026-02-06 14:15:09.289472	2026-02-06 14:15:09.295003	2026-02-06 14:15:09.454418	done	artifacts/order_000022/PRO_cargo_airline_5_20260206_161509.zip	\N	206	50000
11	23	2026-02-06 14:15:10.78957	2026-02-06 14:15:10.796415	2026-02-06 14:15:10.965148	done	artifacts/order_000023/PRO_startup_airline_6_20260206_161510.zip	\N	232	10000
12	24	2026-02-06 14:15:11.741135	2026-02-06 14:15:11.747074	2026-02-06 14:15:11.921769	done	artifacts/order_000024/PRO_charter_airline_7_20260206_161511.zip	\N	217	10000
\.


--
-- Data for Name: orders; Type: TABLE DATA; Schema: public; Owner: pie
--

COPY public.orders (id, created_at, customer_email, plan, amount_cents, currency, status, stripe_payment_intent_id, stripe_checkout_session_id, notes) FROM stdin;
1	2026-02-06 13:15:29.375715	complete_test@bigcorp.com	pro	49900	eur	paid	\N	\N	Complete flow test - should trigger background job
3	2026-02-06 13:29:39.155432	pay_test_1770384579@example.com	pro	49900	eur	paid	\N	\N	\N
2	2026-02-06 13:29:39.142105	test_1770384579@example.com	starter	9900	eur	paid	\N	\N	\N
7	2026-02-06 13:35:06.346282	customer@airline.com	starter	9900	eur	pending	\N	\N	\N
4	2026-02-06 13:30:14.053768	airline@example.com	pro	49900	eur	paid	\N	\N	\N
5	2026-02-06 13:30:42.793409	customer@airline.com	starter	9900	eur	paid	\N	\N	\N
8	2026-02-06 13:38:17.367948	airline@company.com	pro	49900	eur	pending	\N	\N	\N
6	2026-02-06 13:33:07.286013	customer@airline.com	starter	9900	eur	paid	\N	\N	\N
9	2026-02-06 13:39:55.695198	real_customer@airline.com	pro	49900	eur	pending	\N	\N	\N
10	2026-02-06 13:39:55.790732	premium_airline@company.com	enterprise	199900	eur	pending	\N	\N	\N
11	2026-02-06 13:40:45.114732	airline@example.com	pro	49900	eur	pending	\N	\N	\N
12	2026-02-06 13:41:06.442232	customer@email.com	starter	9900	eur	pending	\N	\N	\N
13	2026-02-06 13:41:16.747332	test@example.com	pro	49900	eur	pending	\N	\N	\N
14	2026-02-06 14:12:58.098936	customer@airline.com	starter	9900	eur	pending	\N	\N	\N
15	2026-02-06 14:14:18.321327	test_customer@airline.com	starter	9900	eur	pending	\N	\N	\N
16	2026-02-06 14:14:38.30842	business_test_-6741769649017155023@example.com	pro	49900	eur	paid	\N	\N	\N
17	2026-02-06 14:15:04.147681	regional_airline_0@regionalair.com	starter	9900	eur	paid	\N	\N	\N
18	2026-02-06 14:15:04.733849	startup_airline_1@startupair.com	starter	9900	eur	pending	\N	\N	\N
19	2026-02-06 14:15:05.77837	international_airline_2@globalair.com	enterprise	199900	eur	paid	\N	\N	\N
20	2026-02-06 14:15:06.359349	charter_airline_3@charterair.com	enterprise	199900	eur	pending	\N	\N	\N
21	2026-02-06 14:15:07.327094	charter_airline_4@charterair.com	enterprise	199900	eur	pending	\N	\N	\N
22	2026-02-06 14:15:08.903226	cargo_airline_5@cargoair.com	pro	49900	eur	paid	\N	\N	\N
23	2026-02-06 14:15:10.360535	startup_airline_6@startupair.com	starter	9900	eur	paid	\N	\N	\N
24	2026-02-06 14:15:11.366099	charter_airline_7@charterair.com	starter	9900	eur	paid	\N	\N	\N
25	2026-02-06 14:15:36.697948	airline@example.com	pro	49900	eur	pending	\N	\N	\N
26	2026-02-06 14:20:52.381759	customer@airline.com	pro	49900	eur	pending	\N	\N	\N
\.


--
-- Name: jobs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pie
--

SELECT pg_catalog.setval('public.jobs_id_seq', 12, true);


--
-- Name: orders_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pie
--

SELECT pg_catalog.setval('public.orders_id_seq', 26, true);


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
-- Name: jobs jobs_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pie
--

ALTER TABLE ONLY public.jobs
    ADD CONSTRAINT jobs_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict VxOFa3fR7n56GbpZhnZRl8irlwmWdIhngka9kHp56kH1DasoHnMO97Uw82EU5sE

