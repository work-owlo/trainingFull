DROP SCHEMA public CASCADE;
CREATE SCHEMA public;

CREATE TABLE IF NOT EXISTS public.auth_token
(
    id integer NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1 ),
    refresh_token text COLLATE pg_catalog."default" NOT NULL,
    access_token text COLLATE pg_catalog."default" NOT NULL,
    updated timestamp without time zone,
    CONSTRAINT auth_token_pkey PRIMARY KEY (id)
)

CREATE TABLE IF NOT EXISTS public.company
(
    id integer NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1 ),
    company_id text COLLATE pg_catalog."default" NOT NULL,
    company_name text COLLATE pg_catalog."default" NOT NULL,
    company_description text COLLATE pg_catalog."default" NOT NULL,
    status text COLLATE pg_catalog."default" NOT NULL,
    created timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT company_pkey PRIMARY KEY (id)
)

CREATE TABLE IF NOT EXISTS public.employee_user
(
    id integer NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1 ),
    user_id text COLLATE pg_catalog."default" NOT NULL,
    first_name text COLLATE pg_catalog."default" NOT NULL,
    last_name text COLLATE pg_catalog."default" NOT NULL,
    email text COLLATE pg_catalog."default" NOT NULL,
    status text COLLATE pg_catalog."default" NOT NULL,
    created timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT employee_user_pkey PRIMARY KEY (id)
)

CREATE TABLE IF NOT EXISTS public.invoice
(
    id integer NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1 ),
    invoice_id text COLLATE pg_catalog."default" NOT NULL,
    invoice_month integer NOT NULL,
    invoice_year integer NOT NULL,
    company_id text COLLATE pg_catalog."default" NOT NULL,
    compensation double precision NOT NULL,
    invoice_amount double precision NOT NULL,
    status text COLLATE pg_catalog."default" NOT NULL,
    created timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT invoice_pkey PRIMARY KEY (id)
)


CREATE TABLE IF NOT EXISTS public.job_roles
(
    id integer NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1 ),
    company_id text COLLATE pg_catalog."default" NOT NULL,
    role_id text COLLATE pg_catalog."default" NOT NULL,
    role_name text COLLATE pg_catalog."default" NOT NULL,
    role_description text COLLATE pg_catalog."default" NOT NULL,
    status text COLLATE pg_catalog."default" NOT NULL,
    created timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    completion_rate double precision,
    average_score double precision,
    average_time double precision,
    CONSTRAINT job_roles_pkey PRIMARY KEY (id)
)

CREATE TABLE IF NOT EXISTS public.manager_permissions
(
    id integer NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1 ),
    user_id text COLLATE pg_catalog."default" NOT NULL,
    add_managers boolean DEFAULT false,
    edit_managers boolean DEFAULT false,
    delete_managers boolean DEFAULT false,
    read_managers boolean DEFAULT false,
    add_roles boolean DEFAULT false,
    edit_roles boolean DEFAULT false,
    delete_roles boolean DEFAULT false,
    add_shifts boolean DEFAULT false,
    edit_shifts boolean DEFAULT false,
    delete_shifts boolean DEFAULT false,
    edit_company boolean DEFAULT false,
    delete_company boolean DEFAULT false,
    created timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT manager_permissions_pkey PRIMARY KEY (id)
)


CREATE TABLE IF NOT EXISTS public.manager_user
(
    id integer NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1 ),
    user_id text COLLATE pg_catalog."default" NOT NULL,
    company_id text COLLATE pg_catalog."default",
    first_name text COLLATE pg_catalog."default" NOT NULL,
    last_name text COLLATE pg_catalog."default" NOT NULL,
    email text COLLATE pg_catalog."default" NOT NULL,
    status text COLLATE pg_catalog."default" NOT NULL,
    created timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT manager_user_pkey PRIMARY KEY (id)
)

DROP TABLE IF EXISTS module;
CREATE TABLE module
(
    id SERIAL PRIMARY KEY,
    module_id TEXT NOT NULL,
    company_id TEXT NOT NULL,
    module_title TEXT NOT NULL,
    module_description TEXT NOT NULL,
    tool_id TEXT NOT NULL,
    access TEXT NOT NULL,
    module_text TEXT,
    num_chats TEXT,
    customer TEXT,
    situation TEXT,
    problem TEXT,
    respond TEXT,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.role_module
(
    id integer NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1 ),
    module_id text COLLATE pg_catalog."default" NOT NULL,
    role_id text COLLATE pg_catalog."default" NOT NULL,
    status text COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT role_module_pkey PRIMARY KEY (id)
)

CREATE TABLE IF NOT EXISTS public.role_tools
(
    id integer NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1 ),
    role_id text COLLATE pg_catalog."default" NOT NULL,
    tool_id text COLLATE pg_catalog."default" NOT NULL,
    status text COLLATE pg_catalog."default" NOT NULL,
    rt_id text COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT role_tools_pkey PRIMARY KEY (id)
)

CREATE TABLE IF NOT EXISTS public.section
(
    id integer NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1 ),
    section_id text COLLATE pg_catalog."default" NOT NULL,
    module_id text COLLATE pg_catalog."default" NOT NULL,
    section_title text COLLATE pg_catalog."default" NOT NULL,
    section_description text COLLATE pg_catalog."default" NOT NULL,
    minutes_to_complete double precision NOT NULL,
    training_order integer NOT NULL,
    created timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT section_pkey PRIMARY KEY (id)
)

CREATE TABLE IF NOT EXISTS public.team
(
    employee_id text COLLATE pg_catalog."default",
    company_id text COLLATE pg_catalog."default",
    role_id text COLLATE pg_catalog."default" NOT NULL,
    employment_type text COLLATE pg_catalog."default" NOT NULL,
    status text COLLATE pg_catalog."default" NOT NULL,
    created timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    id_input text COLLATE pg_catalog."default",
    first_name text COLLATE pg_catalog."default",
    last_name text COLLATE pg_catalog."default",
    email text COLLATE pg_catalog."default" NOT NULL,
    id integer NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1 ),
    team_id text COLLATE pg_catalog."default",
    CONSTRAINT team_pkey PRIMARY KEY (id)
)

CREATE TABLE IF NOT EXISTS public.tools
(
    id integer NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1 ),
    tool_id text COLLATE pg_catalog."default" NOT NULL,
    tool_name text COLLATE pg_catalog."default" NOT NULL,
    tool_icon text COLLATE pg_catalog."default" NOT NULL,
    status text COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT tools_pkey PRIMARY KEY (id)
)

DROP TABLE IF EXISTS training;
CREATE TABLE training (
    id SERIAL PRIMARY KEY,
    training_id TEXT NOT NULL,
    team_id TEXT NOT NULL,
    module_id TEXT NOT NULL,
    query_id TEXT,
    response TEXT,
    responseToResponse TEXT,
    training_status TEXT NOT NULL,
    training_type TEXT
);

CREATE TABLE query (
    id SERIAL PRIMARY KEY,
    query_id TEXT NOT NULL,
    module_id TEXT,
    path_id TEXT,
    page_id INTEGER,
    query TEXT,
    query_type TEXT NOT NULL,
    prev_query_id TEXT
);

-- Query element
DROP TABLE IF EXISTS query_element;
CREATE TABLE query_element (
    id SERIAL PRIMARY KEY,
    query_id TEXT NOT NULL,
    query_element_id TEXT NOT NULL,
    element_id TEXT NOT NULL,
    element_type TEXT NOT NULL,
    form_id TEXT
);

-- Element
DROP TABLE IF EXISTS element;
CREATE TABLE element (
    pk_val SERIAL PRIMARY KEY,
    id TEXT NOT NULL,
    parse_id TEXT NOT NULL,
    context TEXT,
    page_id TEXT NOT NULL,
    to_page_id TEXT,
    form_id TEXT,
    element_value TEXT,
    element_type TEXT,
    element_subtype TEXT,
    width INTEGER NOT NULL,
    height INTEGER NOT NULL,
    x INTEGER NOT NULL,
    y INTEGER NOT NULL,
    id_val TEXT,
    placeholder TEXT,
    element_name TEXT,
    outerHtml TEXT,
    generated_value TEXT,
    deleted TEXT,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Select option
DROP TABLE IF EXISTS select_option;
CREATE TABLE select_option (
    id SERIAL PRIMARY KEY,
    parse_id TEXT NOT NULL,
    element_id TEXT NOT NULL,
    option_id TEXT NOT NULL,
    option_value TEXT NOT NULL,
    selected BOOLEAN NOT NULL
);

-- Element action
DROP TABLE IF EXISTS element_action;
CREATE TABLE element_action (
    id SERIAL PRIMARY KEY,
    element_id TEXT NOT NULL,
    action_type TEXT NOT NULL,
    to_page_id TEXT,
    page_id TEXT NOT NULL
);

-- Page
DROP TABLE IF EXISTS page;
CREATE TABLE page (
    id SERIAL PRIMARY KEY,
    parse_id TEXT NOT NULL,
    page_url TEXT NOT NULL,
    page_name TEXT,
    page_id TEXT NOT NULL,
    page_hash TEXT,
    source_element_id TEXT
);

-- Cookie
DROP TABLE IF EXISTS cookie;
CREATE TABLE cookie (
    id SERIAL PRIMARY KEY,
    page_id TEXT NOT NULL,
    cookie_name TEXT NOT NULL,
    cookie_value TEXT NOT NULL
);

-- Form
DROP TABLE IF EXISTS form;
CREATE TABLE form (
    id SERIAL PRIMARY KEY,
    parse_id TEXT NOT NULL,
    page_id TEXT NOT NULL,
    form_id TEXT NOT NULL,
    action_name TEXT,
    action_link TEXT,
    context TEXT,
    outerHtml TEXT,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Screenshot
DROP TABLE IF EXISTS screenshot;
CREATE TABLE screenshot (
    id SERIAL PRIMARY KEY,
    parse_id TEXT NOT NULL,
    img_counter INTEGER NOT NULL,
    node_id TEXT NOT NULL,
    screenshot_name TEXT NOT NULL,
    y INTEGER NOT NULL
);

-- Parse
DROP TABLE IF EXISTS parse;
CREATE TABLE parse (
    id SERIAL PRIMARY KEY,
    company_id TEXT NOT NULL,
    input_type TEXT NOT NULL,
    parse_id TEXT NOT NULL,
    website_url TEXT NOT NULL,
    website_name TEXT NOT NULL,
    website_description TEXT NOT NULL,
    status TEXT NOT NULL,
    parse_root_id TEXT,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

