
{{ config(materialized='table') }}

WITH delivered_orders AS (
    SELECT
        order_id,
        DATE_TRUNC('month', order_purchase_timestamp)::DATE AS sales_month
    FROM {{ ref('stg_orders') }}
    WHERE order_status = 'delivered'
      AND order_purchase_timestamp IS NOT NULL
),

monthly_metrics AS (
    SELECT
        o.sales_month,
        COUNT(DISTINCT oi.order_id) AS delivered_orders_with_items,
        COUNT(*) AS total_items,
        SUM(oi.price) AS item_gross_sales,
        SUM(oi.freight_value) AS total_freight
    FROM delivered_orders o
    INNER JOIN {{ ref('stg_order_items') }} oi
        ON o.order_id = oi.order_id
    GROUP BY o.sales_month
)

SELECT
    sales_month,
    delivered_orders_with_items,
    total_items,
    ROUND(item_gross_sales, 2) AS item_gross_sales,
    ROUND(total_freight, 2) AS total_freight,
    ROUND(item_gross_sales + total_freight, 2) AS sales_plus_freight,
    ROUND(
        item_gross_sales / NULLIF(delivered_orders_with_items, 0),
        2
    ) AS average_order_value
FROM monthly_metrics
ORDER BY sales_month
