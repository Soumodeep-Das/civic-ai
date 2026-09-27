import csv
import hashlib
import json
from pathlib import Path

import pytest

from research.civicai_research.audit import audit
from research.civicai_research.curate import assess_readiness, redact_text, write_readiness_report
from research.civicai_research.opencity import ingest
from research.civicai_research.review import (apply_adjudication, create_package, merge_submissions,
                                               validate_adjudication, validate_submission)


def source_csv():
    import io

    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(["title", "description", "category_title", "sub_category_title", "created_at",
                     "location", "address", "latitude", "longitude", "ward_title"])
    writer.writerow(["Formula", "=HYPERLINK(\"https://example.invalid\") call 9876543210",
                     "Mobility", "Fixing/Reparing Potholes", "2020-01-01", "Bengaluru", "", "12.9", "77.6", "Ward"])
    writer.writerow(["Duplicate", "Large pothole near school", "Mobility", "Fixing/Reparing Potholes",
                     "2020-01-02", "Bengaluru", "", "12.9", "77.6", "Ward"])
    writer.writerow(["Duplicate", "Large pothole near school", "Mobility", "Fixing/Reparing Potholes",
                     "2020-01-03", "Bengaluru", "", "12.9", "77.6", "Ward"])
    return stream.getvalue().encode()


def package(tmp_path):
    snapshot = tmp_path / "snapshot"
    raw = source_csv(); ingest(raw, snapshot, b"{}")
    audit(snapshot, tmp_path / "audit")
    output = tmp_path / "package"
    result = create_package(snapshot, tmp_path / "audit", output, examples_per_group=2)
    return snapshot, output, result


def edit_form(template: Path, output: Path, *, reviewer: str, decision: str, rationale: str,
              row_index: int = 0, **outcomes):
    with template.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream); fields = reader.fieldnames; rows = list(reader)
    row = rows[row_index]; row.update(reviewer_id=reviewer, reviewed_at="2026-09-27T12:00:00+05:30",
                                      decision=decision, reviewer_rationale=rationale)
    row.update(outcomes)
    with output.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, quoting=csv.QUOTE_ALL, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)


def test_package_is_deterministic_safe_and_does_not_change_raw_snapshot(tmp_path):
    snapshot, output, report = package(tmp_path)
    before = hashlib.sha256((snapshot / "source.csv").read_bytes()).hexdigest()
    assert report["human_decisions_present"] is False
    assert report["training_approved"] is False
    assert report["counts"]["taxonomy"] == 8
    assert report["counts"]["mapping"] == 1
    assert report["counts"]["privacy"] == 1
    assert report["counts"]["duplicate"] >= 1
    with (output / "forms/mapping_review.csv").open("r", encoding="utf-8-sig", newline="") as stream:
        mapping_row = next(csv.DictReader(stream))
    assert mapping_row["source_category"] == "Mobility"
    assert mapping_row["source_subcategory"] == "Fixing/Reparing Potholes"
    assert mapping_row["mapping_version"] == "icmyc-to-civicai-proposal-v1"
    with (output / "forms/record_review.csv").open("r", encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert any(row["preview_redacted"].startswith("'") and "[PHONE]" in row["preview_redacted"] for row in rows)
    assert hashlib.sha256((snapshot / "source.csv").read_bytes()).hexdigest() == before
    with pytest.raises(ValueError, match="exists"):
        create_package(snapshot, tmp_path / "audit", output)


def test_submission_validation_rejects_invalid_state_and_context_tampering(tmp_path):
    _, output, _ = package(tmp_path)
    template = output / "forms/mapping_review.csv"
    valid = tmp_path / "valid.csv"
    edit_form(template, valid, reviewer="reviewer_1", decision="approve_mapping", rationale="Examples consistent",
              approved_category="road_damage")
    result = validate_submission(output, valid)
    assert result["completed"] == 1

    invalid = tmp_path / "invalid.csv"
    edit_form(template, invalid, reviewer="reviewer_1", decision="invented", rationale="No")
    with pytest.raises(ValueError, match="invalid decision"):
        validate_submission(output, invalid)

    tampered = tmp_path / "tampered.csv"
    edit_form(template, tampered, reviewer="reviewer_1", decision="ambiguous", rationale="Mixed",
              source_subcategory="Changed source label")
    with pytest.raises(ValueError, match="immutable"):
        validate_submission(output, tampered)


def test_merge_preserves_disagreement_and_rejects_duplicate_reviewer(tmp_path):
    _, package_dir, _ = package(tmp_path)
    template = package_dir / "forms/mapping_review.csv"
    first, second = tmp_path / "one.csv", tmp_path / "two.csv"
    edit_form(template, first, reviewer="r_one", decision="reject_mapping", rationale="Insufficient consistency")
    edit_form(template, second, reviewer="r_two", decision="ambiguous", rationale="Mixed meanings")
    report = merge_submissions(package_dir, [first, second], tmp_path / "merged")
    assert report["conflicting_items"] == 1
    assert report["training_approved"] is False
    decisions = json.loads((tmp_path / "merged/decisions.json").read_text(encoding="utf-8"))
    assert len(decisions["conflicts"]) == 1
    assert {row["reviewer_id"] for row in decisions["conflicts"][0]["submissions"]} == {"r_one", "r_two"}

    with pytest.raises(ValueError, match="Duplicate reviewer"):
        merge_submissions(package_dir, [first, first], tmp_path / "duplicate-merge")


def test_decision_specific_evidence_is_required(tmp_path):
    _, package_dir, _ = package(tmp_path)
    privacy = tmp_path / "privacy.csv"
    edit_form(package_dir / "forms/privacy_review.csv", privacy, reviewer="reviewer_1", decision="redact",
              rationale="Possible resident name", redaction_types="name")
    with pytest.raises(ValueError, match="explicit spans"):
        validate_submission(package_dir, privacy)

    record = tmp_path / "record.csv"
    edit_form(package_dir / "forms/record_review.csv", record, reviewer="reviewer_1", decision="exclude",
              rationale="Not usable")
    with pytest.raises(ValueError, match="exclusion requires"):
        validate_submission(package_dir, record)

    duplicate = tmp_path / "duplicate.csv"
    edit_form(package_dir / "forms/duplicate_review.csv", duplicate, reviewer="reviewer_1",
              decision="keep_together", rationale="Same incident")
    with pytest.raises(ValueError, match="approved_group_id"):
        validate_submission(package_dir, duplicate)


def test_adjudication_rejects_tampered_conflict_context(tmp_path):
    _, package_dir, _ = package(tmp_path)
    template = package_dir / "forms/mapping_review.csv"
    first, second = tmp_path / "one.csv", tmp_path / "two.csv"
    edit_form(template, first, reviewer="r_one", decision="reject_mapping", rationale="Not consistent")
    edit_form(template, second, reviewer="r_two", decision="ambiguous", rationale="Mixed")
    merge_submissions(package_dir, [first, second], tmp_path / "merged")
    adjudication = tmp_path / "merged/adjudication_review.csv"
    with adjudication.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream); fields = reader.fieldnames; rows = list(reader)
    rows[0].update(conflicting_submissions_json="[]", adjudicator_id="adjudicator_1",
                   adjudicated_at="2026-09-27T12:00:00+05:30", final_decision="ambiguous",
                   final_outcomes_json="{}", adjudication_rationale="Evidence remains mixed")
    with adjudication.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, quoting=csv.QUOTE_ALL, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)
    with pytest.raises(ValueError, match="modified"):
        validate_adjudication(tmp_path / "merged/decisions.json", adjudication)


def test_valid_adjudication_preserves_reviews_and_resolves_conflict(tmp_path):
    _, package_dir, _ = package(tmp_path)
    template = package_dir / "forms/mapping_review.csv"
    first, second = tmp_path / "one.csv", tmp_path / "two.csv"
    edit_form(template, first, reviewer="r_one", decision="reject_mapping", rationale="Not consistent")
    edit_form(template, second, reviewer="r_two", decision="ambiguous", rationale="Mixed")
    merge_submissions(package_dir, [first, second], tmp_path / "merged")
    adjudication = tmp_path / "merged/adjudication_review.csv"
    with adjudication.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream); fields = reader.fieldnames; rows = list(reader)
    rows[0].update(adjudicator_id="adjudicator_1", adjudicated_at="2026-09-27T13:00:00+05:30",
                   final_decision="ambiguous", final_outcomes_json='{"approved_category": ""}',
                   adjudication_rationale="Samples remain semantically mixed")
    with adjudication.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, quoting=csv.QUOTE_ALL, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)
    report = apply_adjudication(tmp_path / "merged/decisions.json", adjudication,
                                tmp_path / "merged/decisions-adjudicated.json")
    assert report == {"adjudicated": 1, "remaining_conflicts": 0, "training_approved": False}
    merged = json.loads((tmp_path / "merged/decisions-adjudicated.json").read_text(encoding="utf-8"))
    assert merged["resolved"][0]["resolution"] == "adjudicated"
    assert set(merged["resolved"][0]["reviewers"]) == {"r_one", "r_two"}


def test_redaction_is_deterministic_non_destructive_and_validates_spans():
    raw = "Call 9876543210 or a@example.com; resident Alice"
    start = raw.index("Alice"); span = f"{start}:{start + len('Alice')}:name"
    first = redact_text(raw, {"phone", "email", "name"}, span)
    second = redact_text(raw, {"phone", "email", "name"}, span)
    assert first == second
    assert raw == "Call 9876543210 or a@example.com; resident Alice"
    assert "[PHONE]" in first[0] and "[EMAIL]" in first[0] and "[NAME]" in first[0]
    with pytest.raises(ValueError, match="overlap"):
        redact_text(raw, {"name", "address"}, "0:5:name|4:8:address")
    with pytest.raises(ValueError, match="requires matching"):
        redact_text(raw, {"name"})


def test_unresolved_human_gates_cannot_approve_training(tmp_path):
    _, package_dir, _ = package(tmp_path)
    template = package_dir / "forms/mapping_review.csv"
    submission = tmp_path / "one.csv"
    edit_form(template, submission, reviewer="reviewer_1", decision="approve_mapping",
              rationale="Examples consistent", approved_category="road_damage")
    merge_submissions(package_dir, [submission], tmp_path / "merged")
    report = assess_readiness(package_dir / "package.json", tmp_path / "merged/decisions.json")
    assert report["training_approved"] is False
    assert report["unresolved_by_review_type"]["taxonomy"] == 8
    written = write_readiness_report(package_dir / "package.json", tmp_path / "merged/decisions.json",
                                     tmp_path / "readiness")
    assert written["training_approved"] is False
    assert (tmp_path / "readiness/STAGE_B_REQUIRED").is_file()
    with pytest.raises(ValueError, match="exists"):
        write_readiness_report(package_dir / "package.json", tmp_path / "merged/decisions.json",
                               tmp_path / "readiness")
