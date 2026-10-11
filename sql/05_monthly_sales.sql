
-- Monthly sales analytics
-- Grain: one row per purchase month
--
-- Business rules:
-- 1. Use delivered orders for this initial sales report.
-- 2. Calculate item sales from order_items.price.
-- 3. Calculate freight separately.
-- 4. Count distinct orders to avoid counting an order more than once.

SELECT
    DATE_TRUNC('month', o.order_purchase_timestamp)::DATE
        AS purchase_month,

    COUNT(DISTINCT o.order_id)
        AS delivered_order_count,

    COUNT(*)
        AS item_count,

    ROUND(SUM(oi.price), 2)
        AS item_gross_sales_brl,

    ROUND(SUM(oi.freight_value), 2)
        AS freight_revenue_brl,

    ROUND(SUM(oi.price + oi.freight_value), 2)
        AS item_plus_freight_brl

FROM orders AS o

INNER JOIN order_items AS oi
    ON o.order_id = oi.order_id

WHERE o.order_status = 'delivered'
  AND o.order_purchase_timestamp IS NOT NULL

GROUP BY
    DATE_TRUNC('month', o.order_purchase_timestamp)::DATE

ORDER BY
    purchase_month;
