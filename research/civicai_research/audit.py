"""Create a privacy-conscious, reproducible audit of an acquired Indian complaint snapshot."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import re
import unicodedata

from .manifest import _file_hash, load_taxonomy, validate_manifest

DEFAULT_MAPPING = Path(__file__).parents[1] / "mappings" / "icmyc_v1.json"
FIELDS = ("title", "description", "category_title", "sub_category_title", "location",
          "address", "latitude", "longitude", "ward_title", "created_at")
EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
PHONE = re.compile(r"(?<!\d)(?:\+?91[-\s]?)?[6-9]\d{9}(?!\d)")
URL = re.compile(r"^(?:https?://\S+|www\.\S+)$", re.I)
HTML = re.compile(r"<[^>]{1,200}>")


def normalize(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def template(text: str) -> str:
    value = re.sub(r"https?://\S+|www\.\S+", " URL ", normalize(text))
    value = re.sub(r"\d+", " NUMBER ", value)
    return " ".join(re.sub(r"[^\w]+", " ", value).split())


def language_bucket(text: str) -> str:
    bengali = sum("\u0980" <= char <= "\u09ff" for char in text)
    devanagari = sum("\u0900" <= char <= "\u097f" for char in text)
    latin = sum(("a" <= char.casefold() <= "z") for char in text)
    if bengali:
        return "bengali_latin_mixed" if latin else "bengali_script"
    if devanagari:
        return "devanagari_latin_mixed" if latin else "devanagari_script"
    if latin:
        return "latin_script_english_or_transliterated"
    return "unknown_or_other_script"


def audit(snapshot: Path, output: Path, mapping_path: Path = DEFAULT_MAPPING, sample_per_group: int = 5):
    if output.exists():
        raise ValueError("Audit output exists; use a new version directory")
    if not (snapshot / "COMPLETE").is_file() or (snapshot / "INCOMPLETE").exists():
        raise ValueError("Snapshot is not marked complete")
    acquisition = json.loads((snapshot / "acquisition.json").read_text(encoding="utf-8"))
    if acquisition.get("country") != "IN" or acquisition.get("source_name") != "opencity-icmyc-india":
        raise ValueError("Reviewed Indian provenance is required")
    raw = (snapshot / "source.csv").read_bytes()
    if _file_hash(snapshot / "source.csv") != acquisition.get("raw_sha256"):
        raise ValueError("Raw source checksum mismatch")
    manifest_report = validate_manifest(snapshot / "manifest.jsonl")
    if not manifest_report.valid:
        raise ValueError("Manifest invalid: " + "; ".join(manifest_report.errors[:10]))
    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    taxonomy_version, taxonomy_categories = load_taxonomy()
    allowed_mapping_states = {"accepted", "ambiguous", "rejected", "needs_review"}
    if mapping.get("status") != "proposed" or mapping.get("source_name") != acquisition["source_name"]:
        raise ValueError("Mapping must be a proposal for this source")
    if mapping.get("taxonomy_version") != taxonomy_version or mapping.get("default_status") not in allowed_mapping_states:
        raise ValueError("Mapping taxonomy/default status is invalid")
    rules = {}
    for rule in mapping.get("rules", []):
        source_subcategory = rule.get("source_subcategory")
        status, proposed_category = rule.get("status"), rule.get("proposed_category")
        if not isinstance(source_subcategory, str) or not source_subcategory.strip() or source_subcategory.strip() in rules:
            raise ValueError("Mapping source subcategories must be unique non-empty strings")
        if status not in allowed_mapping_states or (proposed_category is not None and proposed_category not in taxonomy_categories):
            raise ValueError("Mapping state/category is invalid")
        if status == "accepted" and proposed_category is None:
            raise ValueError("Accepted mapping requires a proposed category")
        if status == "rejected" and proposed_category is not None:
            raise ValueError("Rejected mapping cannot propose a category")
        if not isinstance(rule.get("confidence"), str) or not isinstance(rule.get("rationale"), str):
            raise ValueError("Mapping confidence and rationale are required")
        rules[source_subcategory.strip()] = rule
    if sample_per_group < 1:
        raise ValueError("sample_per_group must be positive")
    encoding = acquisition["encoding"]
    rows = list(csv.DictReader(raw.decode(encoding).splitlines()))
    manifest = [json.loads(line) for line in (snapshot / "manifest.jsonl").read_text(encoding="utf-8").splitlines()]
    if len(rows) != len(manifest) or len(rows) != acquisition["records_returned"]:
        raise ValueError("Raw/manifest/acquisition counts differ")

    missing = Counter(); categories = Counter(); subcategories = Counter(); mapping_states = Counter()
    proposed = Counter(); accepted_proposed = Counter(); languages = Counter(); years = Counter(); months = Counter(); date_formats = Counter(); wards = Counter()
    quality = Counter(); privacy = Counter(); exact_rows = Counter(); descriptions = Counter()
    title_description = Counter(); templates = Counter(); coordinate = Counter()
    review_groups = defaultdict(list); suspicious = []
    duplicate_description_refs = defaultdict(list); duplicate_template_refs = defaultdict(list)
    for index, (row, item) in enumerate(zip(rows, manifest), 1):
        expected = f"icmyc-{acquisition['raw_sha256'][:12]}-row-{index}"
        if item["record_id"] != expected:
            raise ValueError(f"Manifest order/provenance mismatch at record {index}")
        for field in FIELDS:
            if not row.get(field, "").strip() or row.get(field, "").strip().upper() == "NULL":
                missing[field] += 1
        category = row.get("category_title", "").strip(); subcategory = row.get("sub_category_title", "").strip()
        categories[category] += 1; subcategories[subcategory] += 1; wards[row.get("ward_title", "").strip()] += 1
        rule = rules.get(subcategory, {"status": mapping["default_status"], "proposed_category": None,
                                      "confidence": "none", "rationale": "No exact proposal rule; human review required."})
        mapping_states[rule["status"]] += 1
        if rule["proposed_category"]:
            proposed[rule["proposed_category"]] += 1
            if rule["status"] == "accepted":
                accepted_proposed[rule["proposed_category"]] += 1
        review_key = f"{rule['status']}:{rule['proposed_category'] or 'unmapped'}"
        review_groups[review_key].append({"record_id": item["record_id"], "text_ref": item["text_ref"],
            "source_category": category, "source_subcategory": subcategory,
            "proposed_category": rule["proposed_category"], "mapping_status": rule["status"],
            "mapping_confidence": rule["confidence"], "reviewer_status": "unreviewed"})
        title = row.get("title", "").strip(); description = row.get("description", "").strip()
        normalized = normalize(description); pair = normalize(title + "\n" + description)
        template_value = template(description)
        descriptions[normalized] += 1; title_description[pair] += 1; templates[template_value] += 1
        duplicate_ref = {"record_id": item["record_id"], "text_ref": item["text_ref"]}
        duplicate_description_refs[normalized].append(duplicate_ref)
        if template_value:
            duplicate_template_refs[template_value].append(duplicate_ref)
        exact_rows[hashlib.sha256(json.dumps(row, sort_keys=True).encode()).hexdigest()] += 1
        language = language_bucket(description); languages[language] += 1
        reasons = []
        words = len(normalized.split())
        if len(description) < 20 or words < 3: quality["extremely_short"] += 1; reasons.append("extremely_short")
        if URL.fullmatch(description): quality["url_only"] += 1; reasons.append("url_only")
        if HTML.search(description): quality["contains_html_like_markup"] += 1; reasons.append("html_like")
        if "\ufffd" in description: quality["replacement_character"] += 1; reasons.append("replacement_character")
        if any(ord(char) < 32 and char not in "\r\n\t" for char in description):
            quality["unexpected_control_character"] += 1; reasons.append("control_character")
        if EMAIL.search(description): privacy["possible_email"] += 1; reasons.append("possible_email")
        if PHONE.search(description): privacy["possible_indian_phone"] += 1; reasons.append("possible_phone")
        if language != "latin_script_english_or_transliterated": reasons.append("language_script_review")
        if reasons and len(suspicious) < 1000:
            suspicious.append({"record_id": item["record_id"], "text_ref": item["text_ref"], "reasons": reasons})
        date = row.get("created_at", "")
        year_first = re.search(r"\b(20\d{2})[-/]([01]?\d)[-/]", date)
        day_first = re.search(r"\b\d{1,2}-([01]?\d)-(20\d{2})\b", date)
        month_first = re.search(r"\b([01]?\d)/([0-3]?\d)/(20\d{2})\b", date)
        if year_first and 1 <= int(year_first.group(2)) <= 12:
            year, month = year_first.group(1), int(year_first.group(2))
            date_formats["year_first"] += 1
        elif day_first and 1 <= int(day_first.group(1)) <= 12:
            year, month = day_first.group(2), int(day_first.group(1))
            date_formats["day-month-year_dash"] += 1
        elif month_first and 1 <= int(month_first.group(1)) <= 12:
            year, month = month_first.group(3), int(month_first.group(1))
            date_formats["month-day-year_slash"] += 1
            if int(month_first.group(2)) <= 12:
                date_formats["slash_calendar_order_ambiguous"] += 1
        else:
            year = month = None
        if year is not None:
            years[year] += 1; months[f"{year}-{month:02d}"] += 1
        else: quality["unparsed_date"] += 1
        lat, lon = row.get("latitude", "").strip(), row.get("longitude", "").strip()
        if not lat or not lon or lat.upper() == "NULL" or lon.upper() == "NULL":
            coordinate["missing_pair"] += 1
        else:
            try:
                lat_value, lon_value = float(lat), float(lon)
                coordinate["valid_global"] += -90 <= lat_value <= 90 and -180 <= lon_value <= 180
                coordinate["inside_broad_india_bbox"] += 6 <= lat_value <= 38 and 68 <= lon_value <= 98
            except ValueError: coordinate["unparseable"] += 1

    duplicate_stats = {
        "exact_row_groups": sum(count > 1 for count in exact_rows.values()),
        "exact_row_excess_records": sum(count - 1 for count in exact_rows.values() if count > 1),
        "normalized_description_groups": sum(count > 1 for count in descriptions.values()),
        "normalized_description_excess_records": sum(count - 1 for count in descriptions.values() if count > 1),
        "normalized_title_description_groups": sum(count > 1 for count in title_description.values()),
        "template_groups": sum(count > 1 for key, count in templates.items() if key),
        "template_excess_records": sum(count - 1 for key, count in templates.items() if key and count > 1),
    }
    accepted = {name: count for name, count in accepted_proposed.items() if count}
    positive = list(accepted.values())
    accepted_total = sum(positive)
    complete_missingness = {field: missing[field] for field in FIELDS}
    complete_quality = {key: quality[key] for key in ("extremely_short", "url_only",
        "contains_html_like_markup", "replacement_character", "unexpected_control_character", "unparsed_date")}
    complete_quality["empty_description_omissions_at_import"] = acquisition.get("omissions", {}).get("empty_description", 0)
    complete_languages = {key: languages[key] for key in ("bengali_script", "bengali_latin_mixed",
        "devanagari_script", "devanagari_latin_mixed", "latin_script_english_or_transliterated",
        "unknown_or_other_script")}
    complete_privacy = {key: privacy[key] for key in ("possible_email", "possible_indian_phone")}
    complete_coordinates = {key: coordinate[key] for key in ("missing_pair", "unparseable", "valid_global",
        "inside_broad_india_bbox")}
    report = {"status": "audit_not_training_approval", "source": acquisition["source_name"],
        "country": "IN", "dataset_version": acquisition["dataset_version"],
        "raw_sha256": acquisition["raw_sha256"], "raw_records": len(rows),
        "records_by_source": {acquisition["source_name"]: len(rows)},
        "manifest_records": len(manifest), "source_categories": dict(categories),
        "source_subcategories": dict(subcategories), "missingness": complete_missingness,
        "text_quality": complete_quality, "language_script_evidence": complete_languages,
        "privacy_pattern_counts": complete_privacy, "duplicates": duplicate_stats,
        "mapping_version": mapping["mapping_version"], "mapping_status_counts": dict(mapping_states),
        "proposed_class_counts_all_statuses": dict(proposed),
        "accepted_mapping_class_counts": accepted,
        "accepted_mapping_class_proportions": {name: count / accepted_total for name, count in accepted.items()},
        "accepted_mapping_class_max_min_ratio": max(positive) / min(positive) if positive else None,
        "date_year_counts": dict(years), "date_month_counts": dict(months),
        "date_format_counts": dict(date_formats),
        "ward_field_distinct_nonmissing": len([key for key in wards if key and key.upper() != "NULL"]),
        "coordinate_audit": complete_coordinates,
        "limitations": ["Script buckets do not prove language identity, especially Latin transliteration.",
            "Template normalization detects only simple variants; semantic near duplicates require review.",
            "Proposed mappings are source-label proposals, not per-record human labels.",
            "Privacy regex counts are screening signals and include false positives/negatives.",
            "Slash dates are treated as month/day/year; dates where both components are at most 12 remain calendar-order ambiguous.",
            "Bengaluru data cannot establish Kolkata, West Bengal, or all-India performance."],
        "training_approved": False}
    output.mkdir(parents=True)
    (output / "audit.json").write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8")
    selected = []
    for key in sorted(review_groups):
        selected.extend(sorted(review_groups[key], key=lambda row: hashlib.sha256(row["record_id"].encode()).hexdigest())[:sample_per_group])
    duplicate_review = []
    for kind, groups in (("normalized_description", duplicate_description_refs),
                         ("numeric_url_normalized_template", duplicate_template_refs)):
        for value, refs in groups.items():
            if len(refs) > 1:
                duplicate_review.append({"kind": kind, "fingerprint": hashlib.sha256(value.encode()).hexdigest(),
                                         "count": len(refs), "records": refs[:20]})
    duplicate_review.sort(key=lambda group: (-group["count"], group["kind"], group["fingerprint"]))
    duplicate_review = duplicate_review[:400]
    for name, values in (("mapping-review.json", selected), ("suspicious-review.json", suspicious),
                         ("duplicate-review.json", duplicate_review)):
        (output / name).write_text(json.dumps(values, ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path); parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--mapping", type=Path, default=DEFAULT_MAPPING); parser.add_argument("--sample-per-group", type=int, default=5)
    args = parser.parse_args(argv)
    try: report = audit(args.snapshot, args.output, args.mapping, args.sample_per_group)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc: parser.exit(1, f"Audit failed: {exc}\n")
    print(json.dumps({"raw_records": report["raw_records"], "mapping_status_counts": report["mapping_status_counts"],
                      "training_approved": False}, indent=2))


if __name__ == "__main__": main()
