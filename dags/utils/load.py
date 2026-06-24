"""
dags/utils/load.py
Carga de datos transformados hacia el Data Warehouse en PostgreSQL.
Todas las operaciones usan ON CONFLICT para garantizar idempotencia.
"""
import logging
from io import StringIO

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

logger = logging.getLogger(__name__)


def get_connection(conn_params: dict):
    """Crea una conexión psycopg2 al Data Warehouse."""
    return psycopg2.connect(
        host=conn_params["host"],
        port=conn_params.get("port", 5432),
        dbname=conn_params["schema"],
        user=conn_params["login"],
        password=conn_params["password"],
    )


def upsert_products(conn, df_products: pd.DataFrame) -> int:
    """
    Upsert en dim_products.
    Si el product_code ya existe → actualiza canonical_name y category.
    """
    if df_products.empty:
        return 0

    records = [
        (row["product_code"], row["canonical_name"], row["category"])
        for _, row in df_products.iterrows()
    ]

    sql = """
        INSERT INTO dim_products (product_code, canonical_name, category)
        VALUES %s
        ON CONFLICT (product_code) DO UPDATE
            SET canonical_name = EXCLUDED.canonical_name,
                category       = EXCLUDED.category,
                updated_at     = NOW()
    """
    with conn.cursor() as cur:
        execute_values(cur, sql, records, page_size=500)
    conn.commit()
    logger.info(f"  dim_products: {len(records):,} productos upserted.")
    return len(records)


def upsert_customers(conn, df_customers: pd.DataFrame) -> int:
    """Upsert en dim_customers."""
    if df_customers.empty:
        return 0

    records = [
        (row["customer_id"], bool(row["is_anonymous"]))
        for _, row in df_customers.iterrows()
    ]

    sql = """
        INSERT INTO dim_customers (customer_id, is_anonymous)
        VALUES %s
        ON CONFLICT (customer_id) DO NOTHING
    """
    with conn.cursor() as cur:
        execute_values(cur, sql, records, page_size=500)
    conn.commit()
    logger.info(f"  dim_customers: {len(records):,} clientes procesados.")
    return len(records)


def insert_transactions(conn, df: pd.DataFrame, batch_size: int = 5000) -> tuple:
    """
    Inserta registros en fact_transactions.
    ON CONFLICT (source_row_hash) DO NOTHING garantiza idempotencia:
    si el pipeline corre dos veces, los duplicados se ignoran silenciosamente.
    Returns: (inserted, skipped_duplicates)
    """
    if df.empty:
        return 0, 0

    required_cols = [
        "invoice_no", "product_code", "customer_id",
        "invoice_date_utc", "date_id",
        "quantity", "unit_price", "gross_revenue",
        "country", "transaction_type", "source", "source_row_hash",
    ]

    # Asegurar que 'country' no tenga nulos
    df["country"] = df["country"].fillna("Unknown")

    total_inserted = 0
    total_skipped  = 0
    batches = [df[i:i+batch_size] for i in range(0, len(df), batch_size)]

    sql = """
        INSERT INTO fact_transactions (
            invoice_no, product_code, customer_id,
            transaction_date, date_id,
            quantity, unit_price, gross_revenue,
            country, transaction_type, source, source_row_hash
        )
        VALUES %s
        ON CONFLICT (source_row_hash) DO NOTHING
    """

    for i, batch in enumerate(batches):
        records = [
            (
                row["invoice_no"],
                row["product_code"],
                row["customer_id"],
                row["invoice_date_utc"],
                row["date_id"],
                int(row["quantity"]),
                float(row["unit_price"]),
                float(row["gross_revenue"]),
                row["country"],
                row["transaction_type"],
                row["source"],
                row["source_row_hash"],
            )
            for _, row in batch.iterrows()
        ]

        with conn.cursor() as cur:
            execute_values(cur, sql, records, page_size=500)
            # Contar cuántos se insertaron realmente vs. cuántos se saltaron
            inserted_in_batch = cur.rowcount if cur.rowcount >= 0 else len(records)
        conn.commit()
        total_inserted += inserted_in_batch
        logger.info(f"  Batch {i+1}/{len(batches)}: {inserted_in_batch:,} insertados.")

    logger.info(f"  fact_transactions: {total_inserted:,} filas cargadas.")
    return total_inserted, total_skipped


def log_rejected_records(conn, df_rejected: pd.DataFrame, source: str):
    """Guarda los registros rechazados en log_rejected_records."""
    if df_rejected.empty:
        return

    import json

    records = []
    for _, row in df_rejected.iterrows():
        raw = {k: str(v) for k, v in row.to_dict().items() if k != "rejection_reason"}
        records.append((
            row.get("source", source),
            row.get("invoice_no", None),
            row.get("product_code", None),
            str(row.get("rejection_reason", "Sin motivo")),
            json.dumps(raw),
        ))

    sql = """
        INSERT INTO log_rejected_records
            (source, invoice_no, product_code, rejection_reason, raw_data)
        VALUES %s
    """
    with conn.cursor() as cur:
        execute_values(cur, sql, records, page_size=200)
    conn.commit()
    logger.info(f"  log_rejected_records: {len(records):,} registros rechazados guardados.")


def compute_and_upsert_daily_revenue(conn):
    """
    Recalcula fact_daily_revenue desde fact_transactions.
    UPSERT: si ya existe la combinación (date_id, product_code, country),
    actualiza los valores. Esto garantiza idempotencia en la tabla de agregados.
    """
    sql_compute = """
        INSERT INTO fact_daily_revenue (
            date_id, product_code, country,
            gross_sales, total_returns, net_revenue,
            sale_quantity, return_quantity, sale_count, return_count
        )
        SELECT
            date_id,
            product_code,
            country,
            COALESCE(SUM(gross_revenue) FILTER (WHERE transaction_type = 'SALE'),  0) AS gross_sales,
            COALESCE(SUM(gross_revenue) FILTER (WHERE transaction_type = 'RETURN'), 0) AS total_returns,
            COALESCE(SUM(gross_revenue) FILTER (WHERE transaction_type = 'SALE'),  0)
            - COALESCE(SUM(gross_revenue) FILTER (WHERE transaction_type = 'RETURN'), 0) AS net_revenue,
            COALESCE(SUM(quantity)       FILTER (WHERE transaction_type = 'SALE'),  0) AS sale_quantity,
            COALESCE(SUM(ABS(quantity))  FILTER (WHERE transaction_type = 'RETURN'), 0) AS return_quantity,
            COUNT(*)                     FILTER (WHERE transaction_type = 'SALE')  AS sale_count,
            COUNT(*)                     FILTER (WHERE transaction_type = 'RETURN') AS return_count
        FROM fact_transactions
        GROUP BY date_id, product_code, country
        ON CONFLICT (date_id, product_code, country) DO UPDATE
            SET gross_sales     = EXCLUDED.gross_sales,
                total_returns   = EXCLUDED.total_returns,
                net_revenue     = EXCLUDED.net_revenue,
                sale_quantity   = EXCLUDED.sale_quantity,
                return_quantity = EXCLUDED.return_quantity,
                sale_count      = EXCLUDED.sale_count,
                return_count    = EXCLUDED.return_count,
                updated_at      = NOW()
    """
    with conn.cursor() as cur:
        cur.execute(sql_compute)
        rows_affected = cur.rowcount
    conn.commit()
    logger.info(f"  fact_daily_revenue: {rows_affected:,} filas actualizadas/insertadas.")
    return rows_affected
