import os
import sys

# Use the JDK already configured for this project.
os.environ["JAVA_HOME"] = r"C:\Program Files\Eclipse Adoptium\jdk-11.0.32.101-hotspot"

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, sum as spark_sum

spark = (
    SparkSession.builder
    .appName("EcommerceSparkSmokeTest")
    .master("local[2]")
    .config("spark.driver.memory", "512m")
    .config("spark.sql.shuffle.partitions", "2")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("ERROR")

try:
    orders = [
        (101, "delivered", 250.0),
        (102, "delivered", 400.0),
        (103, "canceled", 150.0),
        (104, "delivered", 300.0),
    ]

    columns = ["order_id", "status", "item_sales"]

    df = spark.createDataFrame(orders, columns)

    print("\n--- Sample order data ---")
    df.show()

    print("\n--- Delivered sales summary ---")
    summary = (
        df.filter(col("status") == "delivered")
        .agg(spark_sum("item_sales").alias("delivered_item_sales"))
    )

    summary.show()

    delivered_count = df.filter(
        col("status") == "delivered"
    ).count()

    print(f"Delivered orders: {delivered_count}")

finally:
    spark.stop()
