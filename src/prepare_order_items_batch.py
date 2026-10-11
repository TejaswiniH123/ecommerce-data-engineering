
import csv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

source_file = (
    PROJECT_ROOT / "data" / "raw" / "olist_order_items_dataset.csv"
)
output_file = PROJECT_ROOT / "data" / "incoming" / "order_items_batch.csv"

output_file.parent.mkdir(parents=True, exist_ok=True)

with source_file.open("r", encoding="utf-8-sig", newline="") as source:
    reader = csv.DictReader(source)
    fieldnames = reader.fieldnames
    rows = []

    for row in reader:
        rows.append(row)
        if len(rows) == 5:
            break

if not fieldnames or len(rows) != 5:
    raise ValueError("Could not read five order-item records.")

with output_file.open("w", encoding="utf-8", newline="") as output:
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"Created: {output_file}")
print(f"Records: {len(rows)}")
