
import os
import sys
from datetime import datetime
from decimal import Decimal

import pytest
from pyspark.sql import SparkSession

# Ensure Python workers use this project's virtual environment.
os.environ["JAVA_HOME"] = (
    r"C:\Program Files\Eclipse Adoptium\jdk-11.0.32.101-hotspot"
)
os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

from spark_jobs.order_items_validation import split_valid_and_invalid


@pytest.fixture(scope="module")
def spark():
    session = (
        SparkSession.builder
        .appName("OrderItemsValidationTests")
        .master("local[2]")
        .config("spark.driver.memory", "512m")
        .config("spark.sql.shuffle.partitions", "2")
        .config("spark.pyspark.python", sys.executable)
        .config("spark.pyspark.driver.python", sys.executable)
        .getOrCreate()
    )

    session.sparkContext.setLogLevel("ERROR")

    yield session

    session.stop()


@pytest.fixture
def sample_schema():
    from pyspark.sql.types import (
        StructType,
        StructField,
        StringType,
        IntegerType,
        TimestampType,
        DecimalType,
    )

    return StructType([
        StructField("order_id", StringType(), True),
        StructField("order_item_id", IntegerType(), True),
        StructField("product_id", StringType(), True),
        StructField("seller_id", StringType(), True),
        StructField("shipping_limit_date", TimestampType(), True),
        StructField("price", DecimalType(12, 2), True),
        StructField("freight_value", DecimalType(12, 2), True),
    ])


def make_row(
    order_id="test_order",
    order_item_id=1,
    product_id="test_product",
    seller_id="test_seller",
    price=Decimal("100.00"),
    freight_value=Decimal("10.00"),
):
    return (
        order_id,
        order_item_id,
        product_id,
        seller_id,
        datetime(2018, 1, 1, 10, 0, 0),
        price,
        freight_value,
    )


def test_valid_record_passes(spark, sample_schema):
    df = spark.createDataFrame(
        [make_row()],
        schema=sample_schema,
    )

    valid_df, rejected_df = split_valid_and_invalid(df)

    assert valid_df.count() == 1
    assert rejected_df.count() == 0


def test_negative_price_is_rejected(spark, sample_schema):
    df = spark.createDataFrame(
        [make_row(price=Decimal("-50.00"))],
        schema=sample_schema,
    )

    valid_df, rejected_df = split_valid_and_invalid(df)

    assert valid_df.count() == 0
    assert rejected_df.count() == 1


def test_null_order_id_is_rejected(spark, sample_schema):
    df = spark.createDataFrame(
        [make_row(order_id=None)],
        schema=sample_schema,
    )

    valid_df, rejected_df = split_valid_and_invalid(df)

    assert valid_df.count() == 0
    assert rejected_df.count() == 1


def test_zero_order_item_id_is_rejected(spark, sample_schema):
    df = spark.createDataFrame(
        [make_row(order_item_id=0)],
        schema=sample_schema,
    )

    valid_df, rejected_df = split_valid_and_invalid(df)

    assert valid_df.count() == 0
    assert rejected_df.count() == 1


def test_input_count_equals_valid_plus_rejected(
    spark,
    sample_schema,
):
    rows = [
        make_row(order_id="valid_1"),
        make_row(order_id="valid_2"),
        make_row(
            order_id="invalid_1",
            price=Decimal("-1.00"),
        ),
    ]

    df = spark.createDataFrame(rows, schema=sample_schema)

    valid_df, rejected_df = split_valid_and_invalid(df)

    assert df.count() == valid_df.count() + rejected_df.count()
    assert valid_df.count() == 2
    assert rejected_df.count() == 1
