#!/bin/bash
# scripts/init_airflow.sh
# Este script se ejecuta automáticamente al iniciar el contenedor airflow-init.
# Configura todas las Connections y Variables sin intervención manual.

set -e

echo "============================================"
echo " DataMart ETL — Inicializando Airflow"
echo "============================================"

# Esperar a que la base de datos de Airflow esté lista
echo "[1/5] Esperando base de datos de metadatos..."
airflow db check

# Inicializar / migrar la base de datos de Airflow
echo "[2/5] Inicializando base de datos de Airflow..."
airflow db migrate

# Crear usuario administrador (idempotente: no falla si ya existe)
echo "[3/5] Creando usuario administrador..."
airflow users create \
    --username "${_AIRFLOW_WWW_USER_USERNAME:-admin}" \
    --firstname "DataMart" \
    --lastname "Admin" \
    --role "Admin" \
    --email "admin@datamart.com.co" \
    --password "${_AIRFLOW_WWW_USER_PASSWORD:-admin123}" \
    2>/dev/null || echo "  → Usuario ya existe, omitiendo."

# ─────────────────────────────────────────────
# CONNECTIONS
# ─────────────────────────────────────────────
echo "[4/5] Configurando Airflow Connections..."

# Eliminar si existe para garantizar idempotencia, luego recrear
airflow connections delete 'postgres_warehouse' 2>/dev/null || true
airflow connections add 'postgres_warehouse' \
    --conn-type 'postgres' \
    --conn-host "${WAREHOUSE_DB_HOST}" \
    --conn-schema "${WAREHOUSE_DB_NAME}" \
    --conn-login "${WAREHOUSE_DB_USER}" \
    --conn-password "${WAREHOUSE_DB_PASSWORD}" \
    --conn-port "${WAREHOUSE_DB_PORT:-5432}"
echo "  ✓ Connection 'postgres_warehouse' creada."

# ─────────────────────────────────────────────
# VARIABLES
# ─────────────────────────────────────────────
echo "[5/5] Inicializando Airflow Variables..."

airflow variables set 'batch_size'             "${PIPELINE_BATCH_SIZE:-5000}"
airflow variables set 'data_path'              "${PIPELINE_DATA_PATH:-/opt/airflow/data}"
airflow variables set 'reject_log_enabled'     "${PIPELINE_REJECT_LOG_ENABLED:-true}"
airflow variables set 'source1_filename'       "data.csv"
airflow variables set 'source2_filename'       "online_retail_II.csv"

echo "  ✓ Variables inicializadas."

echo ""
echo "============================================"
echo " Inicialización completada exitosamente"
echo "============================================"
