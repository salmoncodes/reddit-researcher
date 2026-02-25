"""Export data to CSV."""

import csv
from pathlib import Path


def export_table(storage, table_name, output_path):
    """Export a table to CSV."""
    data = storage.export_table(table_name)

    if not data:
        print(f"No data in table: {table_name}")
        return

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

    print(f"Exported {len(data)} rows to {output_path}")


def export_all(storage, output_dir):
    """Export all tables to CSV."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    tables = ["posts", "subreddits", "post_tags"]

    # Check if comments table has data
    comments = storage.export_table("comments")
    if comments:
        tables.append("comments")

    for table in tables:
        export_table(storage, table, output_dir / f"{table}.csv")
