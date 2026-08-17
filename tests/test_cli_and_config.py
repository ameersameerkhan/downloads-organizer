import json

import pytest

from downloads_organizer.cli import build_parser
from downloads_organizer.config import DEFAULT_CATEGORY, load_categories


def test_cli_accepts_custom_source_and_output(tmp_path):
    source = tmp_path / "incoming"
    output = tmp_path / "sorted"
    parser = build_parser()

    args = parser.parse_args(["--source", str(source), "--output", str(output), "--dry-run"])

    assert args.source == source
    assert args.output == output
    assert args.dry_run is True


def test_cli_exposes_explicit_duplicate_deletion_flag():
    parser = build_parser()

    args = parser.parse_args(["--delete-duplicates"])

    assert args.delete_duplicates is True


def test_config_file_can_override_categories_and_fallback(tmp_path):
    config_path = tmp_path / "categories.json"
    config_path.write_text(json.dumps({
        "categories": {"Design": [".fig", ".sketch"]},
        "fallback": "Other",
    }))

    categories, fallback = load_categories(config_path)

    assert categories == {"Design": [".fig", ".sketch"]}
    assert fallback == "Other"


def test_invalid_config_rejects_non_list_extensions(tmp_path):
    config_path = tmp_path / "categories.json"
    config_path.write_text(json.dumps({"categories": {"Design": ".fig"}}))

    with pytest.raises(ValueError, match="list"):
        load_categories(config_path)


def test_default_fallback_is_miscellaneous():
    assert DEFAULT_CATEGORY == "Miscellaneous"
