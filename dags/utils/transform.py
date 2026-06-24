"""
dags/utils/transform.py
Transformación completa del pipeline DataMart ETL.
Decisiones documentadas en DECISIONS.md y EDA_Conclusiones_y_decisiones.pdf
"""
import hashlib
import json
import logging
from pathlib import Path

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


# ─── 1. LIMPIEZA BÁSICA Y TIPOS ────────────────────────────────────────────────

def clean_and_cast_types(df: pd.DataFrame) -> tuple:
    """
    Convierte tipos y separa registros rechazados.
    Reglas:
    - quantity y unit_price no numéricos → RECHAZAR
    - product_code nulo → RECHAZAR
    - description nula → CORREGIR buscando mismo StockCode (moda)
    - description → normalizar a MAYÚSCULAS
    """
    rejected_rows = []

    df["quantity"]   = pd.to_numeric(df["quantity"],   errors="coerce")
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")

    mask_invalid_numeric = df["quantity"].isna() | df["unit_price"].isna()
    if mask_invalid_numeric.any():
        bad = df[mask_invalid_numeric].copy()
        bad["rejection_reason"] = "quantity o unit_price no es numerico"
        rejected_rows.append(bad)
        df = df[~mask_invalid_numeric].copy()
        logger.warning(f"  Rechazados {len(bad):,} registros por valores numericos invalidos.")

    df["product_code"] = df["product_code"].astype(str).str.strip()
    mask_no_product = df["product_code"].isin(["", "nan", "NaN", "None"])
    if mask_no_product.any():
        bad = df[mask_no_product].copy()
        bad["rejection_reason"] = "product_code nulo o vacio"
        rejected_rows.append(bad)
        df = df[~mask_no_product].copy()
        logger.warning(f"  Rechazados {len(bad):,} registros sin product_code.")

    df["description"] = df["description"].astype(str).str.strip()
    mask_null_desc = df["description"].isin(["", "nan", "NaN", "None"])
    if mask_null_desc.any():
        desc_map = (
            df[~mask_null_desc]
            .groupby("product_code")["description"]
            .agg(lambda x: x.mode().iloc[0] if not x.mode().empty else x.iloc[0])
        )
        df.loc[mask_null_desc, "description"] = (
            df.loc[mask_null_desc, "product_code"].map(desc_map)
        )
        df["description"] = df["description"].fillna("SIN DESCRIPCION")
        logger.info(f"  {mask_null_desc.sum():,} descripciones nulas corregidas por StockCode.")

    df["description"] = df["description"].str.upper()

    rejected = pd.concat(rejected_rows, ignore_index=True) if rejected_rows else pd.DataFrame()
    return df, rejected


# ─── 2. NORMALIZACIÓN DE FECHAS A UTC ──────────────────────────────────────────

def normalize_dates_to_utc(df: pd.DataFrame) -> tuple:
    """
    Parsea invoice_date a datetime UTC.

    Formatos presentes en los datasets:
      - Source 1: '12/1/2010 8:26'    → M/D/YYYY H:MM  (dayfirst=False)
      - Source 2: '2010-12-01 08:26:00' → ISO 8601      (parseo automático)
      - Algunos registros: '10/31/2011 14:41' → también M/D/YYYY

    Estrategia:
      1. Intentar parseo general (cubre ISO y M/D/YYYY)
      2. Los que fallan: intentar con dayfirst=True (cubre D/M/YYYY)
      3. Los que siguen fallando → RECHAZAR con motivo 'Fecha invalida'
    """
    # Paso 1: parseo general
    parsed = pd.to_datetime(df["invoice_date"], errors="coerce", dayfirst=False)

    # Paso 2: los que fallaron, intentar con dayfirst=True
    mask_failed = parsed.isna()
    if mask_failed.any():
        parsed2 = pd.to_datetime(
            df.loc[mask_failed, "invoice_date"],
            errors="coerce",
            dayfirst=True
        )
        parsed = parsed.copy()
        parsed.loc[mask_failed] = parsed2
        logger.info(f"  {mask_failed.sum():,} fechas reintentadas con dayfirst=True.")

    # Paso 3: los que siguen siendo NaT → rechazar
    mask_bad_date = parsed.isna()
    rejected = pd.DataFrame()
    if mask_bad_date.any():
        rejected = df[mask_bad_date].copy()
        rejected["rejection_reason"] = "Fecha invalida"
        df     = df[~mask_bad_date].copy()
        parsed = parsed[~mask_bad_date]
        logger.warning(f"  Rechazados {len(rejected):,} registros con fecha invalida.")

    df["invoice_date_utc"] = parsed.dt.tz_localize("UTC")
    df["date_id"]          = df["invoice_date_utc"].dt.date

    return df, rejected


# ─── 3. NORMALIZACIÓN DE PRODUCT CODES ────────────────────────────────────────

def normalize_product_codes(df: pd.DataFrame) -> pd.DataFrame:
    """Regla de negocio: StockCode → MAYÚSCULAS y sin espacios."""
    df["product_code"] = (
        df["product_code"]
        .astype(str)
        .str.upper()
        .str.strip()
        .str.replace(r"\s+", "", regex=True)
    )
    return df


# ─── 4. MANEJO DE CUSTOMER ID FALTANTES ────────────────────────────────────────

def handle_missing_customer_id(df: pd.DataFrame) -> pd.DataFrame:
    """
    DECISIÓN (EDA §3):
    ~25% de registros sin CustomerID → asignar 'ANONYMOUS'.
    Excluirlos sesgaría el volumen de ventas.
    El flag is_anonymous en dim_customers permite filtrarlos.
    """
    df["customer_id"] = df["customer_id"].astype(str).str.strip()
    mask_anonymous = df["customer_id"].isin(["", "nan", "NaN", "None"])
    count_anonymous = mask_anonymous.sum()
    if count_anonymous > 0:
        df.loc[mask_anonymous, "customer_id"] = "ANONYMOUS"
        logger.info(f"  {count_anonymous:,} transacciones sin cliente → ANONYMOUS.")

    df["customer_id"] = df["customer_id"].apply(
        lambda x: str(int(float(x))) if x != "ANONYMOUS" and _is_float_str(x) else x
    )
    return df


def _is_float_str(s: str) -> bool:
    try:
        float(s)
        return True
    except (ValueError, TypeError):
        return False


# ─── 5. VALIDACIÓN DE PRECIO (SOLO EN VENTAS) ──────────────────────────────────

def validate_unit_price(df: pd.DataFrame) -> tuple:
    """
    DECISIÓN (EDA §7):
    UnitPrice <= 0 en VENTA → RECHAZAR con motivo 'Precio Unitario <=0'
    Las devoluciones pueden tener precio 0 (ajustes contables), se aceptan.
    """
    mask_invalid_price = (df["transaction_type"] == "SALE") & (df["unit_price"] <= 0)
    rejected = df[mask_invalid_price].copy()
    if not rejected.empty:
        rejected["rejection_reason"] = "Precio Unitario <=0"
        logger.warning(f"  Rechazados {len(rejected):,} registros por Precio Unitario <=0.")
    valid = df[~mask_invalid_price].copy()
    return valid, rejected


# ─── 6. CÁLCULO DE REVENUE ─────────────────────────────────────────────────────

def calculate_revenue(df: pd.DataFrame) -> pd.DataFrame:
    """gross_revenue = |quantity| × unit_price. Siempre positivo."""
    df["gross_revenue"] = df["quantity"].abs() * df["unit_price"]
    return df


# ─── 7. NOMBRE CANÓNICO DE PRODUCTO ────────────────────────────────────────────

def resolve_canonical_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    DECISIÓN (EDA §4):
    Nombre canónico = moda (descripción más frecuente por product_code).
    Ya normalizado a MAYÚSCULAS en clean_and_cast_types.
    """
    canonical = (
        df.groupby("product_code")["description"]
        .agg(lambda x: x.mode().iloc[0] if not x.mode().empty else x.iloc[0])
        .reset_index()
        .rename(columns={"description": "canonical_name"})
    )
    df = df.merge(canonical, on="product_code", how="left")
    return df


# ─── 8. ASIGNACIÓN DE CATEGORÍA ────────────────────────────────────────────────

def assign_category(df: pd.DataFrame, config_path: str = None) -> pd.DataFrame:
    """
    Intenta obtener categoría desde la API interna de productos.
    Si la API no está disponible → fallback por palabras clave (category_mapping.json).
    """
    import requests

    API_URL      = "http://product-api:8000/products"
    category_map = {}

    try:
        page = 1
        while True:
            resp = requests.get(f"{API_URL}?page={page}&size=200", timeout=5)
            if resp.status_code != 200:
                break
            data = resp.json()
            for item in data["items"]:
                category_map[item["code"]] = item["category"]
            if page >= data["pages"]:
                break
            page += 1
        logger.info(f"  Categorias obtenidas desde API: {len(category_map):,} productos.")
    except Exception as e:
        logger.warning(f"  API no disponible ({e}). Usando fallback por palabras clave.")
        category_map = {}

    if category_map:
        df["category"] = df["product_code"].map(category_map).fillna("Varios")
    else:
        mapping_file = Path("/opt/airflow/config/category_mapping.json")
        with open(mapping_file, "r", encoding="utf-8") as f:
            config = json.load(f)
        categories  = config["categories"]
        default_cat = config.get("default", "Varios")

        def _infer(name):
            name_upper = str(name).upper()
            for cat, keywords in categories.items():
                if any(kw in name_upper for kw in keywords):
                    return cat
            return default_cat

        df["category"] = df["canonical_name"].apply(_infer)

    return df


# ─── 9. HASH DE FILA PARA IDEMPOTENCIA ────────────────────────────────────────

def compute_row_hash(df: pd.DataFrame) -> pd.DataFrame:
    """SHA-256 por fila sobre la clave de negocio. Garantiza idempotencia."""
    def _hash_row(row):
        key = f"{row['invoice_no']}|{row['product_code']}|{row['quantity']}|{row['invoice_date_utc']}|{row['source']}"
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    df["source_row_hash"] = df.apply(_hash_row, axis=1)
    return df


# ─── FUNCIÓN PRINCIPAL ─────────────────────────────────────────────────────────

def run_transformation(
    df_raw: pd.DataFrame,
    df_duplicados: pd.DataFrame = None,
    config_path: str = "/opt/airflow/config",
) -> tuple:
    """
    Pipeline completo de transformación.

    Parámetros:
        df_raw        : DataFrame combinado y deduplicado de ambas fuentes
        df_duplicados : DataFrame de duplicados detectados en extract (para loguear)
        config_path   : ruta a archivos de configuración

    Returns:
        df_valid    : listo para fact_transactions
        df_products : para upsert en dim_products
        df_customers: para upsert en dim_customers
        df_rejected : para log_rejected_records
    """
    logger.info(f"Iniciando transformacion con {len(df_raw):,} registros...")
    all_rejected = []

    # Incluir duplicados en el log de rechazos
    if df_duplicados is not None and not df_duplicados.empty:
        all_rejected.append(df_duplicados)
        logger.info(f"  {len(df_duplicados):,} duplicados agregados al log de rechazos.")

    # Paso 1: Limpieza básica, corrección de nulos y normalización
    df, rej = clean_and_cast_types(df_raw)
    if not rej.empty:
        all_rejected.append(rej)

    # Paso 2: Normalizar códigos de producto
    df = normalize_product_codes(df)

    # Paso 3: Normalizar fechas a UTC (con soporte multi-formato)
    df, rej = normalize_dates_to_utc(df)
    if not rej.empty:
        all_rejected.append(rej)

    # Paso 4: Manejar customer_id faltantes
    df = handle_missing_customer_id(df)

    # Paso 5: Marcar ventas y devoluciones
    df["transaction_type"] = np.where(df["quantity"] > 0, "SALE", "RETURN")
    ventas = (df["transaction_type"] == "SALE").sum()
    devol  = (df["transaction_type"] == "RETURN").sum()
    logger.info(f"  Ventas: {ventas:,} | Devoluciones: {devol:,}")

    # Paso 6: Validar precio (solo en ventas)
    df, rej = validate_unit_price(df)
    if not rej.empty:
        all_rejected.append(rej)

    # Paso 7: Calcular revenue
    df = calculate_revenue(df)

    # Paso 8: Nombres canónicos
    df = resolve_canonical_names(df)

    # Paso 9: Categorías (API con fallback)
    df = assign_category(df, config_path)

    # Paso 10: Hash de idempotencia
    df = compute_row_hash(df)

    # Dimensión productos
    df_products = (
        df[["product_code", "canonical_name", "category"]]
        .drop_duplicates(subset=["product_code"])
        .copy()
    )

    # Dimensión clientes
    df_customers = df[["customer_id"]].drop_duplicates().copy()
    df_customers["is_anonymous"] = df_customers["customer_id"] == "ANONYMOUS"

    # Consolidar rechazos
    df_rejected = pd.concat(all_rejected, ignore_index=True) if all_rejected else pd.DataFrame()

    logger.info(
        f"Transformacion completada: {len(df):,} validos | "
        f"{len(df_rejected):,} rechazados | "
        f"{len(df_products):,} productos unicos."
    )
    return df, df_products, df_customers, df_rejected