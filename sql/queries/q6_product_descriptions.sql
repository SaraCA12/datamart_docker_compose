-- Q6a: Total de códigos únicos de producto
SELECT COUNT(DISTINCT product_code) AS total_codigos_unicos
FROM dim_products;

-- Q6b: Productos con descripción 'SIN DESCRIPCION' (sin descripción consistente)
SELECT
    dp.product_code,
    dp.canonical_name,
    dp.category,
    COUNT(ft.id) AS num_transacciones
FROM dim_products dp
LEFT JOIN fact_transactions ft ON dp.product_code = ft.product_code
WHERE dp.canonical_name = 'SIN DESCRIPCION'
   OR dp.canonical_name IS NULL
GROUP BY dp.product_code, dp.canonical_name, dp.category
ORDER BY num_transacciones DESC;
