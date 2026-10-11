
import csv
from collections import Counter, defaultdict
from pathlib import Path

FILE_PATH = Path("data/raw/olist_order_reviews_dataset.csv")


def main():
    review_id_counts = Counter()
    order_id_counts = Counter()
    full_row_counts = Counter()
    review_ids_by_order = defaultdict(set)

    with FILE_PATH.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            review_id_counts[row["review_id"]] += 1
            order_id_counts[row["order_id"]] += 1

            full_row = tuple(row[column] for column in reader.fieldnames)
            full_row_counts[full_row] += 1

            review_ids_by_order[row["order_id"]].add(row["review_id"])

    repeated_review_ids = sum(
        count > 1 for count in review_id_counts.values()
    )

    exact_duplicate_extra_rows = sum(
        count - 1 for count in full_row_counts.values() if count > 1
    )

    orders_with_multiple_review_rows = sum(
        count > 1 for count in order_id_counts.values()
    )

    orders_with_multiple_review_ids = sum(
        len(review_ids) > 1
        for review_ids in review_ids_by_order.values()
    )

    print(f"Total review rows: {sum(review_id_counts.values()):,}")
    print(f"Repeated review IDs: {repeated_review_ids:,}")
    print(f"Exact duplicate extra rows: {exact_duplicate_extra_rows:,}")
    print(
        "Orders with multiple review rows: "
        f"{orders_with_multiple_review_rows:,}"
    )
    print(
        "Orders with multiple distinct review IDs: "
        f"{orders_with_multiple_review_ids:,}"
    )


if __name__ == "__main__":
    main()
