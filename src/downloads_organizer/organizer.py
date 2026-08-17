"""Safe filesystem planning and execution for Downloads Organizer.

Invariants:
* validate paths before mutation
* planning never mutates the filesystem
* dry-run never creates, moves, or deletes anything
* confirmed duplicates are retained unless removal was explicitly requested
"""

import hashlib
import json
import shutil
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from .config import DEFAULT_CATEGORIES, DEFAULT_CATEGORY
from .reporting import generate_html_report


def get_file_category(extension, categories=None, fallback=DEFAULT_CATEGORY):
    categories = categories or DEFAULT_CATEGORIES
    extension = extension.lower()
    for category, extensions in categories.items():
        if extension in extensions:
            return category
    return fallback


def get_file_hash(file_path):
    digest = hashlib.sha256()
    with open(file_path, "rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resolve_paths(source_path=None, output_path=None):
    source = Path(source_path) if source_path is not None else Path.home() / "Downloads"
    output = Path(output_path) if output_path is not None else source / "Organized"

    if not source.exists():
        raise FileNotFoundError(f"Source folder does not exist: {source}")
    if not source.is_dir():
        raise ValueError(f"Source path is not a directory: {source}")
    if source.resolve() == output.resolve():
        raise ValueError("Source and output folders must be different")

    return source, output


def build_plan(*, source_path=None, output_path=None, categories=None,
               fallback=DEFAULT_CATEGORY, organize_by_date=False,
               delete_duplicates=False):
    """Inspect the source and return proposed operations without changing files."""
    source, output = _resolve_paths(source_path, output_path)
    categories = categories or DEFAULT_CATEGORIES
    operations = []

    for item in source.iterdir():
        if item.is_dir():
            continue

        category = get_file_category(item.suffix, categories, fallback)
        modified_date = datetime.fromtimestamp(item.stat().st_mtime)
        destination_folder = output / category
        if organize_by_date:
            destination_folder = destination_folder / modified_date.strftime("%Y-%m")

        destination_path = destination_folder / item.name
        if destination_path.exists():
            if get_file_hash(item) == get_file_hash(destination_path):
                operations.append({
                    "action": "delete_duplicate" if delete_duplicates else "keep_duplicate",
                    "source": item,
                    "destination": destination_path,
                    "category": category,
                    "size_bytes": item.stat().st_size,
                    "modified": modified_date.isoformat(),
                })
                continue

            counter = 1
            while destination_path.exists():
                destination_path = destination_folder / f"{item.stem}_{counter}{item.suffix}"
                counter += 1

        operations.append({
            "action": "move",
            "source": item,
            "destination": destination_path,
            "category": category,
            "size_bytes": item.stat().st_size,
            "modified": modified_date.isoformat(),
        })

    return {"source": source, "output": output, "operations": operations}


def execute_plan(plan):
    """Apply a previously built plan. Keep this function intentionally small."""
    for operation in plan["operations"]:
        if operation["action"] == "move":
            operation["destination"].parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(operation["source"]), str(operation["destination"]))
        elif operation["action"] == "delete_duplicate":
            # This action can appear only when deletion was explicitly enabled
            # while building the plan. Dry-run never calls execute_plan.
            operation["source"].unlink()


def _build_report(plan, start_time, *, executed):
    stats = defaultdict(int)
    all_files = []
    duplicates = 0
    duplicates_deleted = 0
    total_size = 0

    for operation in plan["operations"]:
        if operation["action"] in {"keep_duplicate", "delete_duplicate"}:
            duplicates += 1
            if executed and operation["action"] == "delete_duplicate":
                duplicates_deleted += 1
            continue

        size_bytes = operation["size_bytes"]
        all_files.append({
            "name": operation["source"].name,
            "category": operation["category"],
            "size_mb": round(size_bytes / (1024 * 1024), 2),
            "modified": operation["modified"],
            "new_path": str(operation["destination"].relative_to(plan["output"])),
        })
        stats[operation["category"]] += 1
        total_size += size_bytes

    return {
        "metadata": {
            "timestamp": start_time.isoformat(),
            "duration_seconds": round((datetime.now() - start_time).total_seconds(), 2),
            "source_folder": str(plan["source"]),
            "target_folder": str(plan["output"]),
            "total_files_processed": len(all_files),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "duplicates_found": duplicates,
            "duplicates_deleted": duplicates_deleted,
        },
        "category_stats": dict(stats),
        "all_files": all_files,
        "largest_files": sorted(all_files, key=lambda file: file["size_mb"], reverse=True),
        "oldest_files": sorted(all_files, key=lambda file: file["modified"]),
    }


def organize_files(*, source_path=None, output_path=None, categories=None,
                   fallback=DEFAULT_CATEGORY, organize_by_date=False,
                   dry_run=False, delete_duplicates=False):
    start_time = datetime.now()
    plan = build_plan(
        source_path=source_path,
        output_path=output_path,
        categories=categories,
        fallback=fallback,
        organize_by_date=organize_by_date,
        delete_duplicates=delete_duplicates,
    )

    if not dry_run:
        execute_plan(plan)

    report_data = _build_report(plan, start_time, executed=not dry_run)

    if not dry_run:
        plan["output"].mkdir(parents=True, exist_ok=True)
        timestamp = start_time.strftime("%Y%m%d_%H%M%S")
        (plan["output"] / f"report_{timestamp}.json").write_text(
            json.dumps(report_data, indent=2)
        )
        generate_html_report(report_data, plan["output"] / f"report_{timestamp}.html")

    # Operations are returned for CLI previews and tests, but are deliberately
    # excluded from persisted reports because they contain Path objects.
    return {**report_data, "operations": plan["operations"]}
