-- Q1: Evolución mensual de ventas netas (descontando devoluciones)
-- ¿Cuál fue la tendencia de ingresos mes a mes?

SELECT
    dd.year,
    dd.month,
    dd.month_name,
    TO_CHAR(DATE_TRUNC('month', fdr.date_id), 'YYYY-MM') AS periodo,
    ROUND(SUM(fdr.gross_sales)::NUMERIC,   2) AS ventas_brutas,
    ROUND(SUM(fdr.total_returns)::NUMERIC, 2) AS devoluciones,
    ROUND(SUM(fdr.net_revenue)::NUMERIC,   2) AS ventas_netas,
    SUM(fdr.sale_count)                        AS num_transacciones_venta,
    SUM(fdr.return_count)                      AS num_devoluciones,
    ROUND(
        (SUM(fdr.total_returns) / NULLIF(SUM(fdr.gross_sales), 0)) * 100, 2
    ) AS pct_devolucion
FROM fact_daily_revenue fdr
JOIN dim_date dd ON fdr.date_id = dd.date_id
GROUP BY dd.year, dd.month, dd.month_name, DATE_TRUNC('month', fdr.date_id)
ORDER BY dd.year, dd.month;
