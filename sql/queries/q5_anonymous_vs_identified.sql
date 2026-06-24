-- Q5: Diferencia entre clientes identificados vs. anónimos
SELECT
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
