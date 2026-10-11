
import csv
from collections import Counter
from pathlib import Path

RAW_DIR = Path("data") / "raw"


def profile_file(filename, key_columns):
    path = RAW_DIR / filename
    row_count = 0
    missing = Counter()
    key_counts = Counter()
    status_counts = Counter()

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            row_count += 1

            for column, value in row.items():
                if value is None or value.strip() == "":
                    missing[column] += 1

            key = tuple(row.get(column, "") for column in key_columns)

            if any(value.strip() == "" for value in key):
                key_counts["missing_key"] += 1
            else:
                key_counts[key] += 1

            if "order_status" in row:
                status_counts[row["order_status"]] += 1

    duplicate_keys = sum(
        count - 1
        for key, count in key_counts.items()
        if isinstance(key, tuple) and count > 1
    )

    print(f"\n{'=' * 65}")
    print(f"FILE: {filename}")
    print(f"Rows: {row_count:,}")
    print(f"Missing required key rows: {key_counts['missing_key']:,}")
    print(f"Duplicate key occurrences: {duplicate_keys:,}")

    print("Missing values by column:")
    for column, count in sorted(missing.items()):
        print(f"  {column}: {count:,}")

    if status_counts:
        print("Order status distribution:")
        for status, count in sorted(status_counts.items()):
            print(f"  {status}: {count:,}")


def main():
    checks = [
        ("olist_customers_dataset.csv", ["customer_id"]),
        ("olist_orders_dataset.csv", ["order_id"]),
        ("olist_order_items_dataset.csv", ["order_id", "order_item_id"]),
        ("olist_order_payments_dataset.csv", ["order_id", "payment_sequential"]),
        ("olist_products_dataset.csv", ["product_id"]),
        ("olist_sellers_dataset.csv", ["seller_id"]),
        ("olist_order_reviews_dataset.csv", ["review_id"]),
    ]

    for filename, keys in checks:
        profile_file(filename, keys)

    print("\nSource profiling completed.")


if __name__ == "__main__":
    main()
