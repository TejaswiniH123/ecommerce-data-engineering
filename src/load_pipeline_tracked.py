
import os
import subprocess
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv


# Locate the project directory.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

PIPELINE_NAME = "ecommerce_full_refresh"
SOURCE_NAME = "olist_csv_dataset"

TABLES = [
    "customers",
    "orders",
    "products",
    "sellers",
    "order_items",
    "payments",
    "reviews",
    "product_category_translation",
]


def get_connection():
    """Connect to the PostgreSQL database using .env settings."""
    return psycopg2.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=os.getenv("PGPORT", "5432"),
        dbname=os.getenv("PGDATABASE", "ecommerce_dw"),
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD"),
    )


def main():
    connection = get_connection()
    run_id = None

    try:
        # Record that a new pipeline run has started.
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO etl_run_log
                        (pipeline_name, load_type, status, source_name)
                    VALUES (%s, %s, %s, %s)
                    RETURNING run_id;
                    """,
                    (
                        PIPELINE_NAME,
                        "FULL_REFRESH",
                        "RUNNING",
                        SOURCE_NAME,
                    ),
                )
                run_id = cursor.fetchone()[0]

        print(f"Started ETL run ID: {run_id}")

        # Run the existing, tested pipeline without modifying it.
        result = subprocess.run(
            [
                sys.executable,
                str(PROJECT_ROOT / "src" / "load_pipeline.py"),
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.stdout:
            print(result.stdout)

        if result.stderr:
            print(result.stderr)

        if result.returncode != 0:
            raise RuntimeError(
                f"Existing pipeline failed with exit code "
                f"{result.returncode}."
            )

        # Count rows only after the original pipeline succeeds.
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT COALESCE(SUM(row_count), 0)
                    FROM (
                        SELECT COUNT(*) AS row_count FROM customers
                        UNION ALL
                        SELECT COUNT(*) FROM orders
                        UNION ALL
                        SELECT COUNT(*) FROM products
                        UNION ALL
                        SELECT COUNT(*) FROM sellers
                        UNION ALL
                        SELECT COUNT(*) FROM order_items
                        UNION ALL
                        SELECT COUNT(*) FROM payments
                        UNION ALL
                        SELECT COUNT(*) FROM reviews
                        UNION ALL
                        SELECT COUNT(*) FROM product_category_translation
                    ) AS table_counts;
                    """
                )
                rows_processed = cursor.fetchone()[0]

                cursor.execute(
                    """
                    UPDATE etl_run_log
                    SET status = 'SUCCESS',
                        completed_at = CURRENT_TIMESTAMP,
                        rows_processed = %s
                    WHERE run_id = %s;
                    """,
                    (rows_processed, run_id),
                )

        print(f"ETL run {run_id} completed successfully.")
        print(f"Rows present across all eight tables: {rows_processed}")

    except Exception as error:
        # Record the failure without hiding the original error.
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

        print(f"ETL run failed: {error}")
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    main()
