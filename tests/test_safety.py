from downloads_organizer.organizer import organize_files
from downloads_organizer.reporting import generate_html_report


def test_html_report_handles_file_history(tmp_path):
    output = tmp_path / "report.html"
    report_data = {
        "category_stats": {"Documents": 1},
        "all_files": [{
            "name": "notes.txt",
            "category": "Documents",
            "size_mb": 0.01,
            "modified": "2026-08-17T12:00:00",
            "new_path": "Documents/notes.txt",
        }],
        "largest_files": [],
        "oldest_files": [],
    }

    generate_html_report(report_data, output)

    assert output.exists()
    assert "Organization Report" in output.read_text()


def test_duplicate_is_not_deleted_by_default(tmp_path):
    source = tmp_path / "Downloads"
    output = source / "Organized"
    source.mkdir()
    (source / "same.txt").write_text("same content")
    destination = output / "Documents"
    destination.mkdir(parents=True)
    (destination / "same.txt").write_text("same content")

    organize_files(source_path=source, output_path=output)

    assert (source / "same.txt").exists()


def test_duplicate_can_be_deleted_explicitly(tmp_path):
    source = tmp_path / "Downloads"
    output = source / "Organized"
    source.mkdir()
    (source / "same.txt").write_text("same content")
    destination = output / "Documents"
    destination.mkdir(parents=True)
    (destination / "same.txt").write_text("same content")

    organize_files(source_path=source, output_path=output, delete_duplicates=True)

    assert not (source / "same.txt").exists()


def test_dry_run_has_no_filesystem_side_effects(tmp_path):
    source = tmp_path / "Downloads"
    output = source / "Organized"
    source.mkdir()
    original = source / "notes.txt"
    original.write_text("hello")

    result = organize_files(source_path=source, output_path=output, dry_run=True)

    assert original.exists()
    assert not output.exists()
    assert result["metadata"]["total_files_processed"] == 1


def test_dry_run_never_counts_planned_duplicate_deletion_as_deleted(tmp_path):
    source = tmp_path / "Downloads"
    output = source / "Organized"
    source.mkdir()
    duplicate = source / "same.txt"
    duplicate.write_text("same content")
    destination = output / "Documents"
    destination.mkdir(parents=True)
    (destination / "same.txt").write_text("same content")

    result = organize_files(
        source_path=source,
        output_path=output,
        dry_run=True,
        delete_duplicates=True,
    )

    assert duplicate.exists()
    assert result["metadata"]["duplicates_found"] == 1
    assert result["metadata"]["duplicates_deleted"] == 0
    assert result["operations"][0]["action"] == "delete_duplicate"


def test_missing_source_is_rejected_before_changes(tmp_path):
    missing = tmp_path / "missing"
    output = tmp_path / "out"

    try:
        organize_files(source_path=missing, output_path=output)
    except (FileNotFoundError, ValueError):
        pass
    else:
        raise AssertionError("missing source should be rejected")

    assert not output.exists()


def test_source_and_output_cannot_be_same_directory(tmp_path):
    source = tmp_path / "Downloads"
    source.mkdir()

    try:
        organize_files(source_path=source, output_path=source)
    except ValueError:
        pass
    else:
        raise AssertionError("source and output must not be the same directory")
