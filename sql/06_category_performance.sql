
-- Product-category performance
-- Grain: one row per product category
-- Metric: item sales from delivered orders
-- Currency: BRL

SELECT
    COALESCE(
        t.product_category_name_english,
        p.product_category_name,
        'unknown'
    ) AS category_name,

    COUNT(*) AS item_count,

    COUNT(DISTINCT o.order_id) AS delivered_order_count,

    ROUND(SUM(oi.price), 2) AS item_gross_sales_brl,

    ROUND(
        100.0 * SUM(oi.price)
        / NULLIF(SUM(SUM(oi.price)) OVER (), 0),
        2
    ) AS sales_share_percent

FROM order_items AS oi

INNER JOIN orders AS o
    ON oi.order_id = o.order_id

LEFT JOIN products AS p
    ON oi.product_id = p.product_id

LEFT JOIN product_category_translation AS t
    ON p.product_category_name = t.product_category_name

WHERE o.order_status = 'delivered'

GROUP BY
    COALESCE(
        t.product_category_name_english,
        p.product_category_name,
        'unknown'
    )

ORDER BY
    item_gross_sales_brl DESC;
