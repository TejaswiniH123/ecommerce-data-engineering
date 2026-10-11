
{{ config(materialized='table') }}

WITH category_items AS (
    SELECT
        COALESCE(
            t.product_category_name_english,
            p.product_category_name,
            'unknown'
        ) AS category_name,
        oi.order_id,
        oi.price
    FROM {{ ref('stg_order_items') }} oi
    INNER JOIN {{ ref('stg_orders') }} o
        ON oi.order_id = o.order_id
    LEFT JOIN {{ ref('stg_products') }} p
        ON oi.product_id = p.product_id
    LEFT JOIN {{ ref('stg_product_category_translation') }} t
        ON p.product_category_name = t.product_category_name
    WHERE o.order_status = 'delivered'
),

category_totals AS (
    SELECT
        category_name,
        COUNT(*) AS total_items,
        COUNT(DISTINCT order_id) AS delivered_orders,
        SUM(price) AS item_gross_sales
    FROM category_items
    GROUP BY category_name
)

SELECT
    category_name,
    total_items,
    delivered_orders,
    ROUND(item_gross_sales, 2) AS item_gross_sales,
    ROUND(
        100.0 * item_gross_sales
        / NULLIF(SUM(item_gross_sales) OVER (), 0),
        2
    ) AS revenue_share_percentage
FROM category_totals
ORDER BY item_gross_sales DESC
