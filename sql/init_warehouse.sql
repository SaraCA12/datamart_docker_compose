-- =================================================================
-- DataMart S.A.S. — Data Warehouse Analítico
-- Script DDL — Se ejecuta automáticamente al iniciar el contenedor
-- Modelo: Star Schema
-- =================================================================

-- ─────────────────────────────────────────────────────────────────
-- DIMENSIONES
-- ─────────────────────────────────────────────────────────────────

-- DIM: Productos
-- Almacena el catálogo normalizado de productos.
-- El nombre canónico se elige como la descripción más frecuente
-- para cada código de producto (decisión documentada en DECISIONS.md).
CREATE TABLE IF NOT EXISTS dim_products (
    product_code    VARCHAR(30)  PRIMARY KEY,
    canonical_name  VARCHAR(500),
    category        VARCHAR(100) DEFAULT 'Sin categoría',
    is_active       BOOLEAN      DEFAULT TRUE,
    created_at      TIMESTAMPTZ  DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  DEFAULT NOW()
);

-- DIM: Clientes
-- Incluye clientes anónimos bajo el ID 'ANONYMOUS'
-- (decisión documentada en DECISIONS.md).
CREATE TABLE IF NOT EXISTS dim_customers (
    customer_id     VARCHAR(20)  PRIMARY KEY,
    is_anonymous    BOOLEAN      DEFAULT FALSE,
    first_seen_at   DATE,
    last_seen_at    DATE
);

-- DIM: Fechas (tabla de calendario para análisis temporal)
CREATE TABLE IF NOT EXISTS dim_date (
    date_id         DATE         PRIMARY KEY,
    year            SMALLINT     NOT NULL,
    quarter         SMALLINT     NOT NULL,
    month           SMALLINT     NOT NULL,
    month_name      VARCHAR(20)  NOT NULL,
    week_of_year    SMALLINT     NOT NULL,
    day_of_month    SMALLINT     NOT NULL,
    day_of_week     SMALLINT     NOT NULL,  -- 0=Lunes, 6=Domingo
    day_name        VARCHAR(20)  NOT NULL,
    is_weekend      BOOLEAN      NOT NULL
);

-- Poblar dim_date para el rango 2009-2012 (cubre ambos datasets)
INSERT INTO dim_date
SELECT
    d::DATE                                   AS date_id,
    EXTRACT(YEAR    FROM d)::SMALLINT         AS year,
    EXTRACT(QUARTER FROM d)::SMALLINT         AS quarter,
    EXTRACT(MONTH   FROM d)::SMALLINT         AS month,
    TO_CHAR(d, 'TMMonth')                     AS month_name,
    EXTRACT(WEEK    FROM d)::SMALLINT         AS week_of_year,
    EXTRACT(DAY     FROM d)::SMALLINT         AS day_of_month,
    EXTRACT(ISODOW  FROM d)::SMALLINT - 1     AS day_of_week,
    TO_CHAR(d, 'TMDay')                       AS day_name,
    EXTRACT(ISODOW  FROM d) IN (6, 7)         AS is_weekend
FROM generate_series(
    '2009-01-01'::DATE,
    '2012-12-31'::DATE,
    '1 day'::INTERVAL
) AS t(d)
ON CONFLICT (date_id) DO NOTHING;

-- ─────────────────────────────────────────────────────────────────
-- HECHOS
-- ─────────────────────────────────────────────────────────────────

-- FACT: Transacciones individuales (ventas Y devoluciones separadas)
-- Es la tabla central del modelo. Cada fila = una línea de factura.
-- transaction_type distingue 'SALE' de 'RETURN'.
-- source_row_hash garantiza idempotencia: si el pipeline corre dos
-- veces, ON CONFLICT DO NOTHING evita duplicados.
CREATE TABLE IF NOT EXISTS fact_transactions (
    id                  BIGSERIAL    PRIMARY KEY,
    invoice_no          VARCHAR(30)  NOT NULL,
    product_code        VARCHAR(30)  NOT NULL REFERENCES dim_products(product_code),
    customer_id         VARCHAR(20)  NOT NULL REFERENCES dim_customers(customer_id),
    transaction_date    TIMESTAMPTZ  NOT NULL,
    date_id             DATE         NOT NULL REFERENCES dim_date(date_id),
    quantity            INTEGER      NOT NULL,
    unit_price          NUMERIC(12,4) NOT NULL,
    gross_revenue       NUMERIC(14,4) NOT NULL,  -- cantidad × precio_unitario
    country             VARCHAR(100),
    transaction_type    VARCHAR(10)  NOT NULL CHECK (transaction_type IN ('SALE','RETURN')),
    source              VARCHAR(50)  NOT NULL,   -- 'source1' o 'source2'
    source_row_hash     VARCHAR(64)  UNIQUE NOT NULL,  -- SHA256 para idempotencia
    loaded_at           TIMESTAMPTZ  DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fact_trx_date       ON fact_transactions(date_id);
CREATE INDEX IF NOT EXISTS idx_fact_trx_product     ON fact_transactions(product_code);
CREATE INDEX IF NOT EXISTS idx_fact_trx_customer    ON fact_transactions(customer_id);
CREATE INDEX IF NOT EXISTS idx_fact_trx_type        ON fact_transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_fact_trx_country     ON fact_transactions(country);

-- FACT: Revenue diario por producto y país (agregado)
-- Responde directamente las preguntas de negocio sobre revenue neto.
-- Se recalcula en cada ejecución del pipeline (UPSERT).
CREATE TABLE IF NOT EXISTS fact_daily_revenue (
    date_id             DATE         NOT NULL REFERENCES dim_date(date_id),
    product_code        VARCHAR(30)  NOT NULL REFERENCES dim_products(product_code),
    country             VARCHAR(100) NOT NULL,
    gross_sales         NUMERIC(14,4) DEFAULT 0,   -- suma de ventas brutas
    total_returns       NUMERIC(14,4) DEFAULT 0,   -- suma de devoluciones (valor absoluto)
    net_revenue         NUMERIC(14,4) DEFAULT 0,   -- gross_sales - total_returns
    sale_quantity       INTEGER       DEFAULT 0,
    return_quantity     INTEGER       DEFAULT 0,
    sale_count          INTEGER       DEFAULT 0,   -- número de líneas de venta
    return_count        INTEGER       DEFAULT 0,   -- número de líneas de devolución
    updated_at          TIMESTAMPTZ   DEFAULT NOW(),
    PRIMARY KEY (date_id, product_code, country)
);

CREATE INDEX IF NOT EXISTS idx_daily_rev_date    ON fact_daily_revenue(date_id);
CREATE INDEX IF NOT EXISTS idx_daily_rev_product ON fact_daily_revenue(product_code);

-- ─────────────────────────────────────────────────────────────────
-- TABLAS DE LOG Y CONTROL
-- ─────────────────────────────────────────────────────────────────

-- LOG: Registros rechazados (precio <= 0, datos faltantes críticos, etc.)
CREATE TABLE IF NOT EXISTS log_rejected_records (
    id                  BIGSERIAL    PRIMARY KEY,
    source              VARCHAR(50)  NOT NULL,
    invoice_no          VARCHAR(30),
    product_code        VARCHAR(30),
    rejection_reason    TEXT         NOT NULL,
    raw_data            JSONB,
    rejected_at         TIMESTAMPTZ  DEFAULT NOW()
);

-- LOG: Ejecuciones del pipeline (para trazabilidad y diagnóstico)
CREATE TABLE IF NOT EXISTS log_pipeline_runs (
    run_id              VARCHAR(200) PRIMARY KEY,
    dag_run_id          VARCHAR(200),
    execution_date      DATE,
    status              VARCHAR(20)  DEFAULT 'RUNNING',
    records_extracted   INTEGER      DEFAULT 0,
    records_loaded      INTEGER      DEFAULT 0,
    records_rejected    INTEGER      DEFAULT 0,
    started_at          TIMESTAMPTZ  DEFAULT NOW(),
    finished_at         TIMESTAMPTZ,
    notes               TEXT
);

-- ─────────────────────────────────────────────────────────────────
-- CLIENTE ANÓNIMO — seed inicial requerido antes de cargar facts
-- ─────────────────────────────────────────────────────────────────
INSERT INTO dim_customers (customer_id, is_anonymous, first_seen_at, last_seen_at)
VALUES ('ANONYMOUS', TRUE, '2009-01-01', '2012-12-31')
ON CONFLICT (customer_id) DO NOTHING;
