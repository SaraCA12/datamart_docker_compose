"""
dags/utils/extract.py
Extracción de las dos fuentes de datos CSV.
Cada función devuelve un DataFrame con columnas ESTANDARIZADAS.

IMPORTANTE: Las fechas se parsean en esta etapa con el formato
conocido de cada fuente, antes de combinarlas, para evitar
ambigüedades al mezclar formatos M/D/YYYY y YYYY-MM-DD.
"""
import logging
import pandas as pd
from pathlib import Path

logger = logging.getLogger(__name__)

CANONICAL_COLUMNS = [
    "invoice_no", "product_code", "description",
    "quantity", "invoice_date", "unit_price",
    "customer_id", "country", "source",
]


def _normalize_columns(df: pd.DataFrame, rename_map: dict, source_name: str) -> pd.DataFrame:
    df = df.rename(columns=rename_map)
    df["source"] = source_name
    existing = [c for c in CANONICAL_COLUMNS if c in df.columns]
    return df[existing]


def extract_source1(data_path: str) -> pd.DataFrame:
    """
    Source 1: data.csv
    Formato de fecha: M/D/YYYY H:MM → ej. '12/1/2010 8:26'
    Se parsea aquí con el formato exacto de esta fuente.
    """
    file_path = Path(data_path) / "data.csv"
    logger.info(f"Extrayendo Source 1: {file_path}")

    df = pd.read_csv(file_path, encoding="latin-1", dtype=str, low_memory=False)

    # Parsear con formato exacto de Source 1
    parsed = pd.to_datetime(df["InvoiceDate"], format="%m/%d/%Y %H:%M", errors="coerce")

    # Fallback para los que no encajen exactamente
    mask_failed = parsed.isna()
    if mask_failed.any():
        parsed2 = pd.to_datetime(df.loc[mask_failed, "InvoiceDate"], errors="coerce")
        parsed = parsed.copy()
        parsed.loc[mask_failed] = parsed2
        logger.info(f"  {mask_failed.sum():,} fechas S1 parseadas con fallback.")

    # Convertir a string ISO uniforme para combinar con Source 2
    df["InvoiceDate"] = parsed.dt.strftime("%Y-%m-%d %H:%M:%S")

    logger.info(f"Source 1 — {len(df):,} filas extraidas.")

    return _normalize_columns(df, {
        "InvoiceNo":   "invoice_no",
        "StockCode":   "product_code",
        "Description": "description",
        "Quantity":    "quantity",
        "InvoiceDate": "invoice_date",
        "UnitPrice":   "unit_price",
        "CustomerID":  "customer_id",
        "Country":     "country",
    }, source_name="source1")


def extract_source2(data_path: str) -> pd.DataFrame:
    """
    Source 2: online_retail_II.csv
    Formato de fecha: YYYY-MM-DD HH:MM:SS → ej. '2009-12-01 07:45:00'
    Se parsea aquí con el formato exacto de esta fuente.
    """
    file_path = Path(data_path) / "online_retail_II.csv"
    logger.info(f"Extrayendo Source 2: {file_path}")

    df = pd.read_csv(file_path, encoding="utf-8", dtype=str, low_memory=False)

    # Parsear con formato exacto de Source 2 (ISO)
    parsed = pd.to_datetime(df["InvoiceDate"], format="%Y-%m-%d %H:%M:%S", errors="coerce")

    # Fallback para los que no encajen exactamente
    mask_failed = parsed.isna()
    if mask_failed.any():
        parsed2 = pd.to_datetime(df.loc[mask_failed, "InvoiceDate"], errors="coerce")
        parsed = parsed.copy()
        parsed.loc[mask_failed] = parsed2
        logger.info(f"  {mask_failed.sum():,} fechas S2 parseadas con fallback.")

    # Convertir a string ISO uniforme
    df["InvoiceDate"] = parsed.dt.strftime("%Y-%m-%d %H:%M:%S")

    logger.info(f"Source 2 — {len(df):,} filas extraidas.")

    return _normalize_columns(df, {
        "Invoice":     "invoice_no",
        "StockCode":   "product_code",
        "Description": "description",
        "Quantity":    "quantity",
        "InvoiceDate": "invoice_date",
        "Price":       "unit_price",
        "Customer ID": "customer_id",
        "Country":     "country",
    }, source_name="source2")


def combine_sources(df1: pd.DataFrame, df2: pd.DataFrame) -> tuple:
    """
    Combina ambas fuentes y detecta duplicados reales.

    DECISIÓN (DECISIONS.md §3 / EDA §5):
    Clave de deduplicación: (invoice_no, product_code, quantity)
    NO incluimos invoice_date porque los formatos convertidos pueden
    tener diferencias de segundos entre fuentes para el mismo registro.
    Source 2 tiene PRIORIDAD — se concatena primero.
    Los duplicados se registran en log_rejected_records con motivo 'Duplicado'.

    Resultado esperado según EDA:
      - Duplicados internos S1:       5,429
      - Duplicados internos S2:      34,604
      - Solapados entre fuentes:     25,900
      - Total esperado:          ~65,933
    """
    combined = pd.concat([df2, df1], ignore_index=True)
    before   = len(combined)

    # Clave sin invoice_date para evitar falsos positivos por formato
    dedup_cols = ["invoice_no", "product_code", "quantity"]
    mask_dup   = combined.duplicated(subset=dedup_cols, keep="first")

    df_duplicados = combined[mask_dup].copy()
    df_duplicados["rejection_reason"] = "Duplicado"

    combined = combined[~mask_dup].copy()
    removed  = before - len(combined)

    logger.info(
        f"Deduplicacion: {removed:,} duplicados separados al log. "
        f"Registros unicos: {len(combined):,}"
    )
    return combined, df_duplicados