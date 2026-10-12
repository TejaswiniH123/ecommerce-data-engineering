
import os
import sys

os.environ["JAVA_HOME"] = (
    r"C:\Program Files\Eclipse Adoptium\jdk-11.0.32.101-hotspot"
)
os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

from pyspark.sql import SparkSession
from pyspark.sql.functions import col

spark = (
    SparkSession.builder
    .appName("EcommerceWriteParquet")
    .master("local[2]")
    .config("spark.driver.memory", "512m")
    .config("spark.sql.shuffle.partitions", "2")
    .config("spark.pyspark.python", sys.executable)
    .config("spark.pyspark.driver.python", sys.executable)
    .getOrCreate()
)

spark.sparkContext.setLogLevel("ERROR")

try:
    input_path = r"data\raw\olist_order_items_dataset.csv"
    output_path = r"data\processed\parquet\order_items"

    print("Reading raw order-item CSV...")

    df = (
        spark.read
        .option("header", True)
        .option("inferSchema", True)
        .csv(input_path)
    )

    original_count = df.count()

    print(f"Original rows: {original_count}")

    print("Applying basic data quality filters...")

    cleaned_df = df.filter(
        col("order_id").isNotNull()
        & col("product_id").isNotNull()
        & col("price").isNotNull()
        & (col("price") >= 0)
    )

    cleaned_count = cleaned_df.count()

    print(f"Rows after filtering: {cleaned_count}")
    print(f"Rows removed: {original_count - cleaned_count}")

    print("Writing Parquet output...")

    (
        cleaned_df.write
        .mode("overwrite")
        .parquet(output_path)
    )

    print("Reading Parquet back for verification...")

    parquet_df = spark.read.parquet(output_path)
    parquet_count = parquet_df.count()

    print(f"Parquet row count: {parquet_count}")
    print(f"Parquet columns: {parquet_df.columns}")

    if cleaned_count != parquet_count:
        raise ValueError("Parquet row count does not match cleaned row count.")

    print("SUCCESS: Parquet output verified.")

finally:
    spark.stop()
