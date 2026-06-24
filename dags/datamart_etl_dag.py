"""
dags/datamart_etl_dag.py
DAG principal del pipeline ETL DataMart S.A.S.

Flujo:
  extract_source1 ──┐
                    ├──> transform_and_validate ──> load_dimensions ──> load_transactions ──> compute_aggregates ──> finalize
  extract_source2 ──┘
"""
import logging
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from airflow import DAG
from airflow.models import Variable
from airflow.hooks.base import BaseHook
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator

logger = logging.getLogger(__name__)

DEFAULT_ARGS = {
    "owner":            "datamart-engineering",
    "depends_on_past":  False,
    "email_on_failure": False,
    "email_on_retry":   False,
    "retries":          3,
    "retry_delay":      timedelta(minutes=5),
}

with DAG(
    dag_id="datamart_etl_pipeline",
    description="Pipeline ETL DataMart S.A.S. — Fuentes CSV → PostgreSQL DW",
    default_args=DEFAULT_ARGS,
    schedule_interval="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["datamart", "etl", "production"],
) as dag:

    def _get_warehouse_conn_params() -> dict:
        conn = BaseHook.get_connection("postgres_warehouse")
        return {
            "host":     conn.host,
            "port":     conn.port or 5432,
            "schema":   conn.schema,
            "login":    conn.login,
            "password": conn.password,
        }

    def _get_pipeline_vars() -> dict:
        return {
            "batch_size":       int(Variable.get("batch_size",       default_var=5000)),
            "data_path":        Variable.get("data_path",        default_var="/opt/airflow/data"),
            "source1_filename": Variable.get("source1_filename", default_var="data.csv"),
            "source2_filename": Variable.get("source2_filename", default_var="online_retail_II.csv"),
        }

    # ── INICIO ────────────────────────────────────────────────────────────────

    task_start = EmptyOperator(task_id="start")

    # ── EXTRACCIÓN SOURCE 1 ───────────────────────────────────────────────────

    def extract_source1_task(**context):
        from utils.extract import extract_source1
        vars_ = _get_pipeline_vars()
        df    = extract_source1(vars_["data_path"])
        path  = Path(vars_["data_path"]) / "tmp_source1.parquet"
        df.to_parquet(path, index=False)
        logger.info(f"Source 1: {len(df):,} filas → {path}")
        return str(path)

    task_extract_source1 = PythonOperator(
        task_id="extract_source1",
        python_callable=extract_source1_task,
    )

    # ── EXTRACCIÓN SOURCE 2 ───────────────────────────────────────────────────

    def extract_source2_task(**context):
        from utils.extract import extract_source2
        vars_ = _get_pipeline_vars()
        df    = extract_source2(vars_["data_path"])
        path  = Path(vars_["data_path"]) / "tmp_source2.parquet"
        df.to_parquet(path, index=False)
        logger.info(f"Source 2: {len(df):,} filas → {path}")
        return str(path)

    task_extract_source2 = PythonOperator(
        task_id="extract_source2",
        python_callable=extract_source2_task,
    )

    # ── TRANSFORMACIÓN Y VALIDACIÓN ───────────────────────────────────────────

    def transform_and_validate_task(**context):
        from utils.extract import combine_sources
        from utils.transform import run_transformation

        ti    = context["ti"]
        path1 = ti.xcom_pull(task_ids="extract_source1")
        path2 = ti.xcom_pull(task_ids="extract_source2")

        df1 = pd.read_parquet(path1)
        df2 = pd.read_parquet(path2)

        # Combinar y separar duplicados
        df_combined, df_duplicados = combine_sources(df1, df2)
        logger.info(f"Combinados: {len(df_combined):,} | Duplicados: {len(df_duplicados):,}")

        # Transformación completa (pasa duplicados para loguearlos)
        df_valid, df_products, df_customers, df_rejected = run_transformation(
            df_combined,
            df_duplicados=df_duplicados,
            config_path="/opt/airflow/config",
        )

        # Guardar en disco
        vars_     = _get_pipeline_vars()
        data_path = Path(vars_["data_path"])
        df_valid.to_parquet(    data_path / "tmp_valid.parquet",     index=False)
        df_products.to_parquet( data_path / "tmp_products.parquet",  index=False)
        df_customers.to_parquet(data_path / "tmp_customers.parquet", index=False)
        if not df_rejected.empty:
            # Convertir todas las columnas a string para evitar conflictos de tipos
            df_rejected = df_rejected.astype(str)
            df_rejected.to_parquet(data_path / "tmp_rejected.parquet", index=False)

        ti.xcom_push(key="records_valid",    value=len(df_valid))
        ti.xcom_push(key="records_rejected", value=len(df_rejected))
        ti.xcom_push(key="products_count",   value=len(df_products))
        logger.info(f"Validos: {len(df_valid):,} | Rechazados: {len(df_rejected):,}")

    task_transform = PythonOperator(
        task_id="transform_and_validate",
        python_callable=transform_and_validate_task,
    )

    # ── CARGA DE DIMENSIONES ──────────────────────────────────────────────────

    def load_dimensions_task(**context):
        from utils.load import get_connection, upsert_products, upsert_customers, log_rejected_records

        vars_     = _get_pipeline_vars()
        data_path = Path(vars_["data_path"])
        conn      = get_connection(_get_warehouse_conn_params())

        try:
            upsert_products( conn, pd.read_parquet(data_path / "tmp_products.parquet"))
            upsert_customers(conn, pd.read_parquet(data_path / "tmp_customers.parquet"))
            rejected_path = data_path / "tmp_rejected.parquet"
            if rejected_path.exists():
                log_rejected_records(conn, pd.read_parquet(rejected_path), source="pipeline")
        finally:
            conn.close()

    task_load_dimensions = PythonOperator(
        task_id="load_dimensions",
        python_callable=load_dimensions_task,
    )

    # ── CARGA DE TRANSACCIONES ────────────────────────────────────────────────

    def load_transactions_task(**context):
        from utils.load import get_connection, insert_transactions

        vars_     = _get_pipeline_vars()
        data_path = Path(vars_["data_path"])
        conn      = get_connection(_get_warehouse_conn_params())

        try:
            df_valid       = pd.read_parquet(data_path / "tmp_valid.parquet")
            inserted, _    = insert_transactions(conn, df_valid, batch_size=vars_["batch_size"])
            context["ti"].xcom_push(key="transactions_inserted", value=inserted)
        finally:
            conn.close()

    task_load_transactions = PythonOperator(
        task_id="load_transactions",
        python_callable=load_transactions_task,
    )

    # ── AGREGADOS DIARIOS ─────────────────────────────────────────────────────

    def compute_aggregates_task(**context):
        from utils.load import get_connection, compute_and_upsert_daily_revenue

        conn = get_connection(_get_warehouse_conn_params())
        try:
            rows = compute_and_upsert_daily_revenue(conn)
            logger.info(f"fact_daily_revenue: {rows:,} filas actualizadas.")
        finally:
            conn.close()

    task_compute_aggregates = PythonOperator(
        task_id="compute_daily_aggregates",
        python_callable=compute_aggregates_task,
    )

    # ── FINALIZAR Y LOGUEAR ───────────────────────────────────────────────────

    def finalize_task(**context):
        from utils.load import get_connection

        conn = get_connection(_get_warehouse_conn_params())
        ti   = context["ti"]

        records_valid    = ti.xcom_pull(task_ids="transform_and_validate", key="records_valid")    or 0
        records_rejected = ti.xcom_pull(task_ids="transform_and_validate", key="records_rejected") or 0
        transactions_ins = ti.xcom_pull(task_ids="load_transactions",       key="transactions_inserted") or 0

        sql = """
            INSERT INTO log_pipeline_runs
                (run_id, dag_run_id, execution_date, status,
                 records_extracted, records_loaded, records_rejected, finished_at)
            VALUES (%s, %s, %s, 'SUCCESS', %s, %s, %s, NOW())
            ON CONFLICT (run_id) DO UPDATE
                SET status = 'SUCCESS', finished_at = NOW()
        """
        with conn.cursor() as cur:
            cur.execute(sql, (
                context["run_id"], context["run_id"], context["ds"],
                records_valid, transactions_ins, records_rejected
            ))
        conn.commit()
        conn.close()

        # Limpiar temporales
        vars_     = _get_pipeline_vars()
        data_path = Path(vars_["data_path"])
        for tmp in ["tmp_source1.parquet", "tmp_source2.parquet", "tmp_valid.parquet",
                    "tmp_products.parquet", "tmp_customers.parquet", "tmp_rejected.parquet"]:
            p = data_path / tmp
            if p.exists():
                p.unlink()

        logger.info(
            f"Pipeline finalizado. Validos: {records_valid:,} | "
            f"Cargados: {transactions_ins:,} | Rechazados: {records_rejected:,}"
        )

    task_finalize = PythonOperator(
        task_id="finalize_and_log",
        python_callable=finalize_task,
    )

    # ── DEPENDENCIAS ─────────────────────────────────────────────────────────

    task_start >> [task_extract_source1, task_extract_source2]
    [task_extract_source1, task_extract_source2] >> task_transform
    task_transform >> task_load_dimensions
    task_load_dimensions >> task_load_transactions
    task_load_transactions >> task_compute_aggregates
    task_compute_aggregates >> task_finalize