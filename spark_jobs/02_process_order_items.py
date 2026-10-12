
import os
import sys

os.environ["JAVA_HOME"] = (
    r"C:\Program Files\Eclipse Adoptium\jdk-11.0.32.101-hotspot"
)
os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, sum as spark_sum

spark = (
    SparkSession.builder
    .appName("EcommerceOrderItemsProcessing")
    .master("local[2]")
    .config("spark.driver.memory", "512m")
    .config("spark.sql.shuffle.partitions", "2")
    .config("spark.pyspark.python", sys.executable)
    .config("spark.pyspark.driver.python", sys.executable)
    .getOrCreate()
)

spark.sparkContext.setLogLevel("ERROR")

try:
    file_path = (
        r"data\raw\olist_order_items_dataset.csv"
    )

    print("\n--- Reading order items CSV ---")

    df = (
        spark.read
        .option("header", True)
        .option("inferSchema", True)
        .csv(file_path)
    )

    print("\n--- Schema ---")
    df.printSchema()

    print("\n--- First 5 records ---")
    df.show(5, truncate=False)

    print("\n--- Total rows ---")
    print(f"Total order items: {df.count()}")

    print("\n--- Data quality checks ---")
    print(f"Null order IDs: {df.filter(col('order_id').isNull()).count()}")
    print(f"Null product IDs: {df.filter(col('product_id').isNull()).count()}")
    print(f"Null prices: {df.filter(col('price').isNull()).count()}")

    print("\n--- Summary by product ---")

    product_summary = (
        df.groupBy("product_id")
        .agg(
            count("*").alias("total_items"),
            spark_sum("price").alias("total_item_sales")
        )
        .orderBy(col("total_item_sales").desc())
    )

    product_summary.show(10, truncate=False)

finally:
    spark.stop()
