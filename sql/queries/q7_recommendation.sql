-- Q7: Recomendación concreta al equipo de producto
-- Productos con alto revenue pero alta tasa de devolución
-- → candidatos prioritarios para revisión de calidad
WITH product_summary AS (
    SELECT
        dp.product_code,
        dp.canonical_name,
        dp.category,
        SUM(fdr.gross_sales)    AS revenue_bruto,
        SUM(fdr.total_returns)  AS devoluciones,
        SUM(fdr.net_revenue)    AS revenue_neto,
        SUM(fdr.sale_count)     AS num_ventas,
        SUM(fdr.return_count)   AS num_devoluciones,
        CASE WHEN SUM(fdr.gross_sales) > 0
             THEN SUM(fdr.total_returns) / SUM(fdr.gross_sales) * 100
             ELSE 0 END         AS tasa_devolucion_pct
    FROM fact_daily_revenue fdr
    JOIN dim_products dp ON fdr.product_code = dp.product_code
    GROUP BY dp.product_code, dp.canonical_name, dp.category
    HAVING SUM(fdr.sale_count) >= 20
),
ranking AS (
    SELECT *,
        PERCENT_RANK() OVER (ORDER BY revenue_bruto DESC)       AS rank_revenue,
        PERCENT_RANK() OVER (ORDER BY tasa_devolucion_pct DESC) AS rank_devolucion
    FROM product_summary
)
SELECT
    product_code,
    canonical_name,
    category,
    ROUND(revenue_bruto::NUMERIC, 2)       AS revenue_bruto,
    ROUND(devoluciones::NUMERIC, 2)        AS monto_devuelto,
    ROUND(revenue_neto::NUMERIC, 2)        AS revenue_neto,
    num_ventas,
    num_devoluciones,
    ROUND(tasa_devolucion_pct::NUMERIC, 2) AS tasa_devolucion_pct
FROM ranking
WHERE rank_devolucion <= 0.20
  AND rank_revenue    <= 0.30
ORDER BY revenue_bruto DESC
LIMIT 10;
