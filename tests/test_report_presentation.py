from downloads_organizer.reporting import generate_html_report


def sample_report():
    return {
        "metadata": {
            "timestamp": "2026-08-17T12:00:00",
            "duration_seconds": 0.42,
            "source_folder": "/Users/example/Downloads",
            "target_folder": "/Users/example/Downloads/Organized",
            "total_files_processed": 3,
            "total_size_mb": 18.4,
            "duplicates_found": 1,
            "duplicates_deleted": 0,
        },
        "category_stats": {"Documents": 2, "Images": 1},
        "all_files": [
            {"name": "annual-report.pdf", "category": "Documents", "size_mb": 12.1, "modified": "2026-06-10T12:00:00", "new_path": "Documents/annual-report.pdf"},
            {"name": "notes.md", "category": "Documents", "size_mb": 0.1, "modified": "2026-07-05T12:00:00", "new_path": "Documents/notes.md"},
            {"name": "portrait.jpg", "category": "Images", "size_mb": 6.2, "modified": "2026-08-01T12:00:00", "new_path": "Images/portrait.jpg"},
        ],
        "largest_files": [],
        "oldest_files": [],
    }


def test_report_surfaces_run_summary_and_privacy_note(tmp_path):
    output = tmp_path / "report.html"
    generate_html_report(sample_report(), output)
    html = output.read_text()

    assert "3" in html
    assert "Files organised" in html
    assert "Duplicates detected" in html
    assert "Generated locally" in html
    assert "Files by modification month" in html
    assert "download history" not in html.lower()


def test_report_escapes_file_names(tmp_path):
    report = sample_report()
    report["all_files"][0]["name"] = "<script>alert(1)</script>.pdf"
    report["largest_files"] = report["all_files"]
    output = tmp_path / "report.html"

    generate_html_report(report, output)

    html = output.read_text()
    assert "<script>alert(1)</script>.pdf" not in html
    assert "&lt;script&gt;" in html


def test_report_has_no_runtime_network_dependency(tmp_path):
    output = tmp_path / "report.html"
    generate_html_report(sample_report(), output)
    html = output.read_text()

    assert "cdn.jsdelivr" not in html
    assert "<script src=" not in html
