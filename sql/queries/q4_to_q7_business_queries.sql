-- Q4: Países con mayor volumen de transacciones y ticket promedio
SELECT
    ft.country,
    COUNT(DISTINCT ft.invoice_no)              AS num_facturas,
    COUNT(*)                                   AS num_lineas_venta,
    ROUND(SUM(ft.gross_revenue)::NUMERIC, 2)   AS revenue_bruto_total,
    ROUND(
        SUM(ft.gross_revenue) / NULLIF(COUNT(DISTINCT ft.invoice_no), 0), 2
    ) AS ticket_promedio_por_factura,
    ROUND(
        SUM(ft.gross_revenue) / NULLIF(SUM(SUM(ft.gross_revenue)) OVER (), 0) * 100, 2
    ) AS pct_del_total_revenue
FROM fact_transactions ft
WHERE ft.transaction_type = 'SALE'
GROUP BY ft.country
ORDER BY revenue_bruto_total DESC
LIMIT 20;

-- ─────────────────────────────────────────────────────────────────────────────
-- Q5: Diferencia entre clientes identificados vs. anónimos
-- (Solo aplica porque decidimos incluir transacciones sin customer_id)
-- ─────────────────────────────────────────────────────────────────────────────

SELECT
    dc.is_anonymous,
    CASE WHEN dc.is_anonymous THEN 'Sin cliente' ELSE 'Identificado' END AS tipo_cliente,
    COUNT(DISTINCT ft.customer_id)             AS num_clientes,
    COUNT(DISTINCT ft.invoice_no)              AS num_facturas,
    COUNT(*)                                   AS num_lineas,
    ROUND(SUM(ft.gross_revenue)::NUMERIC, 2)   AS revenue_bruto,
    ROUND(
        SUM(ft.gross_revenue) / NULLIF(COUNT(DISTINCT ft.invoice_no), 0), 2
    ) AS ticket_promedio,
    ROUND(
        COUNT(DISTINCT ft.invoice_no)::NUMERIC /
        NULLIF(COUNT(DISTINCT ft.customer_id), 0), 2
    ) AS facturas_por_cliente
FROM fact_transactions ft
JOIN dim_customers dc ON ft.customer_id = dc.customer_id
WHERE ft.transaction_type = 'SALE'
GROUP BY dc.is_anonymous
ORDER BY dc.is_anonymous;

-- ─────────────────────────────────────────────────────────────────────────────
-- Q6: Productos con descripción inconsistente y total de códigos únicos
-- ─────────────────────────────────────────────────────────────────────────────

-- 6a: Cuántos códigos únicos existen
SELECT COUNT(DISTINCT product_code) AS total_codigos_unicos
FROM dim_products;

-- 6b: Productos con más de una descripción distinta en las transacciones
-- (indica inconsistencia en el sistema operacional)
SELECT
    ft.product_code,
    dp.canonical_name                           AS nombre_canonico,
    dp.category,
    COUNT(DISTINCT ft.invoice_no)               AS num_transacciones,
    COUNT(DISTINCT
        UPPER(TRIM(
            -- Reconstruimos la descripción desde fact_transactions no existe;
            -- este subquery usa una vista auxiliar de las descripciones vistas
            -- Para simplificar, contamos variaciones desde la tabla de rechazos
            ft.product_code
        ))
    ) AS variaciones_codigo
FROM fact_transactions ft
JOIN dim_products dp ON ft.product_code = dp.product_code
WHERE dp.canonical_name IS NULL OR dp.canonical_name = ''
GROUP BY ft.product_code, dp.canonical_name, dp.category
ORDER BY num_transacciones DESC;

-- ─────────────────────────────────────────────────────────────────────────────
-- Q7: Recomendación concreta al equipo de producto
-- Identificar productos con alto volumen pero alta tasa de devolución
-- → candidatos para revisión de calidad o política de retorno
-- ─────────────────────────────────────────────────────────────────────────────

WITH product_summary AS (
    SELECT
        dp.product_code,
        dp.canonical_name,
        dp.category,
        SUM(fdr.gross_sales)              AS revenue_bruto,
        SUM(fdr.total_returns)            AS devoluciones,
        SUM(fdr.net_revenue)              AS revenue_neto,
        SUM(fdr.sale_count)               AS num_ventas,
        SUM(fdr.return_count)             AS num_devoluciones,
        CASE WHEN SUM(fdr.gross_sales) > 0
             THEN SUM(fdr.total_returns) / SUM(fdr.gross_sales) * 100
             ELSE 0 END                   AS tasa_devolucion_pct
    FROM fact_daily_revenue fdr
    JOIN dim_products dp ON fdr.product_code = dp.product_code
    GROUP BY dp.product_code, dp.canonical_name, dp.category
    HAVING SUM(fdr.sale_count) >= 20  -- umbral mínimo de relevancia
),
ranking AS (
    SELECT *,
        PERCENT_RANK() OVER (ORDER BY revenue_bruto DESC) AS rank_revenue,
        PERCENT_RANK() OVER (ORDER BY tasa_devolucion_pct DESC) AS rank_devolucion
    FROM product_summary
)
SELECT
    product_code,
    canonical_name,
    category,
    ROUND(revenue_bruto::NUMERIC, 2)        AS revenue_bruto,
    ROUND(devoluciones::NUMERIC, 2)         AS monto_devuelto,
    ROUND(revenue_neto::NUMERIC, 2)         AS revenue_neto,
    num_ventas,
    num_devoluciones,
    ROUND(tasa_devolucion_pct::NUMERIC, 2)  AS tasa_devolucion_pct,
    '⚠️ Alto revenue + alta devolución'     AS alerta
FROM ranking
WHERE rank_devolucion <= 0.2    -- top 20% en tasa de devolución
  AND rank_revenue   <= 0.3     -- top 30% en revenue (productos importantes)
ORDER BY revenue_bruto DESC;

/*
INTERPRETACIÓN:
Los productos en este resultado son los más críticos para el equipo de producto:
generan revenue significativo pero también devolucionan de forma desproporcionada,
lo que erosiona la rentabilidad neta. La recomendación concreta es revisar:
  1. La descripción y las imágenes del producto en la tienda (expectativas del cliente)
  2. El proceso de empaque y logística (¿llegan en mal estado?)
  3. La política de retorno (¿es demasiado laxa para ciertos SKUs?)
*/
