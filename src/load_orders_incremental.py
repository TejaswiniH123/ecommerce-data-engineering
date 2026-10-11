
import csv
import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

BATCH_FILE = PROJECT_ROOT / "data" / "incoming" / "orders_batch.csv"
PIPELINE_NAME = "orders_incremental_load"

COLUMNS = [
    "order_id",
    "customer_id",
    "order_status",
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
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
            raise ValueError("Orders CSV is missing required columns.")

        rows = list(reader)

    if not rows:
        raise ValueError("Orders batch is empty.")

    if any(not row["order_id"] or not row["customer_id"] for row in rows):
        raise ValueError("Every order must have an order_id and customer_id.")

    order_ids = [row["order_id"] for row in rows]
    if len(order_ids) != len(set(order_ids)):
        raise ValueError("Orders batch contains duplicate order_id values.")

    connection = get_connection()
    run_id = None

    try:
        # Create the audit record separately so a later rollback
        # cannot erase the RUNNING record.
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO etl_run_log
                        (pipeline_name, load_type, status, source_name)
                    VALUES (%s, 'INCREMENTAL', 'RUNNING', %s)
                    RETURNING run_id;
                    """,
                    (PIPELINE_NAME, BATCH_FILE.name),
                )
                run_id = cursor.fetchone()[0]

        inserted_count = 0

        # All order inserts belong to one transaction.
        with connection:
            with connection.cursor() as cursor:
                for row in rows:
                    cursor.execute(
                        """
                        INSERT INTO orders (
                            order_id,
                            customer_id,
                            order_status,
                            order_purchase_timestamp,
                            order_approved_at,
                            order_delivered_carrier_date,
                            order_delivered_customer_date,
                            order_estimated_delivery_date
                        )
                        VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s
                        )
                        ON CONFLICT (order_id) DO NOTHING
                        RETURNING order_id;
                        """,
                        tuple(row[column] or None for column in COLUMNS),
                    )

                    if cursor.fetchone() is not None:
                        inserted_count += 1

        with connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE etl_run_log
                    SET status = 'SUCCESS',
                        completed_at = CURRENT_TIMESTAMP,
                        rows_processed = %s
                    WHERE run_id = %s;
                    """,
                    (inserted_count, run_id),
                )

        print(f"ETL run ID: {run_id}")
        print(f"Input records: {len(rows)}")
        print(f"New orders inserted: {inserted_count}")
        print(f"Existing orders skipped: {len(rows) - inserted_count}")
        print("Incremental orders load completed successfully.")

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
