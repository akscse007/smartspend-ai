--
-- PostgreSQL database dump
--

\restrict d01daTcf7pKDnuUSeyTDBhmJ03cQr4kTsK7CFkA1sY1NoYJFGn4TchbsjPd0tsR

-- Dumped from database version 18.1
-- Dumped by pg_dump version 18.1

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO postgres;

--
-- Name: budget_recommendations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.budget_recommendations (
    id integer NOT NULL,
    month character varying(7) NOT NULL,
    category character varying(100) NOT NULL,
    current_spend double precision NOT NULL,
    recommended_budget double precision NOT NULL,
    potential_savings double precision NOT NULL,
    advice text NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.budget_recommendations OWNER TO postgres;

--
-- Name: budget_recommendations_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.budget_recommendations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.budget_recommendations_id_seq OWNER TO postgres;

--
-- Name: budget_recommendations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.budget_recommendations_id_seq OWNED BY public.budget_recommendations.id;


--
-- Name: budgets; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.budgets (
    id integer NOT NULL,
    user_id integer NOT NULL,
    category_id integer,
    category character varying(100) NOT NULL,
    monthly_limit double precision NOT NULL,
    month integer NOT NULL,
    year integer NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT budgets_month_check CHECK (((month >= 1) AND (month <= 12)))
);


ALTER TABLE public.budgets OWNER TO postgres;

--
-- Name: budgets_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.budgets_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.budgets_id_seq OWNER TO postgres;

--
-- Name: budgets_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.budgets_id_seq OWNED BY public.budgets.id;


--
-- Name: category_overrides; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.category_overrides (
    id integer NOT NULL,
    transaction_id integer NOT NULL,
    previous_category character varying(100) NOT NULL,
    new_category character varying(100) NOT NULL,
    reason character varying(255) NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.category_overrides OWNER TO postgres;

--
-- Name: category_overrides_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.category_overrides_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.category_overrides_id_seq OWNER TO postgres;

--
-- Name: category_overrides_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.category_overrides_id_seq OWNED BY public.category_overrides.id;


--
-- Name: monthly_summaries; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.monthly_summaries (
    id integer NOT NULL,
    month character varying(7) NOT NULL,
    total_income double precision NOT NULL,
    total_expense double precision NOT NULL,
    net_savings double precision NOT NULL,
    health_score double precision NOT NULL,
    ai_summary text NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.monthly_summaries OWNER TO postgres;

--
-- Name: monthly_summaries_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.monthly_summaries_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.monthly_summaries_id_seq OWNER TO postgres;

--
-- Name: monthly_summaries_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.monthly_summaries_id_seq OWNED BY public.monthly_summaries.id;


--
-- Name: notifications; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.notifications (
    id integer NOT NULL,
    user_id integer NOT NULL,
    type character varying(50) NOT NULL,
    message text NOT NULL,
    is_read boolean DEFAULT false NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.notifications OWNER TO postgres;

--
-- Name: notifications_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.notifications_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.notifications_id_seq OWNER TO postgres;

--
-- Name: notifications_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.notifications_id_seq OWNED BY public.notifications.id;


--
-- Name: savings_goals; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.savings_goals (
    id integer NOT NULL,
    user_id integer NOT NULL,
    target_amount double precision NOT NULL,
    target_date date NOT NULL,
    current_saved double precision DEFAULT 0 NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.savings_goals OWNER TO postgres;

--
-- Name: savings_goals_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.savings_goals_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.savings_goals_id_seq OWNER TO postgres;

--
-- Name: savings_goals_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.savings_goals_id_seq OWNED BY public.savings_goals.id;


--
-- Name: transactions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.transactions (
    id integer NOT NULL,
    date date NOT NULL,
    description character varying(300) NOT NULL,
    clean_description character varying(300) NOT NULL,
    merchant character varying(150) NOT NULL,
    amount double precision NOT NULL,
    currency character varying(10) DEFAULT 'INR'::character varying NOT NULL,
    amount_inr double precision NOT NULL,
    category character varying(100) NOT NULL,
    prediction_confidence double precision DEFAULT 0 NOT NULL,
    is_income boolean DEFAULT false NOT NULL,
    is_subscription boolean DEFAULT false NOT NULL,
    anomaly_flag boolean DEFAULT false NOT NULL,
    recurrence character varying(20) DEFAULT 'none'::character varying NOT NULL,
    source_hash character varying(64) NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    user_id integer NOT NULL
);


ALTER TABLE public.transactions OWNER TO postgres;

--
-- Name: transactions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.transactions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.transactions_id_seq OWNER TO postgres;

--
-- Name: transactions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.transactions_id_seq OWNED BY public.transactions.id;


--
-- Name: user_feedback; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_feedback (
    id integer NOT NULL,
    transaction_id integer,
    transaction_text character varying(300) NOT NULL,
    predicted_category character varying(100) NOT NULL,
    corrected_category character varying(100) NOT NULL,
    created_at timestamp without time zone NOT NULL,
    user_id integer NOT NULL
);


ALTER TABLE public.user_feedback OWNER TO postgres;

--
-- Name: user_feedback_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.user_feedback_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.user_feedback_id_seq OWNER TO postgres;

--
-- Name: user_feedback_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.user_feedback_id_seq OWNED BY public.user_feedback.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id integer NOT NULL,
    full_name character varying(150) NOT NULL,
    email character varying(255) NOT NULL,
    password_hash character varying(255) NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp without time zone NOT NULL
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: budget_recommendations id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.budget_recommendations ALTER COLUMN id SET DEFAULT nextval('public.budget_recommendations_id_seq'::regclass);


--
-- Name: budgets id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.budgets ALTER COLUMN id SET DEFAULT nextval('public.budgets_id_seq'::regclass);


--
-- Name: category_overrides id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.category_overrides ALTER COLUMN id SET DEFAULT nextval('public.category_overrides_id_seq'::regclass);


--
-- Name: monthly_summaries id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.monthly_summaries ALTER COLUMN id SET DEFAULT nextval('public.monthly_summaries_id_seq'::regclass);


--
-- Name: notifications id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notifications ALTER COLUMN id SET DEFAULT nextval('public.notifications_id_seq'::regclass);


--
-- Name: savings_goals id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.savings_goals ALTER COLUMN id SET DEFAULT nextval('public.savings_goals_id_seq'::regclass);


--
-- Name: transactions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transactions ALTER COLUMN id SET DEFAULT nextval('public.transactions_id_seq'::regclass);


--
-- Name: user_feedback id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_feedback ALTER COLUMN id SET DEFAULT nextval('public.user_feedback_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: budget_recommendations budget_recommendations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.budget_recommendations
    ADD CONSTRAINT budget_recommendations_pkey PRIMARY KEY (id);


--
-- Name: budgets budgets_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.budgets
    ADD CONSTRAINT budgets_pkey PRIMARY KEY (id);


--
-- Name: category_overrides category_overrides_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.category_overrides
    ADD CONSTRAINT category_overrides_pkey PRIMARY KEY (id);


--
-- Name: monthly_summaries monthly_summaries_month_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.monthly_summaries
    ADD CONSTRAINT monthly_summaries_month_key UNIQUE (month);


--
-- Name: monthly_summaries monthly_summaries_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.monthly_summaries
    ADD CONSTRAINT monthly_summaries_pkey PRIMARY KEY (id);


--
-- Name: notifications notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_pkey PRIMARY KEY (id);


--
-- Name: savings_goals savings_goals_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.savings_goals
    ADD CONSTRAINT savings_goals_pkey PRIMARY KEY (id);


--
-- Name: transactions transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_pkey PRIMARY KEY (id);


--
-- Name: budget_recommendations uq_budget_month_category; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.budget_recommendations
    ADD CONSTRAINT uq_budget_month_category UNIQUE (month, category);


--
-- Name: budgets uq_budget_user_category_month_year; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.budgets
    ADD CONSTRAINT uq_budget_user_category_month_year UNIQUE (user_id, category, month, year);


--
-- Name: transactions uq_transactions_user_source_hash; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT uq_transactions_user_source_hash UNIQUE (user_id, source_hash);


--
-- Name: user_feedback user_feedback_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_feedback
    ADD CONSTRAINT user_feedback_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: idx_budgets_category; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_budgets_category ON public.budgets USING btree (category);


--
-- Name: idx_budgets_category_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_budgets_category_id ON public.budgets USING btree (category_id);


--
-- Name: idx_budgets_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_budgets_user_id ON public.budgets USING btree (user_id);


--
-- Name: idx_budgets_user_month_year; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_budgets_user_month_year ON public.budgets USING btree (user_id, month, year);


--
-- Name: idx_notifications_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_notifications_created_at ON public.notifications USING btree (created_at);


--
-- Name: idx_notifications_is_read; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_notifications_is_read ON public.notifications USING btree (is_read);


--
-- Name: idx_notifications_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_notifications_type ON public.notifications USING btree (type);


--
-- Name: idx_notifications_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_notifications_user_id ON public.notifications USING btree (user_id);


--
-- Name: idx_notifications_user_read_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_notifications_user_read_created ON public.notifications USING btree (user_id, is_read, created_at);


--
-- Name: idx_savings_goals_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_savings_goals_user_id ON public.savings_goals USING btree (user_id);


--
-- Name: idx_savings_goals_user_target_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_savings_goals_user_target_date ON public.savings_goals USING btree (user_id, target_date);


--
-- Name: idx_transactions_anomaly_flag; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_transactions_anomaly_flag ON public.transactions USING btree (anomaly_flag);


--
-- Name: idx_transactions_category; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_transactions_category ON public.transactions USING btree (category);


--
-- Name: idx_transactions_category_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_transactions_category_date ON public.transactions USING btree (category, date);


--
-- Name: idx_transactions_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_transactions_date ON public.transactions USING btree (date);


--
-- Name: idx_transactions_date_is_income; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_transactions_date_is_income ON public.transactions USING btree (date, is_income);


--
-- Name: idx_transactions_merchant; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_transactions_merchant ON public.transactions USING btree (merchant);


--
-- Name: ix_transactions_user_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_transactions_user_date ON public.transactions USING btree (user_id, date);


--
-- Name: ix_transactions_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_transactions_user_id ON public.transactions USING btree (user_id);


--
-- Name: ix_user_feedback_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_user_feedback_created_at ON public.user_feedback USING btree (created_at);


--
-- Name: ix_user_feedback_transaction_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_user_feedback_transaction_id ON public.user_feedback USING btree (transaction_id);


--
-- Name: ix_user_feedback_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_user_feedback_user_id ON public.user_feedback USING btree (user_id);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: category_overrides category_overrides_transaction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.category_overrides
    ADD CONSTRAINT category_overrides_transaction_id_fkey FOREIGN KEY (transaction_id) REFERENCES public.transactions(id);


--
-- Name: transactions fk_transactions_user_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT fk_transactions_user_id FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: user_feedback fk_user_feedback_user_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_feedback
    ADD CONSTRAINT fk_user_feedback_user_id FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: user_feedback user_feedback_transaction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_feedback
    ADD CONSTRAINT user_feedback_transaction_id_fkey FOREIGN KEY (transaction_id) REFERENCES public.transactions(id);


--
-- PostgreSQL database dump complete
--

\unrestrict d01daTcf7pKDnuUSeyTDBhmJ03cQr4kTsK7CFkA1sY1NoYJFGn4TchbsjPd0tsR

