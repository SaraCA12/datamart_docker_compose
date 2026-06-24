-- Q2: Categorías con mayor revenue bruto y mayor proporción de devoluciones
-- Permite priorizar qué categorías merecen atención del equipo de producto

SELECT
    dp.category,
    ROUND(SUM(fdr.gross_sales)::NUMERIC,   2) AS revenue_bruto_total,
    ROUND(SUM(fdr.total_returns)::NUMERIC, 2) AS total_devoluciones,
    ROUND(SUM(fdr.net_revenue)::NUMERIC,   2) AS revenue_neto_total,
    SUM(fdr.sale_count)                        AS num_ventas,
    SUM(fdr.return_count)                      AS num_devoluciones,
    ROUND(
        (SUM(fdr.total_returns) / NULLIF(SUM(fdr.gross_sales), 0)) * 100, 2
    ) AS pct_devolucion,
    ROUND(
        SUM(fdr.gross_sales) / NULLIF(SUM(SUM(fdr.gross_sales)) OVER (), 0) * 100, 2
    ) AS pct_del_total_revenue
FROM fact_daily_revenue fdr
JOIN dim_products dp ON fdr.product_code = dp.product_code
GROUP BY dp.category
ORDER BY revenue_bruto_total DESC;
