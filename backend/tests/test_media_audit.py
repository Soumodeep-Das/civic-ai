from pathlib import Path

from civicai.media_audit import audit_inventory


def test_media_audit_reports_missing_orphan_and_invalid_entries(tmp_path: Path):
    (tmp_path / "kept.png").write_bytes(b"kept")
    (tmp_path / "orphan.jpg").write_bytes(b"orphan")

    report = audit_inventory(
        tmp_path,
        [
            "/api/v1/complaint-images/kept.png",
            "/api/v1/complaint-images/missing.png",
            "https://example.invalid/public-image.png",
        ],
    )

    assert report.database_references == 3
    assert report.stored_files == 2
    assert report.missing_files == ("missing.png",)
    assert report.orphan_files == ("orphan.jpg",)
    assert report.invalid_references == ("https://example.invalid/public-image.png",)
    assert report.consistent is False


def test_media_audit_accepts_empty_missing_directory(tmp_path: Path):
    report = audit_inventory(tmp_path / "not-created", [])
    assert report.consistent is True
    assert report.stored_files == 0
