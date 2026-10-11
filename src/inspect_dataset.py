import csv
from pathlib import Path

RAW_DIR = Path("data") / "raw"

FILES_TO_INSPECT = [
    "olist_customers_dataset.csv",
    "olist_orders_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_products_dataset.csv",
    "olist_sellers_dataset.csv",
    "olist_order_reviews_dataset.csv",
    "product_category_name_translation.csv",
]

FILES_TO_COUNT = {
    "olist_customers_dataset.csv",
    "olist_orders_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_products_dataset.csv",
    "olist_sellers_dataset.csv",
    "olist_order_reviews_dataset.csv",
}


def inspect_csv(filename):
    path = RAW_DIR / filename

    print("\n" + "=" * 70)
    print(f"FILE: {filename}")

    if not path.exists():
        print("ERROR: File not found.")
        return

    size_mb = path.stat().st_size / (1024 * 1024)
    print(f"Size: {size_mb:.2f} MB")

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        headers = reader.fieldnames

        if not headers:
            print("ERROR: No CSV headers found.")
            return

        print(f"Columns ({len(headers)}): {headers}")

        print("Sample rows:")
        for row_number, row in enumerate(reader, start=1):
            if row_number <= 2:
                print(f"  Row {row_number}: {row}")

    if filename in FILES_TO_COUNT:
        with path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.reader(file)
            next(reader, None)
            row_count = sum(1 for _ in reader)

        print(f"Data rows: {row_count:,}")
    else:
        print("Data row count: Not calculated in this inspection.")


def main():
    if not RAW_DIR.exists():
        raise FileNotFoundError(
            f"Raw data directory not found: {RAW_DIR.resolve()}"
        )

    print("OLIST DATASET INSPECTION")
    print(f"Raw data directory: {RAW_DIR.resolve()}")

    for filename in FILES_TO_INSPECT:
        inspect_csv(filename)

    print("\n" + "=" * 70)
    print("Inspection completed.")


if __name__ == "__main__":
    main()
