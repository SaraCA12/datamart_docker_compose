# Documento de Decisiones Técnicas
## DataMart S.A.S. | Pipeline ETL con Apache Airflow

---

## 1. Diseño del modelo del repositorio analítico

### Patrón elegido: Star Schema (Esquema Estrella)

El modelo fue diseñado siguiendo el patrón Star Schema, compuesto por tablas de dimensiones, tablas de hechos y tablas de control.

### Tablas de dimensiones

**`dim_products`** — Catálogo normalizado de productos.
Almacena el código de producto, el nombre canónico (resuelto por moda), la categoría inferida y si el producto está activo. Permite responder preguntas de negocio sobre qué productos generan más revenue o tienen mayor tasa de devolución.

**`dim_customers`** — Clientes identificados y anónimos.
Incluye un flag `is_anonymous` para distinguir transacciones con cliente registrado de las que no lo tienen. Esto permite filtrar o incluir clientes anónimos según el análisis.

**`dim_date`** — Tabla de calendario pre-poblada (2009–2012).
Contiene año, trimestre, mes, semana, día de la semana y flag de fin de semana. Facilita análisis temporales sin necesidad de extraer estas partes de la fecha en cada consulta.

### Tablas de hechos

**`fact_transactions`** — Granularidad: una fila por línea de factura.
Es la tabla central del modelo. Contiene tanto ventas (`transaction_type = 'SALE'`) como devoluciones (`transaction_type = 'RETURN'`) en la misma tabla. Esta decisión permite calcular el neto con una sola consulta usando `FILTER (WHERE transaction_type = ...)`, evitando JOINs complejos entre dos tablas separadas. Incluye `gross_revenue = |quantity| × unit_price` y el campo `source_row_hash` para garantizar idempotencia.

**`fact_daily_revenue`** — Granularidad: día + producto + país.
Tabla de hechos agregada que pre-calcula ventas brutas, devoluciones, revenue neto y conteos por periodo diario. Responde directamente las preguntas de negocio sobre evolución mensual y revenue por categoría sin necesidad de agregar millones de filas en tiempo de consulta.

### Tablas de control y calidad

**`log_rejected_records`** — Registros rechazados con motivo y datos originales en formato JSON. Permite auditar qué se excluyó del análisis y por qué.

**`log_pipeline_runs`** — Trazabilidad de cada ejecución del pipeline: cuántos registros se procesaron, cuántos se cargaron, cuántos se rechazaron y en qué momento.

### Por qué Star Schema y no otro modelo

- **Simplicidad para el negocio:** el equipo de inteligencia de negocio puede escribir consultas SQL con JOINs simples entre facts y dimensions sin conocer la lógica de transformación.
- **Rendimiento:** las tablas de hechos pre-agregan los datos más consultados (`fact_daily_revenue`), reduciendo el tiempo de respuesta en dashboards.
- **Coherencia con las preguntas de negocio:** todas las preguntas de la sección 7 se responden con JOINs entre `fact_daily_revenue`, `dim_products` y `dim_date`. No requieren lógica adicional en las consultas.
- **Separación ventas/devoluciones:** el campo `transaction_type` en `fact_transactions` cumple el requisito de la sección 5 sin necesidad de una tabla separada, manteniendo el modelo simple.

---

## 2. Resolución de casos ambiguos (Sección 5)

### Caso 1: Transacciones sin Customer ID

**Problema:** Aproximadamente el 25% de los registros no tienen un identificador de cliente.

**Decisión: INCLUIR, asignando el ID sintético `'ANONYMOUS'`.**

**Justificación:** Excluir el 25% de las transacciones sesgaría significativamente el análisis de volumen de ventas y revenue total. Estos registros representan ventas reales que sí ocurrieron. La dimensión `dim_customers` incluye el flag `is_anonymous = TRUE`, lo que permite filtrarlos fácilmente en análisis que requieran solo clientes identificados.

**Resultado del análisis (Q5):** Los clientes anónimos tienen un ticket promedio de $997 — el doble que los identificados ($470). Esto confirma que son compradores mayoristas de alto valor, no clientes ocasionales.

**Impacto documentado:** 234,965 transacciones asignadas como ANONYMOUS.

---

### Caso 2: Descripciones inconsistentes para el mismo código de producto

**Problema:** El mismo `StockCode` aparece con múltiples variantes de escritura. Por ejemplo: `CANDLE HOLDER WHITE`, `Candle Holder White`, `candle holder white`.

**Decisión: CORREGIR en dos pasos.**

1. Si la descripción está nula → buscar si ese mismo `product_code` tiene registros con descripción válida y copiar la más frecuente (moda).
2. Si no existe ninguna descripción para ese código → asignar `'SIN DESCRIPCION'`.
3. Todas las descripciones se normalizan a **MAYÚSCULAS** para eliminar variaciones de capitalización.
4. El nombre canónico final = la moda de las descripciones normalizadas por `product_code`.

**Justificación:** La moda representa la forma en que el sistema operacional nombra el producto la mayoría del tiempo. Es reproducible, determinista y no requiere intervención manual.

**Resultado:** 5,729 descripciones nulas corregidas. Solo 46 productos (0.9% del catálogo) quedaron como `'SIN DESCRIPCION'` por no tener ninguna referencia en ninguna fuente.

---

### Caso 3: Solapamiento de fechas entre los dos datasets de Kaggle

**Problema:** Los datasets `data.csv` (Source 1) y `online_retail_II.csv` (Source 2) se solapan temporalmente. Algunas facturas aparecen en ambas fuentes.

**Decisión: Clave compuesta `(invoice_no, product_code, quantity)` para detectar duplicados. Source 2 tiene PRIORIDAD.**

**Justificación de la clave sin `invoice_date`:**
Durante el desarrollo se detectó que incluir `invoice_date` en la clave de deduplicación causaba falsos positivos masivos. El motivo: cada fuente tiene su propio formato de fecha (`M/D/YYYY H:MM` en Source 1 vs `YYYY-MM-DD HH:MM:SS` en Source 2). Aunque se convierten a ISO estándar antes de combinar, las diferencias de segundos o precisión entre fuentes para el mismo registro hacían que no se detectaran como duplicados reales. Se optó por usar solo `(invoice_no, product_code, quantity)` como clave más estable.

**Justificación de la prioridad de Source 2:** El dataset `online_retail_II.csv` es el historial extendido con mayor cobertura. Se concatena primero y al hacer `drop_duplicates(keep='first')` sus registros sobreviven automáticamente.

**Resultado:** ~65,933 duplicados detectados y separados al log de rechazos.

---

### Caso 4: Parseo de fechas con formatos distintos entre fuentes

**Problema:** Source 1 usa formato `M/D/YYYY H:MM` y Source 2 usa ISO `YYYY-MM-DD HH:MM:SS`. Al combinarlas y parsear juntas, pandas generaba más de 1 millón de fechas inválidas.

**Decisión: Parsear cada fuente con su formato exacto ANTES de combinarlas.**

**Implementación en `extract.py`:**
- Source 1: `pd.to_datetime(df["InvoiceDate"], format="%m/%d/%Y %H:%M")`
- Source 2: `pd.to_datetime(df["InvoiceDate"], format="%Y-%m-%d %H:%M:%S")`
- Luego ambas se convierten a string ISO `%Y-%m-%d %H:%M:%S` para transporte uniforme.
- En `transform.py` se parsea el ISO estándar sin ambigüedad.

**Resultado:** De 1,072,960 fechas inválidas en la primera versión → 0 fechas inválidas tras esta corrección.

---

### Caso 5: Asignación de categorías sin API de catálogo (plus opcional)

**Contexto:** Se implementó la API opcional de productos (sección 4.3) usando FastAPI. El pipeline la consume para enriquecer las transacciones con la categoría de cada producto.

**Estrategia principal:** Consumir la API en `http://product-api:8000/products` paginando los resultados. La API genera el catálogo automáticamente al arrancar desde los propios CSVs.

**Estrategia de fallback:** Si la API no está disponible, el pipeline infiere la categoría mediante palabras clave en el nombre del producto usando `config/category_mapping.json`. El pipeline funciona correctamente en ambos casos.

---

### Caso 6: Registros con cantidad negativa o igual a cero

**Problema:** Existen registros con `quantity <= 0` que corresponden a devoluciones o ajustes.

**Decisión: SEPARAR como devoluciones, no rechazar.**

Se asigna `transaction_type = 'RETURN'`. Se almacenan en la misma tabla `fact_transactions` junto con las ventas (`transaction_type = 'SALE'`). El revenue de devoluciones se calcula con valor absoluto para que `gross_revenue` siempre sea positivo.

**Resultado:** 22,382 registros clasificados como RETURN (2.1% del total válido).

---

### Caso 7: Registros con precio unitario igual a cero o negativo

**Problema:** Existen registros de tipo venta con `unit_price <= 0`.

**Decisión: RECHAZAR con motivo `'Precio Unitario <=0'`.**

Una venta con precio cero o negativo no tiene valor analítico para calcular revenue. Se registran en `log_rejected_records` para revisión del equipo operacional. Las devoluciones pueden tener precio cero (ajustes contables) y se aceptan.

**Resultado:** 2,622 registros rechazados.

---

### Caso 8: Conversión del archivo online_retail_II.xlsx a CSV

**Situación:** El dataset descargado de Kaggle (Source 2) venía en formato `.xlsx` con dos hojas: `Year 2009-2010` y `Year 2010-2011`.

**Decisión:** Convertir manualmente a CSV antes de ejecutar el pipeline combinando ambas hojas en un solo archivo:

```python
import pandas as pd
df1 = pd.read_excel('data/online_retail_II.xlsx', sheet_name='Year 2009-2010')
df2 = pd.read_excel('data/online_retail_II.xlsx', sheet_name='Year 2010-2011')
df = pd.concat([df1, df2], ignore_index=True)
df.to_csv('data/online_retail_II.csv', index=False)
```

**Justificación:** Se combinaron ambas hojas para que el pipeline las procese como una fuente unificada. En producción este paso se automatizaría como tarea previa en el DAG.

---

## 3. Garantía de idempotencia del DAG

El pipeline garantiza idempotencia en tres niveles:

### Nivel 1: `fact_transactions` — Hash SHA-256 por fila

Cada fila tiene un `source_row_hash` = SHA-256 de `(invoice_no | product_code | quantity | invoice_date_utc | source)`. Este campo tiene restricción `UNIQUE`. La carga usa:

```sql
INSERT INTO fact_transactions (...) VALUES (...)
ON CONFLICT (source_row_hash) DO NOTHING
```

Ejecutar el pipeline dos veces con los mismos datos no genera duplicados.

### Nivel 2: `fact_daily_revenue` — Upsert por clave compuesta

```sql
ON CONFLICT (date_id, product_code, country) DO UPDATE SET ...
```

Cada ejecución recalcula los agregados desde cero y los actualiza. El resultado final es siempre el correcto.

### Nivel 3: Dimensiones — Upsert sin duplicación

- `dim_products`: `ON CONFLICT (product_code) DO UPDATE` — actualiza nombre y categoría.
- `dim_customers`: `ON CONFLICT (customer_id) DO NOTHING` — no duplica clientes.
- `log_pipeline_runs`: `ON CONFLICT (run_id) DO UPDATE` — registra estado final sin duplicar.

### Paso de datos entre tareas

Los datos intermedios se almacenan en archivos `.parquet` temporales en `/opt/airflow/data/`. Esto evita el límite de tamaño de XCom de Airflow (~48KB en PostgreSQL). Los archivos temporales se eliminan en la tarea `finalize_and_log`.

---

## 4. Decisiones sobre el entorno Docker

### Base de datos externa compartida

Se usó un servidor PostgreSQL externo en lugar de contenedores locales. Esto requirió codificar los caracteres especiales de la contraseña en la URL de conexión (`*` → `%2A`) para que SQLAlchemy la interprete correctamente.

### CeleryExecutor con RabbitMQ y Flower

Se configuró `CeleryExecutor` + RabbitMQ + Flower en lugar del `LocalExecutor` mínimo requerido. Esto permite escalar workers horizontalmente y monitorear tareas en tiempo real — arquitectura más cercana a producción.

### API de productos como servicio Docker

La API FastAPI corre como servicio adicional en `docker-compose.yml`, accesible desde los contenedores de Airflow en `http://product-api:8000`. Al arrancar, genera automáticamente el catálogo desde los CSVs disponibles.

### Permisos de carpetas compartidas

Los volúmenes montados (`logs/`, `data/`) deben tener permisos de escritura para el usuario de Airflow (UID 50000). Si se crean con el usuario root, es necesario ejecutar:

```bash
sudo chmod -R 777 logs/ data/
```

---

## 5. Lo que quedaría pendiente con más tiempo

- **Tests unitarios:** Pytest para las funciones de `transform.py`, especialmente los casos de borde.
- **Great Expectations:** Validación de esquema y distribución de datos antes de la carga.
- **Alertas:** Notificación cuando la tasa de rechazo supere un umbral (ej. >10%).
- **Particionamiento:** `fact_transactions` particionada por `date_id` para escalar a mayor volumen.
- **dbt:** Reemplazar transformaciones Python por modelos dbt para mayor trazabilidad y documentación automática del linaje de datos.
- **Automatización de la conversión XLSX:** Agregar una tarea al DAG que detecte si existe el `.xlsx` y lo convierta automáticamente antes de la extracción.
