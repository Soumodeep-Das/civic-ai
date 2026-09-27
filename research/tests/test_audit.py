import json

import pytest

from research.civicai_research.audit import audit
from research.civicai_research.opencity import ingest


def minimal_csv():
    import csv
    import io

    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(["title", "description", "category_title", "sub_category_title", "created_at"])
    writer.writerow(["Fixture", "Synthetic civic complaint", "Road", "Pothole", "2020-01-01"])
    return stream.getvalue().encode()


def source_csv():
    import csv
    import io

    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(["title", "description", "category_title", "sub_category_title", "created_at",
                     "location", "address", "latitude", "longitude", "ward_title"])
    writer.writerow(["Pothole", "Large pothole near school", "Mobility Roads/Footpaths",
                     "Fixing/Reparing Potholes", "2020-01-01", "Bengaluru", "Road", "12.9", "77.6", "Ward 1"])
    writer.writerow(["Pothole", "Large pothole near school", "Mobility Roads/Footpaths",
                     "Fixing/Reparing Potholes", "2020-01-02", "Bengaluru", "Road", "12.9", "77.6", "Ward 1"])
    writer.writerow(["Other", "Call 9876543210", "Other", "Others", "2021-02-01",
                     "", "", "", "", "NULL"])
    return stream.getvalue().encode()


def test_audit_is_deterministic_and_keeps_mapping_provisional(tmp_path):
    snapshot = tmp_path / "snapshot"
    ingest(source_csv(), snapshot, b"{}")
    first = audit(snapshot, tmp_path / "audit-a")
    second = audit(snapshot, tmp_path / "audit-b")
    assert first == second
    assert first["country"] == "IN"
    assert first["training_approved"] is False
    assert first["mapping_status_counts"] == {"accepted": 2, "needs_review": 1}
    assert first["duplicates"]["normalized_description_excess_records"] == 1
    assert first["privacy_pattern_counts"]["possible_indian_phone"] == 1
    assert first["privacy_pattern_counts"]["possible_email"] == 0
    assert first["date_year_counts"] == {"2020": 2, "2021": 1}
    assert first["text_quality"].get("unparsed_date", 0) == 0
    review = json.loads((tmp_path / "audit-a/mapping-review.json").read_text(encoding="utf-8"))
    assert all("description" not in item for item in review)
    assert {item["reviewer_status"] for item in review} == {"unreviewed"}
    duplicates = json.loads((tmp_path / "audit-a/duplicate-review.json").read_text(encoding="utf-8"))
    assert duplicates[0]["count"] == 2
    assert all("description" not in record for group in duplicates for record in group["records"])


def test_audit_refuses_incomplete_snapshot(tmp_path):
    snapshot = tmp_path / "snapshot"
    ingest(minimal_csv(), snapshot, b"{}")
    (snapshot / "COMPLETE").unlink()
    (snapshot / "INCOMPLETE").write_text("interrupted\n", encoding="utf-8")
    with pytest.raises(ValueError, match="not marked complete"):
        audit(snapshot, tmp_path / "audit")


def test_audit_does_not_overwrite(tmp_path):
    snapshot = tmp_path / "snapshot"
    ingest(source_csv(), snapshot, b"{}")
    audit(snapshot, tmp_path / "audit")
    with pytest.raises(ValueError, match="output exists"):
        audit(snapshot, tmp_path / "audit")


def test_invalid_mapping_state_is_refused(tmp_path):
    snapshot = tmp_path / "snapshot"
    ingest(minimal_csv(), snapshot, b"{}")
    mapping = tmp_path / "mapping.json"
    mapping.write_text(json.dumps({"status": "approved", "source_name": "opencity-icmyc-india",
        "taxonomy_version": "civicai-category-v1", "default_status": "needs_review", "rules": []}),
        encoding="utf-8")
    with pytest.raises(ValueError, match="proposal"):
        audit(snapshot, tmp_path / "audit", mapping)
