
from pyspark.sql.functions import col


REQUIRED_COLUMNS = [
    "order_id",
    "order_item_id",
    "product_id",
    "seller_id",
    "shipping_limit_date",
    "price",
    "freight_value",
]


def get_invalid_condition():
    """Return the condition that identifies invalid order-item records."""

    invalid_condition = None

    for name in REQUIRED_COLUMNS:
        condition = col(name).isNull()

        invalid_condition = (
            condition
            if invalid_condition is None
            else invalid_condition | condition
        )

    invalid_condition = (
        invalid_condition
        | (col("price") < 0)
        | (col("freight_value") < 0)
        | (col("order_item_id") <= 0)
    )

    return invalid_condition


def split_valid_and_invalid(df):
    """Separate valid records from rejected records."""

    invalid_condition = get_invalid_condition()

    valid_df = df.filter(~invalid_condition)
    rejected_df = df.filter(invalid_condition)

    return valid_df, rejected_df
