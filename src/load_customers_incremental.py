
import csv
import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

BATCH_FILE = PROJECT_ROOT / "data" / "incoming" / "customers_batch.csv"
PIPELINE_NAME = "customers_incremental_load"

COLUMNS = [
    "customer_id",
    "customer_unique_id",
    "customer_zip_code_prefix",
    "customer_city",
    "customer_state",
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
        raise FileNotFoundError(f"Batch file not found: {BATCH_FILE}")

    with BATCH_FILE.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames or not set(COLUMNS).issubset(reader.fieldnames):
            raise ValueError("Customer CSV is missing required columns.")

        rows = list(reader)

    if not rows:
        raise ValueError("Customer batch is empty.")

    customer_ids = [row["customer_id"] for row in rows]

    if any(not customer_id for customer_id in customer_ids):
        raise ValueError("Every customer must have a customer_id.")

    if len(customer_ids) != len(set(customer_ids)):
        raise ValueError("Batch contains duplicate customer_id values.")

    connection = get_connection()
    run_id = None

    try:
        # Audit record is committed separately so failures remain visible.
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

        # All customer inserts are part of one transaction.
        with connection:
            with connection.cursor() as cursor:
                for row in rows:
                    cursor.execute(
                        """
                        INSERT INTO customers (
                            customer_id,
                            customer_unique_id,
                            customer_zip_code_prefix,
                            customer_city,
                            customer_state
                        )
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (customer_id) DO NOTHING
                        RETURNING customer_id;
                        """,
                        tuple(row[column] or None for column in COLUMNS),
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
                        unchanged_rows = %s,
                        updated_rows = 0
                    WHERE run_id = %s;
                    """,
                    (inserted_count, inserted_count, unchanged_count, run_id),
                )

        print(f"ETL run ID: {run_id}")
        print(f"Input rows: {len(rows)}")
        print(f"Inserted rows: {inserted_count}")
        print("Updated rows: 0")
        print(f"Unchanged rows: {unchanged_count}")
        print("Customer incremental load completed successfully.")

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
