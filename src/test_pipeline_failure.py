
import sys

import run_incremental_pipeline as pipeline


def main():
    # Save the real pipeline configuration.
    original_steps = pipeline.PIPELINE_STEPS

    try:
        # Use a deliberately nonexistent script for the test.
        pipeline.PIPELINE_STEPS = [
            ("Intentional failure test", "src/this_script_does_not_exist.py"),
            ("Must not run", "src/should_not_run.py"),
        ]

        try:
            pipeline.run_steps()
        except FileNotFoundError as error:
            print(f"PASS: Missing script detected: {error}")
        else:
            raise AssertionError("Expected FileNotFoundError was not raised")

        # Confirm the second step was never reached.
        print("PASS: Pipeline stopped before the next step")

    finally:
        # Restore the original configuration in memory.
        pipeline.PIPELINE_STEPS = original_steps


if __name__ == "__main__":
    main()
