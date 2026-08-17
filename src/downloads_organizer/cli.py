"""Command-line interface for Downloads Organizer."""

import argparse
from pathlib import Path

from . import __version__
from .config import load_categories
from .organizer import organize_files


def build_parser():
    parser = argparse.ArgumentParser(
        prog="downloads-organizer",
        description="Organize local files by type and generate local reports.",
    )
    parser.add_argument("--source", type=Path, default=Path.home() / "Downloads")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--config", type=Path, help="Optional JSON category configuration")
    parser.add_argument("--dry-run", action="store_true", help="Preview without changing files")
    parser.add_argument("--organize-by-date", action="store_true", help="Create YYYY-MM subfolders")
    parser.add_argument(
        "--delete-duplicates",
        action="store_true",
        help="Delete hash-confirmed duplicates; otherwise duplicates are only reported",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def _print_dry_run_operations(operations):
    if not operations:
        print("\nNo files need organising.")
        return

    print("\nPlanned operations:")
    for operation in operations:
        source_name = operation["source"].name
        destination = operation["destination"]
        if operation["action"] == "move":
            print(f"Would move: {source_name} -> {destination}")
        elif operation["action"] == "keep_duplicate":
            print(f"Duplicate retained: {source_name} -> {destination}")
        elif operation["action"] == "delete_duplicate":
            print(f"Would delete duplicate: {source_name} (matches {destination})")


def main(argv=None):
    args = build_parser().parse_args(argv)
    categories, fallback = load_categories(args.config)
    output = args.output if args.output is not None else args.source / "Organized"

    print("=== Downloads Organizer ===")
    print(f"Source: {args.source}")
    print(f"Destination: {output}")
    if args.dry_run:
        print("Mode: dry run (no files will be changed)")

    report = organize_files(
        source_path=args.source,
        output_path=output,
        categories=categories,
        fallback=fallback,
        organize_by_date=args.organize_by_date,
        dry_run=args.dry_run,
        delete_duplicates=args.delete_duplicates,
    )

    if args.dry_run:
        _print_dry_run_operations(report["operations"])

    metadata = report["metadata"]
    print("\n=== Organization Summary ===")
    print(f"Total files processed: {metadata['total_files_processed']}")
    print(f"Duplicates found: {metadata['duplicates_found']}")
    print(f"Duplicates deleted: {metadata['duplicates_deleted']}")
    print(f"Total size processed: {metadata['total_size_mb']} MB")
    return 0
