"""Build and validate offline Issue #7 human-review packages; never infer decisions."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re

from .audit import EMAIL, PHONE
from .manifest import _file_hash, load_taxonomy, validate_manifest

SCHEMA_PATH = Path(__file__).parents[1] / "review" / "review_schema_v1.json"
MAPPING_PATH = Path(__file__).parents[1] / "mappings" / "icmyc_v1.json"
REVIEWER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{1,31}$")
FORMULA_PREFIXES = ("=", "+", "-", "@", "＝", "＋", "－", "＠")
LANGUAGES = {"english", "transliterated_indian", "mixed", "unclear", "unusable", "not_reviewed"}
REDACTION_TYPES = {"phone", "email", "name", "address", "identifier", "other"}

COMMON_REVIEW_FIELDS = ["reviewer_id", "reviewed_at", "decision", "reviewer_rationale"]
FORM_FIELDS = {
    "taxonomy": ["review_type", "item_id", "taxonomy_version", "category_id", "current_name",
        "current_definition", "positive_examples", "negative_examples", "proposal_support_count",
        "example_record_ids", "example_previews", *COMMON_REVIEW_FIELDS,
        "recommended_name", "recommended_definition"],
    "mapping": ["review_type", "item_id", "taxonomy_version", "mapping_version", "source_category",
        "source_subcategory", "support_count", "proposed_category", "proposal_status",
        "proposal_confidence", "proposal_rationale", "example_record_ids", "example_previews",
        *COMMON_REVIEW_FIELDS, "approved_category"],
    "privacy": ["review_type", "item_id", "record_id", "text_ref", "reasons", "preview_redacted",
        "taxonomy_version", "mapping_version", *COMMON_REVIEW_FIELDS, "redaction_types", "redaction_spans"],
    "record": ["review_type", "item_id", "record_id", "text_ref", "source_category",
        "source_subcategory", "review_reasons", "preview_redacted", "proposed_category",
        "taxonomy_version", "mapping_version", *COMMON_REVIEW_FIELDS, "approved_category",
        "exclusion_reason", "language_observation"],
    "duplicate": ["review_type", "item_id", "kind", "fingerprint", "record_count", "record_ids",
        "text_refs", "suggested_group_id", "taxonomy_version", "mapping_version",
        *COMMON_REVIEW_FIELDS, "approved_group_id"],
    "license": ["review_type", "item_id", "source_name", "stated_license", "exact_version",
        "attribution", "redistribution_status", "evidence_reference", *COMMON_REVIEW_FIELDS],
    "dataset_approval": ["review_type", "item_id", "dataset_version", "taxonomy_version",
        "mapping_version", "required_prior_gates", *COMMON_REVIEW_FIELDS],
}


def _schema():
    value = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    if set(value["review_types"]) != set(FORM_FIELDS):
        raise ValueError("Review schema and implementation differ")
    return value


def _sha_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _safe_preview(text: str, limit: int = 240) -> str:
    value = " ".join(text.split())
    value = EMAIL.sub("[EMAIL]", value)
    value = PHONE.sub("[PHONE]", value)
    value = value[:limit]
    if value.startswith(FORMULA_PREFIXES):
        value = "'" + value
    return value


def _spreadsheet_safe(value: object) -> object:
    if isinstance(value, str) and (value.startswith(FORMULA_PREFIXES) or value.startswith(("\t", "\r", "\n"))):
        return "'" + value
    return value


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames is None:
            raise ValueError(f"CSV has no header: {path}")
        return reader.fieldnames, list(reader)


def _write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, quoting=csv.QUOTE_ALL, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _spreadsheet_safe(row.get(field, "")) for field in fields})


def _blank_review(row: dict[str, object], review_type: str) -> dict[str, object]:
    row = dict(row, review_type=review_type)
    for field in FORM_FIELDS[review_type]:
        row.setdefault(field, "")
    return row


def _load_snapshot(snapshot: Path):
    if not (snapshot / "COMPLETE").is_file() or (snapshot / "INCOMPLETE").exists():
        raise ValueError("Snapshot is not complete")
    acquisition = json.loads((snapshot / "acquisition.json").read_text(encoding="utf-8"))
    if acquisition.get("country") != "IN" or acquisition.get("source_name") != "opencity-icmyc-india":
        raise ValueError("Reviewed Indian provenance is required")
    if _file_hash(snapshot / "source.csv") != acquisition.get("raw_sha256"):
        raise ValueError("Raw source checksum mismatch")
    if _file_hash(snapshot / "publisher-metadata.json") != acquisition.get("metadata_sha256"):
        raise ValueError("Publisher metadata checksum mismatch")
    report = validate_manifest(snapshot / "manifest.jsonl")
    if not report.valid or report.records != acquisition.get("records_ingested"):
        raise ValueError("Snapshot manifest is invalid")
    manifest = [json.loads(line) for line in (snapshot / "manifest.jsonl").read_text(encoding="utf-8").splitlines()]
    labels = json.loads((snapshot / "source-labels.json").read_text(encoding="utf-8"))
    by_source = {row["source_record_id"]: row for row in labels}
    if len(by_source) != len(manifest):
        raise ValueError("Source-label identities are incomplete or duplicated")
    return acquisition, manifest, by_source


def create_package(snapshot: Path, audit_dir: Path, output: Path, examples_per_group: int = 3):
    if output.exists():
        raise ValueError("Review package exists; use a new version directory")
    if examples_per_group < 1 or examples_per_group > 10:
        raise ValueError("examples_per_group must be between 1 and 10")
    schema = _schema()
    acquisition, manifest, source_labels = _load_snapshot(snapshot)
    if not (audit_dir / "audit.json").is_file():
        raise ValueError("Issue #6 audit is missing")
    audit = json.loads((audit_dir / "audit.json").read_text(encoding="utf-8"))
    if audit.get("raw_sha256") != acquisition.get("raw_sha256") or audit.get("training_approved") is not False:
        raise ValueError("Audit does not match the unapproved source snapshot")
    mapping = json.loads(MAPPING_PATH.read_text(encoding="utf-8"))
    taxonomy = json.loads((Path(__file__).parents[1] / "taxonomy" / "category_v1.json").read_text(encoding="utf-8"))
    if taxonomy.get("status") != "proposed_pending_human_approval" or mapping.get("status") != "proposed":
        raise ValueError("Stage A requires proposed taxonomy and mapping")
    rules = {row["source_subcategory"]: row for row in mapping["rules"]}
    text_by_record, label_by_record, manifest_by_record = {}, {}, {}
    for item in manifest:
        path = snapshot / item["text_ref"]
        content = path.read_bytes()
        if hashlib.sha256(content).hexdigest() != item["text_sha256"]:
            raise ValueError(f"Text integrity failure: {item['record_id']}")
        text_by_record[item["record_id"]] = content.decode("utf-8")
        label_by_record[item["record_id"]] = source_labels[item["source_record_id"]]
        manifest_by_record[item["record_id"]] = item

    grouped = defaultdict(list)
    for item in manifest:
        source = label_by_record[item["record_id"]]
        grouped[(source["source_category"], source["source_subcategory"])].append(item)
    mapping_rows = []
    category_examples = defaultdict(list)
    category_support = Counter()
    for (source_category, source_subcategory), items in sorted(grouped.items()):
        rule = rules.get(source_subcategory, {"proposed_category": None, "status": mapping["default_status"],
            "confidence": "none", "rationale": "No exact proposal rule; human review required."})
        samples = sorted(items, key=lambda item: _sha_text(item["record_id"]))[:examples_per_group]
        ids = [item["record_id"] for item in samples]
        previews = [_safe_preview(text_by_record[item["record_id"]]) for item in samples]
        item_id = "mapping-" + _sha_text(source_category + "\0" + source_subcategory)[:20]
        mapping_rows.append(_blank_review({"item_id": item_id,
            "taxonomy_version": taxonomy["taxonomy_version"], "mapping_version": mapping["mapping_version"],
            "source_category": source_category, "source_subcategory": source_subcategory,
            "support_count": len(items), "proposed_category": rule["proposed_category"] or "",
            "proposal_status": rule["status"], "proposal_confidence": rule["confidence"],
            "proposal_rationale": rule["rationale"], "example_record_ids": "|".join(ids),
            "example_previews": " || ".join(previews)}, "mapping"))
        if rule["status"] == "accepted" and rule["proposed_category"]:
            category_support[rule["proposed_category"]] += len(items)
            category_examples[rule["proposed_category"]].extend(zip(ids, previews))

    taxonomy_rows = []
    for category in taxonomy["categories"]:
        examples = sorted(category_examples[category["id"]], key=lambda pair: _sha_text(pair[0]))[:examples_per_group]
        taxonomy_rows.append(_blank_review({"item_id": "taxonomy-" + category["id"],
            "taxonomy_version": taxonomy["taxonomy_version"], "category_id": category["id"],
            "current_name": category["name"], "current_definition": category["definition"],
            "positive_examples": " | ".join(category["include"]),
            "negative_examples": " | ".join(category["exclude"]),
            "proposal_support_count": category_support[category["id"]],
            "example_record_ids": "|".join(pair[0] for pair in examples),
            "example_previews": " || ".join(pair[1] for pair in examples)}, "taxonomy"))

    suspicious = json.loads((audit_dir / "suspicious-review.json").read_text(encoding="utf-8"))
    suspicious_by_record = {row["record_id"]: row for row in suspicious}
    privacy_rows, record_rows = [], []
    mapping_sample_ids = {record_id for row in mapping_rows for record_id in row["example_record_ids"].split("|") if record_id}
    record_ids = sorted(set(suspicious_by_record) | mapping_sample_ids)
    for record_id in record_ids:
        item = manifest_by_record.get(record_id)
        if item is None:
            raise ValueError(f"Audit references unknown record: {record_id}")
        source = label_by_record[record_id]; reasons = suspicious_by_record.get(record_id, {}).get("reasons", [])
        rule = rules.get(source["source_subcategory"], {"proposed_category": None})
        common = {"item_id": "record-" + record_id, "record_id": record_id, "text_ref": item["text_ref"],
            "source_category": source["source_category"], "source_subcategory": source["source_subcategory"],
            "review_reasons": "|".join(sorted(set(reasons) | ({"mapping_example"} if record_id in mapping_sample_ids else set()))),
            "preview_redacted": _safe_preview(text_by_record[record_id]),
            "proposed_category": rule.get("proposed_category") or "", "taxonomy_version": taxonomy["taxonomy_version"],
            "mapping_version": mapping["mapping_version"]}
        record_rows.append(_blank_review(common, "record"))
        privacy_reasons = sorted(set(reasons) & {"possible_email", "possible_phone"})
        if privacy_reasons:
            privacy_rows.append(_blank_review({"item_id": "privacy-" + record_id, "record_id": record_id,
                "text_ref": item["text_ref"], "reasons": "|".join(privacy_reasons),
                "preview_redacted": _safe_preview(text_by_record[record_id]),
                "taxonomy_version": taxonomy["taxonomy_version"], "mapping_version": mapping["mapping_version"]}, "privacy"))

    duplicate_source = json.loads((audit_dir / "duplicate-review.json").read_text(encoding="utf-8"))
    duplicate_rows = []
    for group in duplicate_source:
        records = group["records"]
        duplicate_item = _sha_text(group["kind"] + "\0" + group["fingerprint"])
        duplicate_rows.append(_blank_review({"item_id": "duplicate-" + duplicate_item[:20],
            "kind": group["kind"], "fingerprint": group["fingerprint"], "record_count": group["count"],
            "record_ids": "|".join(row["record_id"] for row in records),
            "text_refs": "|".join(row["text_ref"] for row in records),
            "suggested_group_id": "reviewed-duplicate-" + group["fingerprint"][:20],
            "taxonomy_version": taxonomy["taxonomy_version"], "mapping_version": mapping["mapping_version"]}, "duplicate"))

    license_rows = [_blank_review({"item_id": "license-opencity-icmyc",
        "source_name": acquisition["source_name"], "stated_license": "cc-by-sa",
        "exact_version": "UNKNOWN / UNVERIFIED", "attribution": "OpenCity / Janaagraha iCMyC / Vaidyanathan R",
        "redistribution_status": "UNKNOWN / UNVERIFIED",
        "evidence_reference": "research/ICMYC_DATASHEET.md and retained publisher-metadata.json"}, "license")]
    approval_rows = [_blank_review({"item_id": "approval-" + acquisition["dataset_version"],
        "dataset_version": acquisition["dataset_version"], "taxonomy_version": taxonomy["taxonomy_version"],
        "mapping_version": mapping["mapping_version"],
        "required_prior_gates": "taxonomy|mapping|privacy|record|duplicate|license"}, "dataset_approval")]
    forms = {"taxonomy": taxonomy_rows, "mapping": mapping_rows, "privacy": privacy_rows,
        "record": record_rows, "duplicate": duplicate_rows, "license": license_rows,
        "dataset_approval": approval_rows}

    output.mkdir(parents=True); (output / "forms").mkdir(); (output / "submissions").mkdir()
    hashes, counts = {}, {}
    for review_type, rows in forms.items():
        item_ids = [row["item_id"] for row in rows]
        if len(item_ids) != len(set(item_ids)):
            raise ValueError(f"Generated {review_type} form has duplicate item IDs")
        path = output / "forms" / f"{review_type}_review.csv"
        _write_csv(path, FORM_FIELDS[review_type], rows)
        hashes[path.name] = _file_hash(path); counts[review_type] = len(rows)
    package = {"schema_version": schema["schema_version"], "dataset_version": acquisition["dataset_version"],
        "source_name": acquisition["source_name"], "country": "IN", "raw_sha256": acquisition["raw_sha256"],
        "taxonomy_version": taxonomy["taxonomy_version"], "taxonomy_status": taxonomy["status"],
        "mapping_version": mapping["mapping_version"], "mapping_status": mapping["status"],
        "snapshot_manifest_sha256": _file_hash(snapshot / "manifest.jsonl"),
        "audit_sha256": _file_hash(audit_dir / "audit.json"), "schema_sha256": _file_hash(SCHEMA_PATH),
        "taxonomy_sha256": _file_hash(Path(__file__).parents[1] / "taxonomy" / "category_v1.json"),
        "mapping_sha256": _file_hash(MAPPING_PATH), "generator_sha256": _file_hash(Path(__file__)),
        "counts": counts, "form_sha256": hashes, "human_decisions_present": False,
        "training_approved": False}
    package_text = json.dumps(package, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    (output / "package.json").write_text(package_text, encoding="utf-8")
    instructions = (
        "CivicAI Issue #7 Stage A review package\n\n"
        "1. Copy one or more forms into submissions/ and append your reviewer code to each filename.\n"
        "2. Do not alter immutable/source columns. Fill only reviewer_id, reviewed_at, decision, "
        "reviewer_rationale and the outcome columns to their right. Partial submissions are allowed.\n"
        "3. Use an ISO-8601 timestamp with timezone. Use a pseudonymous reviewer code, not a personal name.\n"
        "4. Work independently. Do not inspect another reviewer submission before finishing yours.\n"
        "5. Validate every submission with the documented command before merging.\n"
        "6. Dataset approval must remain blank until all other gates are reviewed and conflicts adjudicated.\n"
        "Spreadsheet warning: previews are untrusted source text and are escaped, but use Protected View and "
        "never enable macros or external content.\n"
    )
    (output / "REVIEW_INSTRUCTIONS.txt").write_text(instructions, encoding="utf-8")
    (output / "COMPLETE").write_text("Review package generated; no human decisions are implied.\n", encoding="utf-8")
    return package


def _timestamp(value: str) -> bool:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.tzinfo is not None
    except ValueError:
        return False


def validate_submission(package_dir: Path, submission: Path):
    package = json.loads((package_dir / "package.json").read_text(encoding="utf-8")); schema = _schema()
    fields, rows = _read_csv(submission)
    if not rows:
        raise ValueError("Submission has no rows")
    review_types = {row.get("review_type", "") for row in rows}
    if len(review_types) != 1 or next(iter(review_types)) not in FORM_FIELDS:
        raise ValueError("Submission must contain one known review_type")
    review_type = next(iter(review_types)); expected_fields = FORM_FIELDS[review_type]
    if fields != expected_fields:
        raise ValueError("Submission header differs from the generated form")
    template_path = package_dir / "forms" / f"{review_type}_review.csv"
    if _file_hash(template_path) != package["form_sha256"].get(template_path.name):
        raise ValueError("Generated template was modified")
    _, template_rows = _read_csv(template_path); template = {row["item_id"]: row for row in template_rows}
    if len(template) != len(template_rows):
        raise ValueError("Generated template has duplicate item IDs")
    immutable = [field for field in expected_fields if field not in COMMON_REVIEW_FIELDS
                 and field not in schema["review_types"][review_type]["outcome_fields"]]
    seen, reviewers, completed = set(), set(), []
    taxonomy_categories = load_taxonomy()[1]
    for line, row in enumerate(rows, 2):
        item_id = row.get("item_id", "")
        if item_id in seen: raise ValueError(f"line {line}: duplicate item_id")
        seen.add(item_id)
        if item_id not in template: raise ValueError(f"line {line}: unknown item_id")
        changed = [field for field in immutable if row.get(field, "") != template[item_id].get(field, "")]
        if changed:
            raise ValueError(f"line {line}: immutable review context changed: {', '.join(changed)}")
        decision = row.get("decision", "").strip()
        review_values = [row.get(field, "").strip() for field in COMMON_REVIEW_FIELDS
                         + schema["review_types"][review_type]["outcome_fields"]]
        if not decision:
            if any(review_values): raise ValueError(f"line {line}: partial decision without decision state")
            continue
        reviewer = row["reviewer_id"].strip(); reviewers.add(reviewer)
        if not REVIEWER.fullmatch(reviewer): raise ValueError(f"line {line}: invalid reviewer_id")
        if not _timestamp(row["reviewed_at"].strip()): raise ValueError(f"line {line}: reviewed_at needs timezone")
        if decision not in schema["review_types"][review_type]["decisions"]:
            raise ValueError(f"line {line}: invalid decision")
        rationale = row["reviewer_rationale"].strip()
        if decision in {"propose_revision", "remove", "needs_discussion", "reject_mapping", "ambiguous",
                        "record_level_review", "exclude_source_subgroup", "exclude", "additional_review",
                        "needs_adjudication", "defer", "exclude_duplicates", "needs_review", "rejected",
                        "not_approved"} and not rationale:
            raise ValueError(f"line {line}: rationale required for this decision")
        category = row.get("approved_category", "").strip()
        if category and category not in taxonomy_categories: raise ValueError(f"line {line}: invalid category")
        if review_type == "mapping" and decision == "approve_mapping":
            if not category or category != row["proposed_category"]:
                raise ValueError(f"line {line}: approval must preserve the proposed category")
        if review_type == "mapping" and decision == "propose_revision" and not category:
            raise ValueError(f"line {line}: mapping revision requires a category")
        if review_type == "record" and decision == "label" and not category:
            raise ValueError(f"line {line}: label decision requires a category")
        if review_type == "record" and decision == "exclude" and not row["exclusion_reason"].strip():
            raise ValueError(f"line {line}: exclusion requires a reason")
        language = row.get("language_observation", "").strip()
        if language and language not in LANGUAGES: raise ValueError(f"line {line}: invalid language observation")
        if review_type == "privacy" and decision == "redact":
            types = {value for value in row["redaction_types"].split("|") if value}
            if not types or not types <= REDACTION_TYPES: raise ValueError(f"line {line}: invalid redaction types")
            if types - {"phone", "email"} and not row["redaction_spans"].strip():
                raise ValueError(f"line {line}: non-pattern redaction needs explicit spans")
        if review_type == "duplicate" and decision == "keep_together" and not row["approved_group_id"].strip():
            raise ValueError(f"line {line}: keep_together requires approved_group_id")
        normalized = dict(row)
        for field in COMMON_REVIEW_FIELDS + schema["review_types"][review_type]["outcome_fields"]:
            normalized[field] = normalized.get(field, "").strip()
        completed.append(normalized)
    if len(reviewers) > 1:
        raise ValueError("One submission file must contain only one reviewer_id")
    return {"review_type": review_type, "reviewer_id": next(iter(reviewers), None),
        "completed": len(completed), "pending_in_file": len(rows) - len(completed), "rows": completed}


def merge_submissions(package_dir: Path, submissions: list[Path], output: Path):
    if output.exists(): raise ValueError("Merged output exists; use a new version directory")
    if not submissions: raise ValueError("At least one submission is required")
    package = json.loads((package_dir / "package.json").read_text(encoding="utf-8")); schema = _schema()
    all_rows, reviewer_keys = [], set()
    for submission in submissions:
        report = validate_submission(package_dir, submission)
        for row in report["rows"]:
            key = (report["review_type"], row["item_id"], row["reviewer_id"])
            if key in reviewer_keys: raise ValueError("Duplicate reviewer submission for an item")
            reviewer_keys.add(key); all_rows.append(row)
    if not all_rows:
        raise ValueError("No completed human decisions were supplied")
    grouped = defaultdict(list)
    for row in all_rows: grouped[(row["review_type"], row["item_id"])].append(row)
    resolved, conflicts = [], []
    for (review_type, item_id), rows in sorted(grouped.items()):
        outcome_fields = schema["review_types"][review_type]["outcome_fields"]
        payloads = defaultdict(list)
        for row in rows:
            payload = {"decision": row["decision"], **{field: row.get(field, "") for field in outcome_fields}}
            payloads[json.dumps(payload, sort_keys=True)].append(row["reviewer_id"])
        item = {"review_type": review_type, "item_id": item_id, "review_count": len(rows)}
        if len(payloads) == 1:
            payload_text, reviewers = next(iter(payloads.items()))
            resolved.append({**item, "resolution": "consensus" if len(rows) > 1 else "single_review",
                "reviewers": reviewers, "payload": json.loads(payload_text),
                "reviews": [{"reviewer_id": row["reviewer_id"], "reviewed_at": row["reviewed_at"],
                    "rationale": row["reviewer_rationale"]} for row in rows]})
        else:
            conflicts.append({**item, "submissions": [{"reviewer_id": row["reviewer_id"],
                "decision": row["decision"], "outcomes": {field: row.get(field, "") for field in outcome_fields},
                "reviewed_at": row["reviewed_at"], "rationale": row["reviewer_rationale"]} for row in rows]})
    output.mkdir(parents=True)
    decisions = {"schema_version": package["schema_version"], "dataset_version": package["dataset_version"],
        "package_sha256": _file_hash(package_dir / "package.json"), "resolved": resolved,
        "conflicts": conflicts, "training_approved": False}
    (output / "decisions.json").write_text(json.dumps(decisions, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    adjudication_fields = ["review_type", "item_id", "conflicting_submissions_json", "adjudicator_id",
        "adjudicated_at", "final_decision", "final_outcomes_json", "adjudication_rationale"]
    adjudication_rows = [{"review_type": row["review_type"], "item_id": row["item_id"],
        "conflicting_submissions_json": json.dumps(row["submissions"], ensure_ascii=False, sort_keys=True)}
        for row in conflicts]
    _write_csv(output / "adjudication_review.csv", adjudication_fields, adjudication_rows)
    report = {"submissions": len(submissions), "completed_decisions": len(all_rows),
        "resolved_items": len(resolved), "conflicting_items": len(conflicts), "training_approved": False}
    (output / "report.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return report


def validate_adjudication(decisions_path: Path, adjudication_path: Path):
    decisions = json.loads(decisions_path.read_text(encoding="utf-8")); schema = _schema()
    fields, rows = _read_csv(adjudication_path)
    expected = ["review_type", "item_id", "conflicting_submissions_json", "adjudicator_id",
        "adjudicated_at", "final_decision", "final_outcomes_json", "adjudication_rationale"]
    if fields != expected: raise ValueError("Adjudication header is invalid")
    conflicts = {(row["review_type"], row["item_id"]): row for row in decisions["conflicts"]}
    seen, resolved = set(), []
    for line, row in enumerate(rows, 2):
        key = (row["review_type"], row["item_id"])
        if key in seen: raise ValueError(f"line {line}: duplicate adjudication")
        seen.add(key)
        if key not in conflicts: raise ValueError(f"line {line}: unknown conflict")
        try: supplied_conflict = json.loads(row["conflicting_submissions_json"])
        except json.JSONDecodeError as exc: raise ValueError(f"line {line}: invalid conflict JSON") from exc
        if supplied_conflict != conflicts[key]["submissions"]:
            raise ValueError(f"line {line}: conflicting submissions were modified")
        if not row["final_decision"].strip(): continue
        if not REVIEWER.fullmatch(row["adjudicator_id"].strip()) or not _timestamp(row["adjudicated_at"].strip()):
            raise ValueError(f"line {line}: adjudicator and timezone timestamp required")
        if row["final_decision"] not in schema["review_types"][row["review_type"]]["decisions"]:
            raise ValueError(f"line {line}: invalid final decision")
        try: outcomes = json.loads(row["final_outcomes_json"] or "{}")
        except json.JSONDecodeError as exc: raise ValueError(f"line {line}: invalid outcomes JSON") from exc
        allowed_outcomes = set(schema["review_types"][row["review_type"]]["outcome_fields"])
        if (not isinstance(outcomes, dict) or not set(outcomes) <= allowed_outcomes
                or not row["adjudication_rationale"].strip()):
            raise ValueError(f"line {line}: outcomes object and rationale required")
        resolved.append({"review_type": row["review_type"], "item_id": row["item_id"],
            "adjudicator_id": row["adjudicator_id"], "adjudicated_at": row["adjudicated_at"],
            "decision": row["final_decision"],
            "outcomes": outcomes, "rationale": row["adjudication_rationale"]})
    return {"resolved": resolved, "pending": len(conflicts) - len(resolved)}


def apply_adjudication(decisions_path: Path, adjudication_path: Path, output: Path):
    if output.exists(): raise ValueError("Adjudicated output exists; use a new path")
    decisions = json.loads(decisions_path.read_text(encoding="utf-8"))
    adjudication = validate_adjudication(decisions_path, adjudication_path)
    resolved_by_key = {(row["review_type"], row["item_id"]): row for row in adjudication["resolved"]}
    remaining, adjudicated = [], []
    for conflict in decisions["conflicts"]:
        key = (conflict["review_type"], conflict["item_id"])
        resolution = resolved_by_key.get(key)
        if resolution is None:
            remaining.append(conflict); continue
        adjudicated.append({"review_type": conflict["review_type"], "item_id": conflict["item_id"],
            "review_count": conflict["review_count"], "resolution": "adjudicated",
            "reviewers": [row["reviewer_id"] for row in conflict["submissions"]],
            "reviews": conflict["submissions"],
            "payload": {"decision": resolution["decision"], **resolution["outcomes"]},
            "adjudication": {"adjudicator_id": resolution["adjudicator_id"],
                "adjudicated_at": resolution["adjudicated_at"], "rationale": resolution["rationale"]}})
    result = dict(decisions)
    result["resolved"] = decisions["resolved"] + adjudicated
    result["conflicts"] = remaining
    result["training_approved"] = False
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return {"adjudicated": len(adjudicated), "remaining_conflicts": len(remaining), "training_approved": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__); commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create"); create.add_argument("--snapshot", type=Path, required=True)
    create.add_argument("--audit", type=Path, required=True); create.add_argument("--output", type=Path, required=True)
    create.add_argument("--examples-per-group", type=int, default=3)
    validate = commands.add_parser("validate"); validate.add_argument("--package", type=Path, required=True)
    validate.add_argument("--submission", type=Path, required=True)
    merge = commands.add_parser("merge"); merge.add_argument("--package", type=Path, required=True)
    merge.add_argument("--submission", type=Path, action="append", required=True); merge.add_argument("--output", type=Path, required=True)
    adjudicate = commands.add_parser("validate-adjudication"); adjudicate.add_argument("--decisions", type=Path, required=True)
    adjudicate.add_argument("--adjudication", type=Path, required=True)
    apply_review = commands.add_parser("apply-adjudication"); apply_review.add_argument("--decisions", type=Path, required=True)
    apply_review.add_argument("--adjudication", type=Path, required=True); apply_review.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "create": result = create_package(args.snapshot, args.audit, args.output, args.examples_per_group)
        elif args.command == "validate": result = validate_submission(args.package, args.submission)
        elif args.command == "merge": result = merge_submissions(args.package, args.submission, args.output)
        elif args.command == "validate-adjudication": result = validate_adjudication(args.decisions, args.adjudication)
        else: result = apply_adjudication(args.decisions, args.adjudication, args.output)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        parser.exit(1, f"Review operation failed: {exc}\n")
    result.pop("rows", None); print(json.dumps(result, ensure_ascii=True, indent=2)); return 0


if __name__ == "__main__": raise SystemExit(main())
