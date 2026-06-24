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
LIMIT 15;
