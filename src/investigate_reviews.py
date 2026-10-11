
import csv
from collections import Counter, defaultdict
from pathlib import Path

FILE_PATH = Path("data/raw/olist_order_reviews_dataset.csv")


def main():
    review_counts = Counter()
    review_examples = defaultdict(list)

    with FILE_PATH.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            review_id = row["review_id"]
            review_counts[review_id] += 1

            if len(review_examples[review_id]) < 3:
                review_examples[review_id].append({
                    "order_id": row["order_id"],
                    "review_score": row["review_score"],
                    "review_creation_date": row["review_creation_date"],
                    "review_answer_timestamp": row["review_answer_timestamp"],
                })

    duplicates = {
        review_id: count
        for review_id, count in review_counts.items()
        if count > 1
    }

    print(f"Total review rows: {sum(review_counts.values()):,}")
    print(f"Unique review IDs: {len(review_counts):,}")
    print(f"Review IDs appearing more than once: {len(duplicates):,}")
    print(
        "Extra occurrences beyond the first: "
        f"{sum(count - 1 for count in duplicates.values()):,}"
    )

    print("\nFirst 10 duplicated review IDs:")

    for review_id, count in list(duplicates.items())[:10]:
        print(f"\nReview ID: {review_id} | Occurrences: {count}")

        for example in review_examples[review_id]:
            print(f"  {example}")


if __name__ == "__main__":
    main()
