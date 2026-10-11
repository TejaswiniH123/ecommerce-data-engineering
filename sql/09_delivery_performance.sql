
-- Delivery performance
-- Grain: one row per purchase month
-- Scope: delivered orders with valid delivery timestamps

WITH delivery_metrics AS (
    SELECT
        DATE_TRUNC(
            'month',
            order_purchase_timestamp
        )::DATE AS purchase_month,

        order_id,

        EXTRACT(
            EPOCH FROM (
                order_delivered_customer_date
                - order_purchase_timestamp
            )
        ) / 86400.0 AS actual_delivery_days,

        EXTRACT(
            EPOCH FROM (
                order_estimated_delivery_date
                - order_purchase_timestamp
            )
        ) / 86400.0 AS estimated_delivery_days,

        CASE
            WHEN order_delivered_customer_date
                 > order_estimated_delivery_date
            THEN 1
            ELSE 0
        END AS delivered_late

    FROM orders

    WHERE order_status = 'delivered'
      AND order_purchase_timestamp IS NOT NULL
      AND order_delivered_customer_date IS NOT NULL
      AND order_estimated_delivery_date IS NOT NULL
)

SELECT
    purchase_month,
    COUNT(*) AS eligible_delivered_orders,

    ROUND(AVG(actual_delivery_days)::NUMERIC, 2)
        AS avg_actual_delivery_days,

    ROUND(AVG(estimated_delivery_days)::NUMERIC, 2)
        AS avg_estimated_delivery_days,

    SUM(delivered_late) AS late_deliveries,

    ROUND(
        100.0 * SUM(delivered_late) / COUNT(*),
        2
    ) AS late_delivery_percentage

FROM delivery_metrics

GROUP BY purchase_month
ORDER BY purchase_month;
