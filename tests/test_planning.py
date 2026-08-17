from downloads_organizer.cli import main as cli_main
from downloads_organizer.organizer import build_plan


def test_build_plan_describes_moves_without_mutating_files(tmp_path):
    source = tmp_path / "Downloads"
    output = source / "Organized"
    source.mkdir()
    original = source / "notes.txt"
    original.write_text("hello")

    plan = build_plan(source_path=source, output_path=output)

    assert plan["operations"] == [
        {
            "action": "move",
            "source": original,
            "destination": output / "Documents" / "notes.txt",
            "category": "Documents",
            "size_bytes": 5,
            "modified": plan["operations"][0]["modified"],
        }
    ]
    assert original.exists()
    assert not output.exists()


def test_dry_run_prints_planned_moves_and_duplicates(tmp_path, capsys):
    source = tmp_path / "Downloads"
    output = source / "Organized"
    source.mkdir()
    (source / "notes.txt").write_text("move me")
    (source / "same.pdf").write_text("same")
    duplicate_destination = output / "Documents"
    duplicate_destination.mkdir(parents=True)
    (duplicate_destination / "same.pdf").write_text("same")

    result = cli_main(["--source", str(source), "--dry-run"])

    captured = capsys.readouterr().out
    assert result == 0
    assert "Would move" in captured
    assert "notes.txt" in captured
    assert "Documents" in captured
    assert "Duplicate retained" in captured
    assert "same.pdf" in captured
    assert (source / "notes.txt").exists()
    assert (source / "same.pdf").exists()
