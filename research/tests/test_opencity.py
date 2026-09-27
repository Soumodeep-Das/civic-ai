import csv
import io
import json

import httpx
import pytest

from research.civicai_research.opencity import acquire, ingest, verify_existing, RESOURCE_ID
from research.civicai_research.manifest import validate_manifest


def csv_data(descriptions=("Synthetic civic complaint",), encoding="utf-8"):
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(["title", "description", "category_title", "sub_category_title", "created_at"])
    for description in descriptions:
        writer.writerow(["Fixture", description, "Road", "Pothole", "2020-01-01"])
    return stream.getvalue().encode(encoding)


def test_import_retains_source_labels_separately_and_leaves_pending(tmp_path):
    report = ingest(csv_data(), tmp_path / "out", b"{}")
    row = json.loads((tmp_path / "out/manifest.jsonl").read_text())
    assert report["country"] == "IN"
    assert not report["training_approved"]
    assert row["category_label"] is None
    assert row["annotation_status"] == "pending"
    assert row["split"] == "unassigned"
    assert row["image_available"] is False
    assert validate_manifest(tmp_path / "out/manifest.jsonl", data_root=tmp_path / "out").valid
    assert (tmp_path / "out/COMPLETE").is_file()
    assert not (tmp_path / "out/INCOMPLETE").exists()


def test_windows_quotes_decoded_without_loss(tmp_path):
    report = ingest(csv_data(("Citizen’s fixture",), "cp1252"), tmp_path / "out", b"{}")
    assert report["encoding"] == "cp1252"
    assert next((tmp_path / "out/texts").iterdir()).read_text(encoding="utf-8") == "Citizen’s fixture"


def test_missing_description_counted_not_fabricated(tmp_path):
    report = ingest(csv_data(("", "Fixture")), tmp_path / "out", b"{}")
    assert report["omissions"] == {"empty_description": 1}
    assert report["records_ingested"] == 1


def test_schema_change_refused(tmp_path):
    with pytest.raises(ValueError, match="schema changed"):
        ingest(b"wrong,column\na,b", tmp_path / "out", b"{}")
    assert not (tmp_path / "out").exists()


def test_no_overwrite(tmp_path):
    ingest(csv_data(), tmp_path / "out", b"{}")
    with pytest.raises(ValueError, match="Output exists"):
        ingest(csv_data(), tmp_path / "out", b"{}")


def test_interrupted_snapshot_can_be_verified_without_download(tmp_path):
    output = tmp_path / "out"
    ingest(csv_data(), output, b"{}")
    (output / "COMPLETE").unlink()
    (output / "INCOMPLETE").write_text("interrupted\n", encoding="utf-8")
    report = verify_existing(output)
    assert report == {"records": 1, "warnings": 0, "valid": True}
    assert (output / "COMPLETE").is_file()
    assert not (output / "INCOMPLETE").exists()


def test_interrupted_snapshot_with_modified_text_is_not_completed(tmp_path):
    output = tmp_path / "out"
    ingest(csv_data(), output, b"{}")
    (output / "COMPLETE").unlink()
    (output / "INCOMPLETE").write_text("interrupted\n", encoding="utf-8")
    next((output / "texts").iterdir()).write_text("tampered", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid"):
        verify_existing(output)
    assert (output / "INCOMPLETE").is_file()
    assert not (output / "COMPLETE").exists()


@pytest.mark.parametrize("license_id,host", [("unknown", "https://data.opencity.in/file"),
                                          ("cc-by-sa", "https://example.invalid/file")])
def test_license_and_host_changes_refused(tmp_path, license_id, host):
    def handler(request):
        return httpx.Response(200, json={"result": {"license_id": license_id,
            "resources": [{"id": RESOURCE_ID, "url": host}]}})
    with httpx.Client(transport=httpx.MockTransport(handler)) as client, pytest.raises(ValueError):
        acquire(tmp_path / "out", client)
    assert not (tmp_path / "out").exists()
