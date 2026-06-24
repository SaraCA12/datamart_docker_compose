# DataMart S.A.S. — ETL Pipeline with Apache Airflow

End-to-end ETL pipeline: CSV files → PostgreSQL Data Warehouse, orchestrated with Apache Airflow + Celery + RabbitMQ in Docker.

---

## Architecture

```
CSV Sources ──► Airflow DAG ──► PostgreSQL Data Warehouse
                    │
                    ├── RabbitMQ (message broker)
                    ├── Celery Worker (task executor)
                    ├── Flower (task monitor)
                    └── FastAPI (product catalog API)
```

---

## Prerequisites

- Docker >= 24.0
- Docker Compose >= 2.20
- Python 3.8+ (only to generate the Fernet key)
- 4 GB RAM available for Docker
- [Kaggle](https://kaggle.com) account to download the datasets

---

## Setup (under 10 minutes)

### 1. Clone the repository

```bash
git clone <REPO_URL>
cd datamart-etl
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Generate the Fernet key:

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Open `.env` and paste the result into `AIRFLOW__CORE__FERNET_KEY`. Also update the database credentials:

```bash
nano .env
```

Critical variables to configure:

```
AIRFLOW__CORE__FERNET_KEY=<result from command above>
AIRFLOW_DB_HOST=<your PostgreSQL host>
AIRFLOW_DB_PORT=<port>
AIRFLOW_DB_NAME=<Airflow metadata DB name>
AIRFLOW_DB_USER=<user>
AIRFLOW_DB_PASSWORD=<password>

WAREHOUSE_DB_HOST=<your PostgreSQL host>
WAREHOUSE_DB_PORT=<port>
WAREHOUSE_DB_NAME=<Data Warehouse DB name>
WAREHOUSE_DB_USER=<user>
WAREHOUSE_DB_PASSWORD=<password>
```

> ⚠️ **Never commit the real `.env` file.** It is already in `.gitignore`.

### 3. Download the Kaggle datasets

| Dataset | File | Destination |
|---|---|---|
| [ecommerce-data](https://www.kaggle.com/datasets/carrie1/ecommerce-data) | `data.csv` | `data/data.csv` |
| [online-retail-transaction-dataset](https://www.kaggle.com/datasets/thedevastator/online-retail-transaction-dataset) | `online_retail_II.xlsx` | `data/online_retail_II.xlsx` |

> ⚠️ The second dataset comes as `.xlsx` with two sheets. Convert it to CSV before continuing:

```bash
python3 -c "
import pandas as pd
df1 = pd.read_excel('data/online_retail_II.xlsx', sheet_name='Year 2009-2010')
df2 = pd.read_excel('data/online_retail_II.xlsx', sheet_name='Year 2010-2011')
df = pd.concat([df1, df2], ignore_index=True)
df.to_csv('data/online_retail_II.csv', index=False)
print(f'Done: {len(df):,} rows exported')
"
```

Verify the files are in place:

```bash
ls -lh data/
# data.csv              (~43 MB)
# online_retail_II.csv  (~130 MB)
```

### 4. Create the PostgreSQL databases

Connect to your PostgreSQL server and create two databases:

```sql
CREATE DATABASE airflow_metadata_<yourname>;
CREATE DATABASE datamart_dw_<yourname>;
```

### 5. Create the Data Warehouse tables

```bash
psql "postgresql://<user>:<password>@<host>:<port>/datamart_dw_<yourname>" \
  -f sql/init_warehouse.sql
```

### 6. Start the full environment

```bash
docker compose up -d
```

This command automatically starts:
- RabbitMQ (message broker)
- Airflow Init (initializes DB, creates admin user, sets up Connections and Variables)
- Airflow Webserver
- Airflow Scheduler
- Airflow Worker (Celery)
- Flower (monitor)
- Product API (FastAPI with product catalog)

Wait ~60 seconds, then verify all services are running:

```bash
docker compose ps
```

All services should be in `Up` or `healthy` state.

---

## Verify the environment is correctly configured

### Airflow UI
Open **http://127.0.0.1:8080**
- Username: `admin`
- Password: `admin123` (or the value set in `.env`)

### Verify Connections
Airflow UI → **Admin → Connections** → search for `postgres_warehouse`.

It should show:
- **Conn Type:** Postgres
- **Host:** your warehouse host
- **Schema:** your warehouse DB name

### Verify Variables
Airflow UI → **Admin → Variables**. The following must exist:

| Variable | Example value |
|---|---|
| `batch_size` | 5000 |
| `data_path` | /opt/airflow/data |
| `source1_filename` | data.csv |
| `source2_filename` | online_retail_II.csv |
| `reject_log_enabled` | true |

### Product API
```bash
curl http://localhost:8000/health
# {"status":"ok","service":"product-catalog-api"}

curl "http://localhost:8000/products?page=1&size=3"
# Returns list of products with categories
```

Interactive docs: **http://localhost:8000/docs**

### RabbitMQ UI
**http://localhost:15672** → user: `airflow` / password: `airflow123`

### Flower (Celery monitor)
**http://localhost:5555** → should show at least 1 worker Online

---

## Run the pipeline

In Airflow UI:
1. Click on `datamart_etl_pipeline`
2. Click ▶ **(Trigger DAG)**
3. Confirm with **Trigger**

The pipeline takes ~15-20 minutes to process ~1.5M records.

### Monitor execution

In the DAG **Graph** view, tasks change color as they run:
- 🟡 Yellow = queued / running
- 🟢 Green = success
- 🔴 Red = failed (click the task to view logs)

Also from the terminal:
```bash
docker logs datamart_airflow_worker -f --tail 20
```

---

## Verify data arrived in the Data Warehouse

```bash
psql "postgresql://<user>:<password>@<host>:<port>/datamart_dw_<yourname>" -c "
SELECT 'dim_products'       AS table_name, COUNT(*) FROM dim_products
UNION ALL
SELECT 'dim_customers',                    COUNT(*) FROM dim_customers
UNION ALL
SELECT 'fact_transactions',                COUNT(*) FROM fact_transactions
UNION ALL
SELECT 'fact_daily_revenue',               COUNT(*) FROM fact_daily_revenue
UNION ALL
SELECT 'log_rejected_records',             COUNT(*) FROM log_rejected_records
UNION ALL
SELECT 'log_pipeline_runs',                COUNT(*) FROM log_pipeline_runs;
"
```

Expected result:

```
table_name           |   count
---------------------+---------
dim_products         |   5,072
dim_customers        |   5,940
fact_transactions    | 1,030,145
fact_daily_revenue   |   593,194
log_rejected_records |   579,135
log_pipeline_runs    |         1
```

---

## Business SQL queries

All queries are in `sql/queries/`:

```bash
# Q1: Monthly evolution of net sales
psql "postgresql://..." -f sql/queries/q1_monthly_net_sales.sql

# Q2: Revenue by category and return rates
psql "postgresql://..." -f sql/queries/q2_category_revenue.sql

# Q3: Top 10 products by net revenue and return rate
psql "postgresql://..." -f sql/queries/q3_top_products.sql

# Q4-Q7: Countries, anonymous customers, descriptions, recommendation
psql "postgresql://..." -f sql/queries/q4_to_q7_business_queries.sql
```

---

## Repository structure

```
datamart-etl/
├── docker-compose.yml          # All services
├── .env.example                # Environment variables template
├── .gitignore
├── README.md                   # This file
├── DECISIONS.md                # Technical decisions and ambiguous cases
├── eda_datamart.ipynb          # Exploratory data analysis
│
├── api/                        # Product catalog REST API (FastAPI)
│   ├── Dockerfile
│   ├── main.py
│   ├── generate_catalog.py
│   └── requirements.txt
│
├── dags/
│   ├── datamart_etl_dag.py     # Main Airflow DAG
│   └── utils/
│       ├── extract.py          # CSV extraction
│       ├── transform.py        # Cleaning, validation, business rules
│       └── load.py             # Data Warehouse loading
│
├── sql/
│   ├── init_warehouse.sql      # Data Warehouse DDL
│   └── queries/
│       ├── q1_monthly_net_sales.sql
│       ├── q2_category_revenue.sql
│       ├── q3_top_products.sql
│       └── q4_to_q7_business_queries.sql
│
├── scripts/
│   └── init_airflow.sh         # Auto-configures Connections and Variables
│
├── config/
│   └── category_mapping.json   # Keyword-to-category mapping (API fallback)
│
└── data/                       # Source CSV files (in .gitignore due to size)
    └── .gitkeep
```

---

## Shut down the environment

```bash
docker compose down          # Stop containers (data persists in volumes)
docker compose down -v       # Stop and remove volumes (full cleanup)
```

---

## FAQ

**Is the pipeline idempotent?**
Yes. Running it twice with the same data produces exactly the same result. This is guaranteed by `ON CONFLICT DO NOTHING` in `fact_transactions` (using `source_row_hash`) and `ON CONFLICT DO UPDATE` in `fact_daily_revenue`.

**Where can I see rejected records?**
```sql
SELECT rejection_reason, COUNT(*)
FROM log_rejected_records
GROUP BY rejection_reason
ORDER BY COUNT(*) DESC;
```

**What if the product API is unavailable?**
The pipeline has an automatic fallback that infers categories from keywords in the product description using `config/category_mapping.json`.

**Why are there so many rejected records?**
536,480 records were rejected due to invalid dates — these come from the historical dataset with non-standard date formats. They are all documented in `log_rejected_records` with the reason `'Fecha invalida'`.
