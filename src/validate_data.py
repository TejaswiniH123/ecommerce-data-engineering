
import logging
import os
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv(PROJECT_ROOT / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(
            LOG_DIR / "data_quality.log", encoding="utf-8"
        ),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)

EXPECTED_ROWS = {
    "customers": 99441,
    "orders": 99441,
    "products": 32951,
    "sellers": 3095,
    "order_items": 112650,
    "payments": 103886,
    "reviews": 99224,
    "product_category_translation": 71,
}


def run_check(cursor, description, query, should_fail=False):
    cursor.execute(query)
    result = cursor.fetchone()[0]

    if result == 0:
        logger.info("PASS: %s", description)
        return True

    message = f"CHECK: {description} | Found: {result:,}"

    if should_fail:
        logger.error("FAIL: %s", message)
        return False

    logger.warning("%s", message)
    return True


def main():
    required = [
        "PGHOST",
        "PGPORT",
        "PGDATABASE",
        "PGUSER",
        "PGPASSWORD",
    ]

    missing = [key for key in required if not os.getenv(key)]

    if missing:
        logger.error(
            "Missing .env settings: %s", ", ".join(missing)
        )
        sys.exit(1)

    connection = None
    failures = 0

    try:
        connection = psycopg2.connect(
            host=os.getenv("PGHOST"),
            port=os.getenv("PGPORT"),
            dbname=os.getenv("PGDATABASE"),
            user=os.getenv("PGUSER"),
            password=os.getenv("PGPASSWORD"),
            connect_timeout=5,
        )

        with connection.cursor() as cursor:
            logger.info("Starting data-quality validation")

            # 1. Verify row counts.
            for table, expected in EXPECTED_ROWS.items():
                cursor.execute(
                    f'SELECT COUNT(*) FROM "{table}"'
                )
                actual = cursor.fetchone()[0]

                if actual == expected:
                    logger.info(
                        "PASS: %s row count = %s",
                        table,
                        f"{actual:,}",
                    )
                else:
                    logger.error(
                        "FAIL: %s expected %s rows, found %s",
                        table,
                        f"{expected:,}",
                        f"{actual:,}",
                    )
                    failures += 1

            # 2. Validate relationships.
            checks = [
                (
                    "Orders without customers",
                    """
                    SELECT COUNT(*)
                    FROM orders o
                    LEFT JOIN customers c
                      ON o.customer_id = c.customer_id
                    WHERE c.customer_id IS NULL
                    """,
                    True,
                ),
                (
                    "Order items without orders",
                    """
                    SELECT COUNT(*)
                    FROM order_items i
                    LEFT JOIN orders o ON i.order_id = o.order_id
                    WHERE o.order_id IS NULL
                    """,
                    True,
                ),
                (
                    "Order items without products",
                    """
                    SELECT COUNT(*)
                    FROM order_items i
                    LEFT JOIN products p ON i.product_id = p.product_id
                    WHERE i.product_id IS NOT NULL
                      AND p.product_id IS NULL
                    """,
                    True,
                ),
                (
                    "Order items without sellers",
                    """
                    SELECT COUNT(*)
                    FROM order_items i
                    LEFT JOIN sellers s ON i.seller_id = s.seller_id
                    WHERE i.seller_id IS NOT NULL
                      AND s.seller_id IS NULL
                    """,
                    True,
                ),
                (
                    "Payments without orders",
                    """
                    SELECT COUNT(*)
                    FROM payments p
                    LEFT JOIN orders o ON p.order_id = o.order_id
                    WHERE o.order_id IS NULL
                    """,
                    True,
                ),
                (
                    "Reviews without orders",
                    """
                    SELECT COUNT(*)
                    FROM reviews r
                    LEFT JOIN orders o ON r.order_id = o.order_id
                    WHERE o.order_id IS NULL
                    """,
                    True,
                ),
            ]

            for description, query, should_fail in checks:
                if not run_check(
                    cursor, description, query, should_fail
                ):
                    failures += 1

            # 3. Business-rule checks.
            business_checks = [
                (
                    "Invalid non-null review scores",
                    """
                    SELECT COUNT(*)
                    FROM reviews
                    WHERE review_score IS NOT NULL
                      AND review_score NOT BETWEEN 1 AND 5
                    """,
                    True,
                ),
                (
                    "Negative item prices",
                    """
                    SELECT COUNT(*)
                    FROM order_items
                    WHERE price < 0
                    """,
                    True,
                ),
                (
                    "Negative freight values",
                    """
                    SELECT COUNT(*)
                    FROM order_items
                    WHERE freight_value < 0
                    """,
                    True,
                ),
                (
                    "Negative payment values",
                    """
                    SELECT COUNT(*)
                    FROM payments
                    WHERE payment_value < 0
                    """,
                    True,
                ),
                (
                    "Orders without order items (investigate)",
                    """
                    SELECT COUNT(*)
                    FROM orders o
                    WHERE NOT EXISTS (
                        SELECT 1
                        FROM order_items i
                        WHERE i.order_id = o.order_id
                    )
                    """,
                    False,
                ),
                (
                    "Repeated review ID occurrences (known source issue)",
                    """
                    SELECT COUNT(*) - COUNT(DISTINCT review_id)
                    FROM reviews
                    """,
                    False,
                ),
            ]

            for description, query, should_fail in business_checks:
                if not run_check(
                    cursor, description, query, should_fail
                ):
                    failures += 1

        if failures:
            logger.error(
                "Validation finished with %s failure(s).",
                failures,
            )
            sys.exit(1)

        logger.info("SUCCESS: all critical quality checks passed")

    except psycopg2.Error:
        logger.exception("Database error during validation")
        sys.exit(1)

    finally:
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    main()
