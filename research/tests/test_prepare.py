import hashlib
import json

from PIL import Image
import pytest

from research.civicai_research.prepare import main, prepare
from research.civicai_research.manifest import validate_manifest


def record(root, number, *, text=None, **overrides):
    content = (text or f"Synthetic fixture {number}").encode()
    name = f"text-{number}.txt"
    (root / name).write_bytes(content)
    row = dict(record_id=f"record-{number}", source_name="synthetic-test",
               source_record_id=str(number), source_terms_ref="synthetic-test-only",
               consent_or_basis=None, dataset_version="fixture-v1",
               taxonomy_version="civicai-category-v1", annotation_status="annotated",
               category_label="road_damage", annotator_id="test", annotation_notes=None,
               exclusion_reason=None, group_id=f"event-{number}", split="unassigned",
               text_available=True, text_ref=name, text_sha256=hashlib.sha256(content).hexdigest(),
               image_available=False, image_ref=None, image_sha256=None)
    row.update(overrides)
    return row


def manifest(root, records):
    path = root / "input.jsonl"
    path.write_text("".join(json.dumps(row) + "\n" for row in records), encoding="utf-8")
    return path


def read_rows(output):
    return [json.loads(line) for line in (output / "manifest.jsonl").read_text().splitlines()]


def test_repeatable_and_order_independent(tmp_path):
    rows = [record(tmp_path, n) for n in range(60)]
    path = manifest(tmp_path, rows)
    first = prepare(path, tmp_path, tmp_path / "first", paired=False)
    prepare(path, tmp_path, tmp_path / "same", paired=False)
    assert (tmp_path / "first/report.json").read_bytes() == (tmp_path / "same/report.json").read_bytes()
    manifest(tmp_path, list(reversed(rows)))
    prepare(path, tmp_path, tmp_path / "reverse", paired=False)
    assert read_rows(tmp_path / "first") == read_rows(tmp_path / "reverse")
    assert set(row["split"] for row in read_rows(tmp_path / "first")) == {"train", "validation", "test"}
    assert not first["training_approved"]
    assert "streetlight" in first["missing_categories"]["train"]


def test_transitive_event_and_normalized_text_connections(tmp_path):
    rows = [record(tmp_path, 1, text="Pothole NEAR school"),
            record(tmp_path, 2, text=" pothole   near school ", group_id="shared"),
            record(tmp_path, 3, group_id="shared")]
    prepare(manifest(tmp_path, rows), tmp_path, tmp_path / "out", paired=False)
    actual = read_rows(tmp_path / "out")
    assert len({row["group_id"] for row in actual}) == 1
    assert len({row["split"] for row in actual}) == 1


def test_conflicting_labels_quarantine_entire_component(tmp_path):
    rows = [record(tmp_path, 1, group_id="shared"),
            record(tmp_path, 2, group_id="shared", category_label="streetlight")]
    report = prepare(manifest(tmp_path, rows), tmp_path, tmp_path / "out", paired=False)
    assert report["conflicting_components"]
    assert all(row["split"] == "unassigned" for row in read_rows(tmp_path / "out"))


def test_paired_default_does_not_invent_text_image_pairs(tmp_path):
    report = prepare(manifest(tmp_path, [record(tmp_path, 1)]), tmp_path, tmp_path / "out")
    assert report["unassigned_reasons"] == {"missing_paired_modality": 1}


def test_decoded_image_duplicates_with_different_encoding(tmp_path):
    rows = [record(tmp_path, n) for n in (1, 2)]
    for n, row in enumerate(rows):
        path = tmp_path / f"image-{n}.png"
        Image.new("RGB", (10, 10), "red").save(path, compress_level=n * 9)
        row.update(image_available=True, image_ref=path.name,
                   image_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    report = prepare(manifest(tmp_path, rows), tmp_path, tmp_path / "out")
    assert report["duplicate_connections"]["decoded_pixels"] == 1
    assert len({row["split"] for row in read_rows(tmp_path / "out")}) == 1


@pytest.mark.parametrize("fault", ["changed_hash", "missing_file", "empty_text", "invalid_utf8", "corrupt_image"])
def test_bad_inputs_do_not_publish_output(tmp_path, fault):
    row = record(tmp_path, 1)
    text_path = tmp_path / row["text_ref"]
    if fault == "changed_hash":
        text_path.write_text("changed")
    elif fault == "missing_file":
        text_path.unlink()
    elif fault in {"empty_text", "invalid_utf8"}:
        content = b"   " if fault == "empty_text" else b"\xff"
        text_path.write_bytes(content)
        row["text_sha256"] = hashlib.sha256(content).hexdigest()
    else:
        image = tmp_path / "bad.png"
        image.write_bytes(b"not an image")
        row.update(image_available=True, image_ref=image.name,
                   image_sha256=hashlib.sha256(image.read_bytes()).hexdigest())
    with pytest.raises((ValueError, OSError)):
        prepare(manifest(tmp_path, [row]), tmp_path, tmp_path / "out")
    assert not (tmp_path / "out").exists()


def test_no_overwrite_or_resplit(tmp_path):
    path = manifest(tmp_path, [record(tmp_path, 1)])
    prepare(path, tmp_path, tmp_path / "out", paired=False)
    with pytest.raises(ValueError, match="already exists"):
        prepare(path, tmp_path, tmp_path / "out")
    with pytest.raises(ValueError, match="cannot be resplit"):
        prepare(tmp_path / "out/manifest.jsonl", tmp_path, tmp_path / "new")


@pytest.mark.parametrize("field", ["annotation_status", "category_label", "split"])
@pytest.mark.parametrize("bad", [[], {}, 4])
def test_invalid_field_types_return_validation_errors(tmp_path, field, bad):
    row = record(tmp_path, 1, **{field: bad})
    report = validate_manifest(manifest(tmp_path, [row]))
    assert not report.valid


def test_cli_produces_verifiable_manifest_and_preserves_input(tmp_path, capsys):
    path = manifest(tmp_path, [record(tmp_path, 1)])
    before = path.read_bytes()
    result = main([str(path), "--data-root", str(tmp_path), "--output", str(tmp_path / "out"), "--allow-unpaired"])
    assert result == 0
    report = json.loads(capsys.readouterr().out)
    assert report["output_manifest_sha256"] == hashlib.sha256((tmp_path / "out/manifest.jsonl").read_bytes()).hexdigest()
    assert validate_manifest(tmp_path / "out/manifest.jsonl", data_root=tmp_path).valid
    assert path.read_bytes() == before


def test_disputed_member_blocks_annotated_related_record(tmp_path):
    rows = [record(tmp_path, 1, group_id="same"),
            record(tmp_path, 2, group_id="same", annotation_status="needs_adjudication",
                   category_label=None, annotation_notes="Ambiguous fixture")]
    prepare(manifest(tmp_path, rows), tmp_path, tmp_path / "out", paired=False)
    assert all(row["split"] == "unassigned" for row in read_rows(tmp_path / "out"))


def test_pending_and_excluded_records_preserved_unassigned(tmp_path):
    rows = [record(tmp_path, 1, annotation_status="pending", category_label=None, annotator_id=None),
            record(tmp_path, 2, annotation_status="excluded", category_label=None, exclusion_reason="Fixture exclusion")]
    report = prepare(manifest(tmp_path, rows), tmp_path, tmp_path / "out", paired=False)
    assert report["unassigned_reasons"] == {"pending": 1, "excluded": 1}
    assert len(read_rows(tmp_path / "out")) == 2


def test_mixed_versions_rejected(tmp_path):
    rows = [record(tmp_path, 1), record(tmp_path, 2, dataset_version="different")]
    with pytest.raises(ValueError, match="One dataset version"):
        prepare(manifest(tmp_path, rows), tmp_path, tmp_path / "out")
