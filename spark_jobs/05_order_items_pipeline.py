
import os
import sys
import json
import argparse
from datetime import datetime, timezone
from order_items_validation import split_valid_and_invalid

os.environ["JAVA_HOME"] = (
    r"C:\Program Files\Eclipse Adoptium\jdk-11.0.32.101-hotspot"
)
os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    IntegerType,
    TimestampType,
    DecimalType,
)
from pyspark.sql.functions import col


# Command-line configuration
parser = argparse.ArgumentParser(
    description="Process and validate Olist order-item data."
)

parser.add_argument(
    "--input",
    default=r"data\raw\olist_order_items_dataset.csv",
    help="Path to the source CSV file.",
)

parser.add_argument(
    "--output",
    default=r"data\processed\parquet\validated_order_items",
    help="Directory for validated Parquet data.",
)

parser.add_argument(
    "--rejected",
    default=r"data\processed\rejected\order_items",
    help="Directory for rejected records.",
)

parser.add_argument(
    "--report",
    default=r"data\processed\reports\order_items_run_summary.json",
    help="Path for the JSON execution report.",
)

args = parser.parse_args()

INPUT_PATH = args.input
OUTPUT_PATH = args.output
REJECT_PATH = args.rejected
REPORT_PATH = args.report


def write_report(report):
    """Write the pipeline execution summary to a JSON file."""
    report_directory = os.path.dirname(REPORT_PATH)
    if report_directory:
        os.makedirs(report_directory, exist_ok=True)

    with open(REPORT_PATH, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)


def main():
    started_at = datetime.now(timezone.utc).isoformat()

    report = {
        "pipeline_name": "order_items_spark_pipeline",
        "status": "FAILURE",
        "started_at_utc": started_at,
        "finished_at_utc": None,
        "input_rows": None,
        "valid_rows": None,
        "rejected_rows": None,
        "parquet_output_rows": None,
        "source": INPUT_PATH,
        "output": OUTPUT_PATH,
        "rejected_output": REJECT_PATH,
        "error_message": None,
    }

    spark = None

    try:
        spark = (
            SparkSession.builder
            .appName("EcommerceOrderItemsPipeline")
            .master("local[2]")
            .config("spark.driver.memory", "512m")
            .config("spark.sql.shuffle.partitions", "2")
            .config("spark.pyspark.python", sys.executable)
            .config("spark.pyspark.driver.python", sys.executable)
            .getOrCreate()
        )

        spark.sparkContext.setLogLevel("ERROR")

        schema = StructType([
            StructField("order_id", StringType(), True),
            StructField("order_item_id", IntegerType(), True),
            StructField("product_id", StringType(), True),
            StructField("seller_id", StringType(), True),
            StructField("shipping_limit_date", TimestampType(), True),
            StructField("price", DecimalType(12, 2), True),
            StructField("freight_value", DecimalType(12, 2), True),
        ])

        print("Reading source CSV...")

        df = (
            spark.read
            .option("header", True)
            .option("timestampFormat", "yyyy-MM-dd HH:mm:ss")
            .schema(schema)
            .csv(INPUT_PATH)
        )

        input_rows = df.count()
        valid_df, rejected_df = split_valid_and_invalid(df)

        valid_rows = valid_df.count()
        rejected_rows = input_rows - valid_rows

        if input_rows != valid_rows + rejected_rows:
            raise RuntimeError(
                "Validation count mismatch: input rows must equal "
                "valid rows plus rejected rows."
            )

        report.update({
            "input_rows": input_rows,
            "valid_rows": valid_rows,
            "rejected_rows": rejected_rows,
        })

        print(f"Input rows: {input_rows}")
        print(f"Valid rows: {valid_rows}")
        print(f"Rejected rows: {rejected_rows}")

        if rejected_rows > 0:
            (
                rejected_df.write
                .mode("overwrite")
                .option("header", True)
                .csv(REJECT_PATH)
            )
            print(f"Rejected records written to: {REJECT_PATH}")
            report["rejected_output"] = REJECT_PATH
        else:
    # Remove rejected records left by an earlier run.
            if os.path.exists(REJECT_PATH):
                import shutil
                shutil.rmtree(REJECT_PATH)

            print("No rejected records found.")
            report["rejected_output"] = None
        (
            valid_df.write
            .mode("overwrite")
            .parquet(OUTPUT_PATH)
        )

        output_rows = spark.read.parquet(OUTPUT_PATH).count()

        if output_rows != valid_rows:
            raise RuntimeError(
                f"Row count mismatch: expected {valid_rows}, "
                f"found {output_rows}"
            )

        report["parquet_output_rows"] = output_rows
        report["status"] = "SUCCESS"

        print("SUCCESS: Pipeline completed and output verified.")

    except Exception as exc:
        report["status"] = "FAILURE"
        report["error_message"] = f"{type(exc).__name__}: {exc}"
        print(f"PIPELINE FAILED: {report['error_message']}")

    finally:
        report["finished_at_utc"] = datetime.now(timezone.utc).isoformat()

        try:
            write_report(report)
            print("\n--- Pipeline summary ---")
            print(json.dumps(report, indent=2))
            print(f"\nExecution report written to: {REPORT_PATH}")
        except Exception as report_error:
            print(f"Could not write execution report: {report_error}")
            report["status"] = "FAILURE"

        if spark is not None:
            try:
                spark.stop()
            except Exception as stop_error:
                print(f"Warning: Spark shutdown failed: {stop_error}")
                report["status"] = "FAILURE"

    if report["status"] != "SUCCESS":
        sys.exit(1)


if __name__ == "__main__":
    main()
