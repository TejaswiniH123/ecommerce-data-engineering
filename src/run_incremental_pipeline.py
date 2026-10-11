
import os
import subprocess
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

PIPELINE_NAME = "incremental_pipeline_orchestrator"

# Run parent tables before dependent tables.
PIPELINE_STEPS = [
    ("Customers", "src/load_customers_incremental.py"),
    ("Orders", "src/load_orders_upsert.py"),
    ("Order items", "src/load_order_items_incremental.py"),
]


def get_connection():
    """Connect to the project's PostgreSQL database."""
    return psycopg2.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=os.getenv("PGPORT", "5432"),
        dbname=os.getenv("PGDATABASE", "ecommerce_dw"),
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD"),
    )


def start_audit_run(connection):
    """Create a parent audit record before running any steps."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO etl_run_log (
                pipeline_name,
                load_type,
                status,
                source_name
            )
            VALUES (%s, %s, %s, %s)
            RETURNING run_id;
            """,
            (
                PIPELINE_NAME,
                "INCREMENTAL",
                "RUNNING",
                "src/run_incremental_pipeline.py",
            ),
        )
        run_id = cursor.fetchone()[0]

    connection.commit()
    return run_id


def finish_audit_run(connection, run_id, status, error_message=None):
    """Record the final status of the overall pipeline."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE etl_run_log
            SET status = %s,
                completed_at = CURRENT_TIMESTAMP,
                error_message = %s
            WHERE run_id = %s;
            """,
            (status, error_message, run_id),
        )

    connection.commit()


def run_steps():
    """Execute pipeline steps in dependency order."""
    print("=" * 60)
    print("ECOMMERCE INCREMENTAL PIPELINE")
    print("=" * 60)

    for step_number, (step_name, script_path) in enumerate(
        PIPELINE_STEPS, start=1
    ):
        script_file = PROJECT_ROOT / script_path

        if not script_file.exists():
            raise FileNotFoundError(
                f"Pipeline script not found: {script_file}"
            )

        print(f"\nStep {step_number}/{len(PIPELINE_STEPS)}: {step_name}")
        print("-" * 60)

        result = subprocess.run(
            [sys.executable, str(script_file)],
            cwd=PROJECT_ROOT,
            check=False,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"{step_name} failed with exit code "
                f"{result.returncode}. Remaining steps were not run."
            )

        print(f"PASSED: {step_name}")

    print("\nALL INCREMENTAL PIPELINE STEPS COMPLETED")


def main():
    connection = None
    run_id = None

    try:
        connection = get_connection()
        run_id = start_audit_run(connection)

        print(f"Parent audit run ID: {run_id}")

        run_steps()

        finish_audit_run(connection, run_id, "SUCCESS")
        print(f"Parent audit status: SUCCESS (run ID {run_id})")

    except Exception as error:
        print(f"\nPIPELINE FAILED: {error}")

        if connection is not None and run_id is not None:
            try:
                finish_audit_run(
                    connection,
                    run_id,
                    "FAILED",
                    str(error)[:5000],
                )
                print(f"Parent audit status: FAILED (run ID {run_id})")
            except Exception as audit_error:
                print(f"Could not update audit record: {audit_error}")

        sys.exit(1)

    finally:
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    main()
