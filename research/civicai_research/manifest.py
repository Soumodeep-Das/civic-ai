from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


DEFAULT_TAXONOMY = Path(__file__).parents[1] / "taxonomy" / "category_v1.json"
MAX_LINE_BYTES = 1_048_576
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
SPLITS = {"unassigned", "train", "validation", "test"}
ANNOTATION_STATES = {"pending", "annotated", "needs_adjudication", "excluded"}
FIELDS = {
    "record_id", "source_name", "source_record_id", "source_terms_ref", "consent_or_basis",
    "dataset_version", "taxonomy_version", "annotation_status", "category_label", "annotator_id",
    "annotation_notes", "exclusion_reason", "group_id", "split", "text_available", "text_ref",
    "text_sha256", "image_available", "image_ref", "image_sha256",
}


@dataclass
class ManifestReport:
    records: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    categories: Counter[str] = field(default_factory=Counter)
    splits: Counter[str] = field(default_factory=Counter)

    @property
    def valid(self) -> bool:
        return not self.errors

    def as_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "records": self.records,
            "categories": dict(sorted(self.categories.items())),
            "splits": dict(sorted(self.splits.items())),
            "warnings": self.warnings,
            "errors": self.errors,
        }


def load_taxonomy(path: Path = DEFAULT_TAXONOMY) -> tuple[str, set[str]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        version = payload["taxonomy_version"]
        categories = payload["categories"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise ValueError(f"Invalid taxonomy file {path}: {exc}") from exc
    if not isinstance(version, str) or not version.strip():
        raise ValueError("Taxonomy version must be a non-empty string")
    if not isinstance(categories, list) or not categories:
        raise ValueError("Taxonomy must contain categories")
    identifiers = [item.get("id") for item in categories if isinstance(item, dict)]
    if len(identifiers) != len(categories) or any(not isinstance(value, str) or not value for value in identifiers):
        raise ValueError("Every taxonomy category must have a non-empty string id")
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("Taxonomy category ids must be unique")
    return version, set(identifiers)


def _text(record: dict[str, Any], field_name: str, line: int, errors: list[str], *, nullable: bool = False) -> str | None:
    value = record.get(field_name)
    if nullable and value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        errors.append(f"line {line}: {field_name} must be a non-empty string" + (" or null" if nullable else ""))
        return None
    return value.strip()


def _nullable_text(record: dict[str, Any], field_name: str, line: int, errors: list[str]) -> str | None:
    value = record.get(field_name)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        errors.append(f"line {line}: {field_name} must be a non-empty string or null")
        return None
    return value.strip()


def _safe_reference(value: str | None, field_name: str, line: int, errors: list[str]) -> None:
    if value is None:
        return
    path = PurePosixPath(value)
    if (
        value != value.strip() or "\\" in value or "\x00" in value or re.match(r"^[A-Za-z]:", value)
        or path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts)
        or path.as_posix() != value
    ):
        errors.append(f"line {line}: {field_name} must be a normalized relative POSIX path without traversal")


def _sha256(value: str | None, field_name: str, line: int, errors: list[str]) -> None:
    if value is not None and not SHA256_PATTERN.fullmatch(value):
        errors.append(f"line {line}: {field_name} must be a lowercase 64-character SHA-256 or null")


def _validate_modality(record: dict[str, Any], prefix: str, line: int, errors: list[str]) -> None:
    available = record.get(f"{prefix}_available")
    raw_reference = record.get(f"{prefix}_ref")
    raw_checksum = record.get(f"{prefix}_sha256")
    reference = _nullable_text(record, f"{prefix}_ref", line, errors)
    checksum = _nullable_text(record, f"{prefix}_sha256", line, errors)
    if not isinstance(available, bool):
        errors.append(f"line {line}: {prefix}_available must be a boolean")
        return
    if available and (reference is None or checksum is None):
        errors.append(f"line {line}: available {prefix} requires {prefix}_ref and {prefix}_sha256")
    if not available and (reference is not None or checksum is not None):
        errors.append(f"line {line}: unavailable {prefix} must not have a reference or checksum")
    _safe_reference(reference, f"{prefix}_ref", line, errors)
    _sha256(checksum, f"{prefix}_sha256", line, errors)
    if isinstance(raw_reference, str) and raw_reference != reference:
        errors.append(f"line {line}: {prefix}_ref must not have surrounding whitespace")
    if isinstance(raw_checksum, str) and raw_checksum != checksum:
        errors.append(f"line {line}: {prefix}_sha256 must not have surrounding whitespace")


def _validate_record(
    record: dict[str, Any], line: int, taxonomy_version: str, categories: set[str], report: ManifestReport,
) -> None:
    missing = FIELDS - record.keys()
    unknown = record.keys() - FIELDS
    if missing:
        report.errors.append(f"line {line}: missing fields: {', '.join(sorted(missing))}")
    if unknown:
        report.errors.append(f"line {line}: unknown fields: {', '.join(sorted(unknown))}")
    if missing:
        return

    record_id = _text(record, "record_id", line, report.errors)
    source_name = _text(record, "source_name", line, report.errors)
    source_record_id = _nullable_text(record, "source_record_id", line, report.errors)
    _text(record, "source_terms_ref", line, report.errors)
    _nullable_text(record, "consent_or_basis", line, report.errors)
    _text(record, "dataset_version", line, report.errors)
    group_id = _text(record, "group_id", line, report.errors)
    annotation_notes = _nullable_text(record, "annotation_notes", line, report.errors)
    exclusion_reason = _nullable_text(record, "exclusion_reason", line, report.errors)
    annotator_id = _nullable_text(record, "annotator_id", line, report.errors)

    if record.get("taxonomy_version") != taxonomy_version:
        report.errors.append(f"line {line}: taxonomy_version must be {taxonomy_version!r}")
    status = record.get("annotation_status")
    if not isinstance(status, str) or status not in ANNOTATION_STATES:
        report.errors.append(f"line {line}: annotation_status must be one of {sorted(ANNOTATION_STATES)}")
    split = record.get("split")
    if not isinstance(split, str) or split not in SPLITS:
        report.errors.append(f"line {line}: split must be one of {sorted(SPLITS)}")
    else:
        report.splits[split] += 1

    category = record.get("category_label")
    if category is not None and (not isinstance(category, str) or category not in categories):
        report.errors.append(f"line {line}: category_label must be null or one of {sorted(categories)}")
    if isinstance(category, str) and category in categories:
        report.categories[category] += 1

    if status == "annotated":
        if not isinstance(category, str) or category not in categories:
            report.errors.append(f"line {line}: annotated records require a valid category_label")
        if annotator_id is None:
            report.errors.append(f"line {line}: annotated records require annotator_id")
        if exclusion_reason is not None:
            report.errors.append(f"line {line}: annotated records must not have exclusion_reason")
    elif status == "pending":
        if category is not None or annotator_id is not None:
            report.errors.append(f"line {line}: pending records must not have category_label or annotator_id")
    elif status == "needs_adjudication":
        if annotator_id is None or annotation_notes is None:
            report.errors.append(f"line {line}: needs_adjudication requires annotator_id and annotation_notes")
    elif status == "excluded":
        if category is not None or exclusion_reason is None:
            report.errors.append(f"line {line}: excluded records require exclusion_reason and no category_label")

    if status != "excluded" and exclusion_reason is not None:
        report.errors.append(f"line {line}: only excluded records may have exclusion_reason")

    if split != "unassigned" and status != "annotated":
        report.errors.append(f"line {line}: only annotated records may have an assigned split")

    _validate_modality(record, "text", line, report.errors)
    _validate_modality(record, "image", line, report.errors)
    if record.get("text_available") is False and record.get("image_available") is False:
        report.errors.append(f"line {line}: at least one modality must be available")

    record["record_id"] = record_id
    record["source_name"] = source_name
    record["source_record_id"] = source_record_id
    record["group_id"] = group_id


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verify_files(records: Iterable[tuple[int, dict[str, Any]]], data_root: Path, report: ManifestReport) -> None:
    root = data_root.resolve()
    for line, record in records:
        for prefix in ("text", "image"):
            if record.get(f"{prefix}_available") is not True:
                continue
            reference = record.get(f"{prefix}_ref")
            checksum = record.get(f"{prefix}_sha256")
            if not isinstance(reference, str) or not isinstance(checksum, str):
                continue
            candidate = (root / Path(*PurePosixPath(reference).parts)).resolve()
            if not candidate.is_relative_to(root):
                report.errors.append(f"line {line}: {prefix}_ref resolves outside data root")
            elif not candidate.is_file():
                report.errors.append(f"line {line}: referenced {prefix} file does not exist: {reference}")
            elif _file_hash(candidate) != checksum:
                report.errors.append(f"line {line}: {prefix}_sha256 does not match file: {reference}")


def validate_manifest(
    manifest_path: Path, taxonomy_path: Path = DEFAULT_TAXONOMY, data_root: Path | None = None,
) -> ManifestReport:
    taxonomy_version, categories = load_taxonomy(taxonomy_path)
    report = ManifestReport()
    parsed: list[tuple[int, dict[str, Any]]] = []
    try:
        stream = manifest_path.open("rb")
    except OSError as exc:
        report.errors.append(f"cannot open manifest {manifest_path}: {exc}")
        return report

    with stream:
        for line_number, raw in enumerate(stream, 1):
            if not raw.strip():
                continue
            if len(raw) > MAX_LINE_BYTES:
                report.errors.append(f"line {line_number}: exceeds {MAX_LINE_BYTES} bytes")
                continue
            try:
                record = json.loads(raw)
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                report.errors.append(f"line {line_number}: invalid UTF-8 JSON: {exc}")
                continue
            if not isinstance(record, dict):
                report.errors.append(f"line {line_number}: each JSONL value must be an object")
                continue
            report.records += 1
            error_count = len(report.errors)
            _validate_record(record, line_number, taxonomy_version, categories, report)
            if len(report.errors) == error_count:
                parsed.append((line_number, record))

    if report.records == 0:
        report.errors.append("manifest contains no records")

    identities: dict[str, int] = {}
    source_identities: dict[tuple[str, str], int] = {}
    group_splits: defaultdict[str, set[str]] = defaultdict(set)
    hashes: defaultdict[tuple[str, str], list[tuple[int, str]]] = defaultdict(list)
    for line, record in parsed:
        record_id = record.get("record_id")
        if isinstance(record_id, str):
            if record_id in identities:
                report.errors.append(f"line {line}: duplicate record_id also used on line {identities[record_id]}")
            else:
                identities[record_id] = line
        source_name, source_record_id = record.get("source_name"), record.get("source_record_id")
        if isinstance(source_name, str) and isinstance(source_record_id, str):
            key = (source_name, source_record_id)
            if key in source_identities:
                report.errors.append(f"line {line}: duplicate source identity also used on line {source_identities[key]}")
            else:
                source_identities[key] = line
        group_id, split = record.get("group_id"), record.get("split")
        if isinstance(group_id, str) and split in SPLITS - {"unassigned"}:
            group_splits[group_id].add(split)
        for prefix in ("text", "image"):
            checksum = record.get(f"{prefix}_sha256")
            if not isinstance(checksum, str) or not SHA256_PATTERN.fullmatch(checksum):
                continue
            hashes[(prefix, checksum)].append((line, split))

    for group_id, assigned_splits in sorted(group_splits.items()):
        if len(assigned_splits) > 1:
            report.errors.append(f"group_id {group_id!r} crosses assigned splits: {', '.join(sorted(assigned_splits))}")

    split_order = {"train": 0, "validation": 1, "test": 2}
    for (prefix, _checksum), occurrences in hashes.items():
        if len(occurrences) < 2:
            continue
        assigned_splits = {split for _line, split in occurrences if split != "unassigned"}
        lines = ", ".join(str(line) for line, _split in occurrences)
        if len(assigned_splits) > 1:
            ordered = sorted(assigned_splits, key=split_order.get)
            report.errors.append(f"{prefix} checksum crosses {'/'.join(ordered)} splits; lines {lines}")
        else:
            report.warnings.append(f"duplicate {prefix} checksum on lines {lines}")

    if data_root is not None:
        _verify_files(parsed, data_root, report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a CivicAI research JSONL manifest")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--taxonomy", type=Path, default=DEFAULT_TAXONOMY)
    parser.add_argument("--data-root", type=Path, help="Also verify referenced files and SHA-256 hashes")
    parser.add_argument("--json", action="store_true", help="Print the report as JSON")
    args = parser.parse_args(argv)
    report = validate_manifest(args.manifest, args.taxonomy, args.data_root)
    if args.json:
        print(json.dumps(report.as_dict(), indent=2))
    else:
        print(f"records={report.records} valid={str(report.valid).lower()}")
        print(f"splits={dict(sorted(report.splits.items()))}")
        print(f"categories={dict(sorted(report.categories.items()))}")
        for warning in report.warnings:
            print(f"WARNING: {warning}")
        for error in report.errors:
            print(f"ERROR: {error}")
    return 0 if report.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
