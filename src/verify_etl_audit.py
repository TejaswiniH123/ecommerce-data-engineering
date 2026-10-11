
import os
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

REQUIRED_PIPELINES = [
    "customers_incremental_load",
    "orders_upsert_load",
    "order_items_incremental_load",
]

def main():
    connection = None

    try:
        connection = psycopg2.connect(
            host=os.getenv("PGHOST", "localhost"),
            port=os.getenv("PGPORT", "5432"),
            dbname=os.getenv("PGDATABASE", "ecommerce_dw"),
            user=os.getenv("PGUSER", "postgres"),
            password=os.getenv("PGPASSWORD"),
        )

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT DISTINCT ON (pipeline_name)
                    pipeline_name,
                    run_id,
                    status,
                    input_rows,
                    inserted_rows,
                    updated_rows,
                    unchanged_rows,
                    started_at
                FROM etl_run_log
                WHERE pipeline_name = ANY(%s)
                ORDER BY pipeline_name, run_id DESC;
                """,
                (REQUIRED_PIPELINES,),
            )

            rows = cursor.fetchall()

        latest_runs = {row[0]: row for row in rows}
        all_passed = True

        print("=" * 75)
        print("LATEST INCREMENTAL ETL AUDIT")
        print("=" * 75)

        for pipeline in REQUIRED_PIPELINES:
            row = latest_runs.get(pipeline)

            if row is None:
                print(f"FAIL: No audit record found for {pipeline}")
                all_passed = False
                continue

            (
                name, run_id, status, input_rows,
                inserted_rows, updated_rows,
                unchanged_rows, started_at
            ) = row

            print(f"\nPipeline: {name}")
            print(f"Run ID: {run_id}")
            print(f"Status: {status}")
            print(f"Input: {input_rows}")
            print(f"Inserted: {inserted_rows}")
            print(f"Updated: {updated_rows}")
            print(f"Unchanged: {unchanged_rows}")

            if status != "SUCCESS":
                print("FAIL: Latest run was not successful")
                all_passed = False
            else:
                print("PASS: Latest run succeeded")

        print("\n" + "=" * 75)

        if all_passed:
            print("SUCCESS: All incremental pipeline audit checks passed.")
        else:
            print("FAILURE: One or more audit checks failed.")
            sys.exit(1)

    except Exception as error:
        print(f"Audit verification failed: {error}")
        sys.exit(1)

    finally:
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    main()
