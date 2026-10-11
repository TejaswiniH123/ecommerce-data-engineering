
import csv
import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

BATCH_FILE = PROJECT_ROOT / "data" / "incoming" / "order_items_batch.csv"
PIPELINE_NAME = "order_items_incremental_load"

COLUMNS = [
    "order_id",
    "order_item_id",
    "product_id",
    "seller_id",
    "shipping_limit_date",
    "price",
    "freight_value",
]


def get_connection():
    return psycopg2.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=os.getenv("PGPORT", "5432"),
        dbname=os.getenv("PGDATABASE", "ecommerce_dw"),
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD"),
    )


def main():
    if not BATCH_FILE.exists():
        raise FileNotFoundError(f"Batch not found: {BATCH_FILE}")

    with BATCH_FILE.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames or not set(COLUMNS).issubset(reader.fieldnames):
            raise ValueError("Order-items CSV is missing required columns.")

        rows = list(reader)

    if not rows:
        raise ValueError("Order-items batch is empty.")

    keys = []

    for row in rows:
        if not row["order_id"] or not row["order_item_id"]:
            raise ValueError("Every item needs an order_id and order_item_id.")

        try:
            item_id = int(row["order_item_id"])
        except (TypeError, ValueError):
            raise ValueError(f"Invalid order_item_id: {row['order_item_id']!r}")

        if item_id <= 0:
            raise ValueError("order_item_id must be positive.")

        keys.append((row["order_id"], item_id))

    if len(keys) != len(set(keys)):
        raise ValueError("Batch contains duplicate composite keys.")

    connection = get_connection()
    run_id = None

    try:
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO etl_run_log
                        (pipeline_name, load_type, status, source_name, input_rows)
                    VALUES (%s, 'INCREMENTAL', 'RUNNING', %s, %s)
                    RETURNING run_id;
                    """,
                    (PIPELINE_NAME, BATCH_FILE.name, len(rows)),
                )
                run_id = cursor.fetchone()[0]

        inserted_count = 0

        # All item inserts are committed together or rolled back together.
        with connection:
            with connection.cursor() as cursor:
                for row in rows:
                    cursor.execute(
                        """
                        INSERT INTO order_items (
                            order_id,
                            order_item_id,
                            product_id,
                            seller_id,
                            shipping_limit_date,
                            price,
                            freight_value
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (order_id, order_item_id) DO NOTHING
                        RETURNING order_id;
                        """,
                        (
                            row["order_id"],
                            int(row["order_item_id"]),
                            row["product_id"].strip() or None,
                            row["seller_id"].strip() or None,
                            row["shipping_limit_date"].strip() or None,
                            row["price"].strip() or None,
                            row["freight_value"].strip() or None,
                        ),
                    )

                    if cursor.fetchone() is not None:
                        inserted_count += 1

        unchanged_count = len(rows) - inserted_count

        with connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE etl_run_log
                    SET status = 'SUCCESS',
                        completed_at = CURRENT_TIMESTAMP,
                        rows_processed = %s,
                        inserted_rows = %s,
                        updated_rows = 0,
                        unchanged_rows = %s
                    WHERE run_id = %s;
                    """,
                    (inserted_count, inserted_count, unchanged_count, run_id),
                )

        print(f"ETL run ID: {run_id}")
        print(f"Input rows: {len(rows)}")
        print(f"Inserted rows: {inserted_count}")
        print("Updated rows: 0")
        print(f"Unchanged rows: {unchanged_count}")
        print("Order-items incremental load completed successfully.")

    except Exception as error:
        if run_id is not None:
            try:
                with connection:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            """
                            UPDATE etl_run_log
                            SET status = 'FAILED',
                                completed_at = CURRENT_TIMESTAMP,
                                error_message = %s
                            WHERE run_id = %s;
                            """,
                            (str(error)[:4000], run_id),
                        )
            except Exception as logging_error:
                print(f"Could not record failure: {logging_error}")

        raise

    finally:
        connection.close()


if __name__ == "__main__":
    main()
