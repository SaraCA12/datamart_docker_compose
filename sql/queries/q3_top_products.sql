-- Q3a: Top 10 productos con mayor revenue NETO
SELECT
    dp.product_code,
    dp.canonical_name,
    dp.category,
    ROUND(SUM(fdr.gross_sales)::NUMERIC,   2) AS revenue_bruto,
    ROUND(SUM(fdr.total_returns)::NUMERIC, 2) AS devoluciones,
    ROUND(SUM(fdr.net_revenue)::NUMERIC,   2) AS revenue_neto,
    SUM(fdr.sale_quantity)                     AS unidades_vendidas
FROM fact_daily_revenue fdr
JOIN dim_products dp ON fdr.product_code = dp.product_code
GROUP BY dp.product_code, dp.canonical_name, dp.category
ORDER BY revenue_neto DESC
LIMIT 10;

-- ─────────────────────────────────────────────────────────────────────────────

-- Q3b: Top 10 productos con mayor TASA DE DEVOLUCIÓN
-- (mínimo 10 ventas para evitar que productos con 1 venta y 1 devolución dominen)
SELECT
    dp.product_code,
    dp.canonical_name,
    dp.category,
    SUM(fdr.sale_count)                        AS num_ventas,
    SUM(fdr.return_count)                      AS num_devoluciones,
    ROUND(SUM(fdr.gross_sales)::NUMERIC,   2)  AS revenue_bruto,
    ROUND(SUM(fdr.total_returns)::NUMERIC, 2)  AS monto_devuelto,
    ROUND(
        (SUM(fdr.total_returns) / NULLIF(SUM(fdr.gross_sales), 0)) * 100, 2
    ) AS tasa_devolucion_pct
FROM fact_daily_revenue fdr
JOIN dim_products dp ON fdr.product_code = dp.product_code
GROUP BY dp.product_code, dp.canonical_name, dp.category
HAVING SUM(fdr.sale_count) >= 10
ORDER BY tasa_devolucion_pct DESC
LIMIT 10;
