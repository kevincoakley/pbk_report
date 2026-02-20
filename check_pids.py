import argparse
import csv
import sys
from typing import Set


def get_ids_from_csv(file_path: str) -> Set[str]:
    """Read the 'id' or 'pid' column from a CSV file and return a set of ids."""
    ids = set()
    try:
        with open(file_path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                print(f"Error: No columns found in {file_path}", file=sys.stderr)
                sys.exit(1)

            id_col = None
            lower_fieldnames = {f.lower(): f for f in reader.fieldnames if f}
            if "id" in lower_fieldnames:
                id_col = lower_fieldnames["id"]
            elif "pid" in lower_fieldnames:
                id_col = lower_fieldnames["pid"]

            if id_col is None:
                print(
                    f"Error: Neither 'id' nor 'pid' column found in {file_path}",
                    file=sys.stderr,
                )
                sys.exit(1)

            for row in reader:
                val = row.get(id_col)
                if val:
                    ids.add(val.strip())
    except FileNotFoundError:
        print(f"Error: File not found {file_path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)
        sys.exit(1)
    return ids


def main() -> None:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Find unique IDs that exist in one CSV but not the other."
    )
    parser.add_argument("file1", help="Path to the first CSV file")
    parser.add_argument("file2", help="Path to the second CSV file")

    args = parser.parse_args()

    ids1 = get_ids_from_csv(args.file1)
    ids2 = get_ids_from_csv(args.file2)

    unique_to_file1 = ids1 - ids2
    unique_to_file2 = ids2 - ids1

    if unique_to_file1:
        print(f"--- IDs unique to {args.file1} ---")
        for uid in sorted(unique_to_file1):
            print(uid)

    if unique_to_file2:
        print()
        print(f"--- IDs unique to {args.file2} ---")
        for uid in sorted(unique_to_file2):
            print(uid)

    if not unique_to_file1 and not unique_to_file2:
        print("No unique IDs found. Both files contain the exact same IDs.")


if __name__ == "__main__":
    main()
