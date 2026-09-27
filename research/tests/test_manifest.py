import hashlib
import json
from copy import deepcopy
from pathlib import Path

from research.civicai_research.manifest import validate_manifest


ROOT = Path(__file__).parents[2]
TAXONOMY = ROOT / "research" / "taxonomy" / "category_v1.json"
SAMPLE = ROOT / "research" / "examples" / "manifest.synthetic.jsonl"


def example_record(**overrides):
    record = {
        "record_id": "record-1",
        "source_name": "test-source",
        "source_record_id": "source-1",
        "source_terms_ref": "https://example.invalid/terms-v1",
        "consent_or_basis": None,
        "dataset_version": "test-v1",
        "taxonomy_version": "civicai-category-v1",
        "annotation_status": "annotated",
        "category_label": "road_damage",
        "annotator_id": "annotator-a",
        "annotation_notes": None,
        "exclusion_reason": None,
        "group_id": "event-1",
        "split": "train",
        "text_available": True,
        "text_ref": "texts/record-1.txt",
        "text_sha256": "1" * 64,
        "image_available": False,
        "image_ref": None,
        "image_sha256": None,
    }
    record.update(overrides)
    return record


def write_manifest(tmp_path, records):
    path = tmp_path / "manifest.jsonl"
    path.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")
    return path


def test_synthetic_contract_manifest_covers_taxonomy_and_is_valid():
    report = validate_manifest(SAMPLE, TAXONOMY)
    assert report.valid, report.errors
    assert report.records == 8
    assert set(report.categories) == {
        "road_damage", "garbage_waste", "streetlight", "waterlogging",
        "broken_footpath", "drainage_sewerage", "water_leakage", "other",
    }
    assert report.splits == {"unassigned": 8}


def test_manifest_rejects_unknown_category_and_inconsistent_annotation(tmp_path):
    record = example_record(category_label="noise", annotator_id=None)
    report = validate_manifest(write_manifest(tmp_path, [record]), TAXONOMY)
    assert not report.valid
    assert any("category_label" in error for error in report.errors)
    assert any("require annotator_id" in error for error in report.errors)


def test_manifest_rejects_missing_and_unknown_fields(tmp_path):
    record = example_record(unexpected="value")
    del record["dataset_version"]
    report = validate_manifest(write_manifest(tmp_path, [record]), TAXONOMY)
    assert any("missing fields: dataset_version" in error for error in report.errors)
    assert any("unknown fields: unexpected" in error for error in report.errors)


def test_manifest_rejects_duplicate_record_and_source_identity(tmp_path):
    first = example_record()
    second = deepcopy(first)
    second["group_id"] = "event-2"
    second["text_sha256"] = "2" * 64
    report = validate_manifest(write_manifest(tmp_path, [first, second]), TAXONOMY)
    assert any("duplicate record_id" in error for error in report.errors)
    assert any("duplicate source identity" in error for error in report.errors)


def test_manifest_rejects_group_and_exact_content_split_leakage(tmp_path):
    first = example_record(split="train")
    second = example_record(
        record_id="record-2", source_record_id="source-2", split="test", text_ref="texts/record-2.txt"
    )
    report = validate_manifest(write_manifest(tmp_path, [first, second]), TAXONOMY)
    assert any("checksum crosses train/test splits" in error for error in report.errors)
    assert any("group_id 'event-1' crosses assigned splits" in error for error in report.errors)


def test_manifest_rejects_path_traversal_and_modality_mismatch(tmp_path):
    record = example_record(text_ref="../private.txt", image_available=False, image_ref="images/hidden.png")
    report = validate_manifest(write_manifest(tmp_path, [record]), TAXONOMY)
    assert any("without traversal" in error for error in report.errors)
    assert any("unavailable image" in error for error in report.errors)

    drive_path = example_record(text_ref="C:/private.txt")
    report = validate_manifest(write_manifest(tmp_path, [drive_path]), TAXONOMY)
    assert any("without traversal" in error for error in report.errors)

    non_normalized = example_record(text_ref="texts//record-1.txt", text_sha256=f"{'1' * 64} ")
    report = validate_manifest(write_manifest(tmp_path, [non_normalized]), TAXONOMY)
    assert any("normalized relative POSIX path" in error for error in report.errors)
    assert any("must not have surrounding whitespace" in error for error in report.errors)


def test_manifest_enforces_annotation_state_and_split_rules(tmp_path):
    pending = example_record(
        annotation_status="pending", category_label=None, annotator_id=None, split="test"
    )
    excluded = example_record(
        record_id="record-2", source_record_id="source-2", group_id="event-2",
        annotation_status="excluded", category_label=None, annotator_id=None,
        exclusion_reason=None, split="unassigned", text_sha256="2" * 64,
    )
    report = validate_manifest(write_manifest(tmp_path, [pending, excluded]), TAXONOMY)
    assert any("only annotated records" in error for error in report.errors)
    assert any("excluded records require exclusion_reason" in error for error in report.errors)


def test_optional_file_verification_accepts_hash_and_rejects_mismatch(tmp_path):
    data_root = tmp_path / "restricted"
    text_path = data_root / "texts" / "record-1.txt"
    text_path.parent.mkdir(parents=True)
    content = b"Synthetic validator fixture only."
    text_path.write_bytes(content)
    checksum = hashlib.sha256(content).hexdigest()
    valid_path = write_manifest(tmp_path, [example_record(text_sha256=checksum)])
    assert validate_manifest(valid_path, TAXONOMY, data_root).valid

    invalid_path = write_manifest(tmp_path, [example_record(text_sha256="f" * 64)])
    report = validate_manifest(invalid_path, TAXONOMY, data_root)
    assert any("does not match file" in error for error in report.errors)


def test_manifest_rejects_empty_and_invalid_jsonl(tmp_path):
    empty = tmp_path / "empty.jsonl"
    empty.write_text("\n", encoding="utf-8")
    assert "manifest contains no records" in validate_manifest(empty, TAXONOMY).errors

    invalid = tmp_path / "invalid.jsonl"
    invalid.write_text("not-json\n", encoding="utf-8")
    report = validate_manifest(invalid, TAXONOMY)
    assert any("invalid UTF-8 JSON" in error for error in report.errors)
