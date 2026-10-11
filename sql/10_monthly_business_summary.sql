```sql
-- Monthly business summary
-- Grain: one row per purchase month
-- Scope: delivered orders with order items

WITH order_metrics AS (
    SELECT
        o.order_id,
        DATE_TRUNC(
            'month', o.order_purchase_timestamp
        )::DATE AS purchase_month,
        SUM(oi.price) AS item_sales,
        SUM(oi.freight_value) AS freight_revenue
    FROM orders o
    JOIN order_items oi
        ON o.order_id = oi.order_id
    WHERE o.order_status = 'delivered'
      AND o.order_purchase_timestamp IS NOT NULL
    GROUP BY
        o.order_id,
        DATE_TRUNC(
            'month', o.order_purchase_timestamp
        )::DATE
),
monthly_sales AS (
    SELECT
        purchase_month,
        COUNT(*) AS delivered_order_count,
        ROUND(SUM(item_sales), 2) AS item_sales_brl,
        ROUND(SUM(freight_revenue), 2) AS freight_revenue_brl,
        ROUND(AVG(item_sales), 2) AS average_order_value_brl
    FROM order_metrics
    GROUP BY purchase_month
),
monthly_delivery AS (
    SELECT
        DATE_TRUNC(
            'month', order_purchase_timestamp
        )::DATE AS purchase_month,
        COUNT(*) FILTER (
            WHERE order_delivered_customer_date IS NOT NULL
              AND order_estimated_delivery_date IS NOT NULL
        ) AS eligible_delivery_orders,
        COUNT(*) FILTER (
            WHERE order_delivered_customer_date IS NULL
               OR order_estimated_delivery_date IS NULL
        ) AS excluded_missing_delivery_dates,
        ROUND(
            100.0 * COUNT(*) FILTER (
                WHERE order_delivered_customer_date IS NOT NULL
                  AND order_estimated_delivery_date IS NOT NULL
                  AND order_delivered_customer_date
                      > order_estimated_delivery_date
            )
            / NULLIF(
                COUNT(*) FILTER (
                    WHERE order_delivered_customer_date IS NOT NULL
                      AND order_estimated_delivery_date IS NOT NULL
                ),
                0
            ),
            2
        ) AS late_delivery_percentage
    FROM orders
    WHERE order_status = 'delivered'
      AND order_purchase_timestamp IS NOT NULL
    GROUP BY 1
)
SELECT
    s.purchase_month,
    s.delivered_order_count,
    s.item_sales_brl,
    s.freight_revenue_brl,
    s.average_order_value_brl,
    d.eligible_delivery_orders,
    d.excluded_missing_delivery_dates,
    d.late_delivery_percentage
FROM monthly_sales s
LEFT JOIN monthly_delivery d
    ON s.purchase_month = d.purchase_month
ORDER BY s.purchase_month;
```