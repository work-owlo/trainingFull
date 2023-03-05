CREATE TABLE IF NOT EXISTS public.auth_token
(
    id integer NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1 ),
    refresh_token text COLLATE pg_catalog."default" NOT NULL,
    access_token text COLLATE pg_catalog."default" NOT NULL,
    updated timestamp without time zone,
    CONSTRAINT auth_token_pkey PRIMARY KEY (id)
);

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
);

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
);

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
);

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
);


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
);

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
);

CREATE TABLE IF NOT EXISTS public.module
(
    id integer NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1 ),
    module_id text COLLATE pg_catalog."default" NOT NULL,
    company_id text COLLATE pg_catalog."default" NOT NULL,
    module_title text COLLATE pg_catalog."default" NOT NULL,
    module_description text COLLATE pg_catalog."default" NOT NULL,
    created timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    tool_id text COLLATE pg_catalog."default" NOT NULL,
    access text COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT module_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public.role_module
(
    id integer NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1 ),
    module_id text COLLATE pg_catalog."default" NOT NULL,
    role_id text COLLATE pg_catalog."default" NOT NULL,
    status text COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT role_module_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public.role_tools
(
    id integer NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1 ),
    role_id text COLLATE pg_catalog."default" NOT NULL,
    tool_id text COLLATE pg_catalog."default" NOT NULL,
    status text COLLATE pg_catalog."default" NOT NULL,
    rt_id text COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT role_tools_pkey PRIMARY KEY (id)
);

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
);

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
);

CREATE TABLE IF NOT EXISTS public.tools
(
    id integer NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1 ),
    tool_id text COLLATE pg_catalog."default" NOT NULL,
    tool_name text COLLATE pg_catalog."default" NOT NULL,
    tool_icon text COLLATE pg_catalog."default" NOT NULL,
    status text COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT tools_pkey PRIMARY KEY (id)
);


CREATE TABLE IF NOT EXISTS public.training
(
    id integer NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1 ),
    training_id text COLLATE pg_catalog."default" NOT NULL,
    team_id text COLLATE pg_catalog."default" NOT NULL,
    query_data text COLLATE pg_catalog."default",
    response text COLLATE pg_catalog."default",
    module_id text COLLATE pg_catalog."default" NOT NULL,
    type text COLLATE pg_catalog."default",
    context text COLLATE pg_catalog."default",
    status text COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT training_pkey PRIMARY KEY (id)
);