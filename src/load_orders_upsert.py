
import csv
import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

BATCH_FILE = PROJECT_ROOT / "data" / "incoming" / "orders_batch.csv"
PIPELINE_NAME = "orders_upsert_load"

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

    order_ids = [row["order_id"] for row in rows]

    if any(not value for value in order_ids):
        raise ValueError("Every record must have an order_id.")

    if any(not row["customer_id"] for row in rows):
        raise ValueError("Every order must have a customer_id.")

    if len(order_ids) != len(set(order_ids)):
        raise ValueError("Batch contains duplicate order_id values.")

    connection = get_connection()
    run_id = None

    try:
        # Keep the audit record separate from the data transaction.
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
        updated_count = 0
        unchanged_count = 0

        with connection:
            with connection.cursor() as cursor:
                for row in rows:
                    values = tuple(row[column] or None for column in COLUMNS)

                    # Determine whether this order already exists.
                    cursor.execute(
                        "SELECT 1 FROM orders WHERE order_id = %s;",
                        (row["order_id"],),
                    )
                    exists = cursor.fetchone() is not None

                    if not exists:
                        cursor.execute(
                            """
                            INSERT INTO orders (
                                order_id, customer_id, order_status,
                                order_purchase_timestamp, order_approved_at,
                                order_delivered_carrier_date,
                                order_delivered_customer_date,
                                order_estimated_delivery_date
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (order_id) DO NOTHING
                            RETURNING order_id;
                            """,
                            values,
                        )

                        if cursor.fetchone() is not None:
                            inserted_count += 1
                        else:
                            # Handles a concurrent insert safely.
                            unchanged_count += 1

                    else:
                        cursor.execute(
                            """
                            UPDATE orders
                            SET customer_id = %s,
                                order_status = %s,
                                order_purchase_timestamp = %s,
                                order_approved_at = %s,
                                order_delivered_carrier_date = %s,
                                order_delivered_customer_date = %s,
                                order_estimated_delivery_date = %s
                            WHERE order_id = %s
                              AND (
                                  customer_id,
                                  order_status,
                                  order_purchase_timestamp,
                                  order_approved_at,
                                  order_delivered_carrier_date,
                                  order_delivered_customer_date,
                                  order_estimated_delivery_date
                              ) IS DISTINCT FROM (
                                  %s, %s, %s, %s, %s, %s, %s
                              )
                            RETURNING order_id;
                            """,
                            (
                                *values[1:],
                                values[0],
                                *values[1:],
                            ),
                        )

                        if cursor.fetchone() is not None:
                            updated_count += 1
                        else:
                            unchanged_count += 1

        affected_count = inserted_count + updated_count

        with connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE etl_run_log
                    SET status = 'SUCCESS',
                        completed_at = CURRENT_TIMESTAMP,
                        rows_processed = %s,
                        inserted_rows = %s,
                        updated_rows = %s,
                        unchanged_rows = %s
                    WHERE run_id = %s;
                    """,
                    (
                        affected_count,
                        inserted_count,
                        updated_count,
                        unchanged_count,
                        run_id,
                    ),
                )

        print(f"ETL run ID: {run_id}")
        print(f"Input rows: {len(rows)}")
        print(f"Inserted rows: {inserted_count}")
        print(f"Updated rows: {updated_count}")
        print(f"Unchanged rows: {unchanged_count}")
        print("Orders upsert completed successfully.")

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
