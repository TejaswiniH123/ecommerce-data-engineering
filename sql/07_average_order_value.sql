
-- Average Order Value (AOV)
-- Grain: one row per purchase month
-- Scope: delivered orders with at least one order item
-- Revenue measure: item prices, excluding freight

WITH order_revenue AS (
    SELECT
        o.order_id,
        DATE_TRUNC(
            'month',
            o.order_purchase_timestamp
        )::DATE AS purchase_month,
        SUM(oi.price) AS order_item_revenue
    FROM orders AS o
    INNER JOIN order_items AS oi
        ON o.order_id = oi.order_id
    WHERE o.order_status = 'delivered'
      AND o.order_purchase_timestamp IS NOT NULL
    GROUP BY
        o.order_id,
        DATE_TRUNC(
            'month',
            o.order_purchase_timestamp
        )::DATE
)

SELECT
    purchase_month,
    COUNT(*) AS delivered_order_count,
    ROUND(SUM(order_item_revenue), 2) AS total_item_sales_brl,
    ROUND(AVG(order_item_revenue), 2) AS average_order_value_brl
FROM order_revenue
GROUP BY purchase_month
ORDER BY purchase_month;
