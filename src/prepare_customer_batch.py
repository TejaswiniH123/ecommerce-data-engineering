
import csv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

source_file = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "olist_customers_dataset.csv"
)

incoming_dir = PROJECT_ROOT / "data" / "incoming"
incoming_dir.mkdir(parents=True, exist_ok=True)

output_file = incoming_dir / "customers_batch.csv"

# Copy five existing source records for our first test.
with source_file.open("r", encoding="utf-8-sig", newline="") as source:
    reader = csv.DictReader(source)
    rows = []

    for row in reader:
        rows.append(row)
        if len(rows) == 5:
            break

if len(rows) != 5:
    raise ValueError("Expected at least five customer records.")

with output_file.open("w", encoding="utf-8", newline="") as output:
    writer = csv.DictWriter(output, fieldnames=reader.fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"Created test batch: {output_file}")
print(f"Records in batch: {len(rows)}")
print("These five customer records already exist in the source dataset.")
