
import sys

import run_incremental_pipeline as pipeline


def main():
    connection = None
    run_id = None

    try:
        connection = pipeline.get_connection()
        run_id = pipeline.start_audit_run(connection)

        test_error = "TEST ONLY: simulated pipeline failure"

        pipeline.finish_audit_run(
            connection,
            run_id,
            "FAILED",
            test_error,
        )

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT status, error_message, completed_at
                FROM etl_run_log
                WHERE run_id = %s;
                """,
                (run_id,),
            )
            row = cursor.fetchone()

        status, error_message, completed_at = row

        print(f"Test audit run ID: {run_id}")
        print(f"Status: {status}")
        print(f"Error message: {error_message}")
        print(f"Completed at: {completed_at}")

        if (
            status == "FAILED"
            and error_message == test_error
            and completed_at is not None
        ):
            print("PASS: Failed audit status verified")
        else:
            print("FAIL: Audit record did not match expectations")
            sys.exit(1)

    except Exception as error:
        print(f"Audit failure test failed: {error}")
        sys.exit(1)

    finally:
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    main()
