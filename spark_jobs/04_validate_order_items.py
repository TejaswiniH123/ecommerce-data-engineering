
import os
import sys

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
from pyspark.sql.functions import col, count, sum as spark_sum

spark = (
    SparkSession.builder
    .appName("ValidateOrderItems")
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

    # Define the expected schema explicitly.
    schema = StructType([
        StructField("order_id", StringType(), True),
        StructField("order_item_id", IntegerType(), True),
        StructField("product_id", StringType(), True),
        StructField("seller_id", StringType(), True),
        StructField("shipping_limit_date", TimestampType(), True),
        StructField("price", DecimalType(12, 2), True),
        StructField("freight_value", DecimalType(12, 2), True),
    ])

    print("\n--- Reading CSV with explicit schema ---")

    df = (
        spark.read
        .option("header", True)
        .option("timestampFormat", "yyyy-MM-dd HH:mm:ss")
        .schema(schema)
        .csv(input_path)
    )

    df.printSchema()

    total_rows = df.count()

    # Identify records that fail required-field checks.
    invalid_rows = df.filter(
        col("order_id").isNull()
        | col("product_id").isNull()
        | col("seller_id").isNull()
        | col("order_item_id").isNull()
        | col("price").isNull()
        | col("freight_value").isNull()
        | (col("price") < 0)
        | (col("freight_value") < 0)
    )

    invalid_count = invalid_rows.count()

    print("\n--- Data quality report ---")
    print(f"Total rows: {total_rows}")
    print(f"Invalid rows: {invalid_count}")
    print(f"Valid rows: {total_rows - invalid_count}")

    print("\n--- Null counts ---")

    for column_name in df.columns:
        null_count = df.filter(
            col(column_name).isNull()
        ).count()

        print(f"{column_name}: {null_count}")

    print("\n--- Valid data summary ---")

    valid_df = df.filter(
        col("order_id").isNotNull()
        & col("product_id").isNotNull()
        & col("seller_id").isNotNull()
        & col("order_item_id").isNotNull()
        & col("price").isNotNull()
        & col("freight_value").isNotNull()
        & (col("price") >= 0)
        & (col("freight_value") >= 0)
    )

    valid_df.agg(
        count("*").alias("valid_item_count"),
        spark_sum("price").alias("total_item_sales"),
        spark_sum("freight_value").alias("total_freight")
    ).show(truncate=False)

    if invalid_count > 0:
        print("WARNING: Invalid records were found.")
        invalid_rows.show(10, truncate=False)
    else:
        print("SUCCESS: All records passed these validation rules.")

finally:
    spark.stop()
