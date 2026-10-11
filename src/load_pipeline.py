
import logging
import os
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv


# Locate the project folders independently of the terminal's location.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
LOG_DIR = PROJECT_ROOT / "logs"

LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "etl.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)

load_dotenv(PROJECT_ROOT / ".env")


# Each table's source file, import columns, and expected row count.
TABLES = [
    {
        "table": "customers",
        "file": "olist_customers_dataset.csv",
        "columns": [
            "customer_id",
            "customer_unique_id",
            "customer_zip_code_prefix",
            "customer_city",
            "customer_state",
        ],
        "expected_rows": 99441,
    },
    {
        "table": "orders",
        "file": "olist_orders_dataset.csv",
        "columns": [
            "order_id",
            "customer_id",
            "order_status",
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ],
        "expected_rows": 99441,
    },
    {
        "table": "products",
        "file": "olist_products_dataset.csv",
        "columns": [
            "product_id",
            "product_category_name",
            "product_name_lenght",
            "product_description_lenght",
            "product_photos_qty",
            "product_weight_g",
            "product_length_cm",
            "product_height_cm",
            "product_width_cm",
        ],
        "expected_rows": 32951,
    },
    {
        "table": "sellers",
        "file": "olist_sellers_dataset.csv",
        "columns": [
            "seller_id",
            "seller_zip_code_prefix",
            "seller_city",
            "seller_state",
        ],
        "expected_rows": 3095,
    },
    {
        "table": "order_items",
        "file": "olist_order_items_dataset.csv",
        "columns": [
            "order_id",
            "order_item_id",
            "product_id",
            "seller_id",
            "shipping_limit_date",
            "price",
            "freight_value",
        ],
        "expected_rows": 112650,
    },
    {
        "table": "payments",
        "file": "olist_order_payments_dataset.csv",
        "columns": [
            "order_id",
            "payment_sequential",
            "payment_type",
            "payment_installments",
            "payment_value",
        ],
        "expected_rows": 103886,
    },
    {
        "table": "reviews",
        "file": "olist_order_reviews_dataset.csv",
        "columns": [
            "review_id",
            "order_id",
            "review_score",
            "review_comment_title",
            "review_comment_message",
            "review_creation_date",
            "review_answer_timestamp",
        ],
        "expected_rows": 99224,
    },
    {
        "table": "product_category_translation",
        "file": "product_category_name_translation.csv",
        "columns": [
            "product_category_name",
            "product_category_name_english",
        ],
        "expected_rows": 71,
    },
]


def validate_configuration():
    required = [
        "PGHOST",
        "PGPORT",
        "PGDATABASE",
        "PGUSER",
        "PGPASSWORD",
    ]

    missing = [key for key in required if not os.getenv(key)]

    if missing:
        raise RuntimeError(
            "Missing environment settings: " + ", ".join(missing)
        )


def connect_to_database():
    return psycopg2.connect(
        host=os.getenv("PGHOST"),
        port=os.getenv("PGPORT"),
        dbname=os.getenv("PGDATABASE"),
        user=os.getenv("PGUSER"),
        password=os.getenv("PGPASSWORD"),
        connect_timeout=5,
    )


def load_table(cursor, table_config):
    table = table_config["table"]
    filename = table_config["file"]
    columns = table_config["columns"]
    file_path = RAW_DIR / filename

    if not file_path.is_file():
        raise FileNotFoundError(f"Source file not found: {file_path}")

    column_sql = ", ".join(f'"{column}"' for column in columns)

    copy_sql = (
        f'COPY "{table}" ({column_sql}) '
        "FROM STDIN WITH (FORMAT CSV, HEADER TRUE, ENCODING 'UTF8')"
    )

    logger.info("Loading %s from %s", table, filename)

    with file_path.open(
        "r", encoding="utf-8-sig", newline=""
    ) as source_file:
        cursor.copy_expert(copy_sql, source_file)

    cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
    actual_rows = cursor.fetchone()[0]
    expected_rows = table_config["expected_rows"]

    if actual_rows != expected_rows:
        raise ValueError(
            f"{table}: expected {expected_rows} rows, "
            f"found {actual_rows}"
        )

    logger.info(
        "Validated %s: %s rows",
        table,
        f"{actual_rows:,}",
    )


def run_pipeline():
    validate_configuration()

    logger.info("Starting full-refresh ETL pipeline")
    logger.info("Source directory: %s", RAW_DIR)

    connection = None

    try:
        connection = connect_to_database()

        # One transaction: commit all tables or roll back all changes.
        with connection:
            with connection.cursor() as cursor:
                # All related tables are truncated together so their
                # foreign-key relationships remain valid.
                cursor.execute("""
                    TRUNCATE TABLE
                        reviews,
                        payments,
                        order_items,
                        orders,
                        customers,
                        product_category_translation,
                        products,
                        sellers
                    RESTART IDENTITY
                """)

                logger.info("Existing table contents cleared")

                for table_config in TABLES:
                    load_table(cursor, table_config)

        logger.info("SUCCESS: all tables loaded and validated")
        logger.info("Database transaction committed")

    except Exception:
        logger.exception("ETL pipeline failed; changes rolled back")
        raise

    finally:
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    run_pipeline()
