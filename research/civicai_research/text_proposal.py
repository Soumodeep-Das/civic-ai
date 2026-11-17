"""Prepare a deterministic, unapproved OpenCity text-curation proposal; never train."""
from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path
import re

from .audit import DEFAULT_MAPPING, EMAIL, PHONE, HTML, URL, language_bucket, normalize, template
from .manifest import DEFAULT_TAXONOMY, _file_hash, load_taxonomy, validate_manifest
from .review import _load_snapshot

VERSION = "icmyc-text-proposal-v1"
SPACED_PHONE = re.compile(r"(?<!\w)(?:\+?91[ .-]?)?[6-9](?:[ -]?\d){9}(?!\w)")
WEB = re.compile(r"https?://\S+|www\.\S+", re.I)


def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def screen(text):
    """Mask overlapping contact/URL candidates; preserve offsets into original text.

    This is a review proposal, not anonymization. Names/addresses are not resolved.
    """
    spans = sorted((m.start(), m.end(), kind) for kind, pattern in
                   (("email", EMAIL), ("phone", PHONE), ("phone", SPACED_PHONE), ("url", WEB))
                   for m in pattern.finditer(text))
    merged = []
    for start, end, kind in spans:
        if merged and start < merged[-1]["end"]:
            merged[-1]["end"] = max(merged[-1]["end"], end)
            merged[-1]["kinds"] = sorted(set(merged[-1]["kinds"]) | {kind})
        else:
            merged.append({"start": start, "end": end, "kinds": [kind]})
    derived = text
    for span in reversed(merged):
        derived = derived[:span["start"]] + "[REDACTED]" + derived[span["end"]:]
    return derived, merged


def propose(snapshot, output, mapping_path=DEFAULT_MAPPING):
    if output.resolve().is_relative_to(snapshot.resolve()):
        raise ValueError("Output must be outside the immutable snapshot")
    if output.exists():
        raise ValueError("Output exists; select a new version directory")
    acquisition, manifest, source_labels = _load_snapshot(snapshot)
    check = validate_manifest(snapshot / "manifest.jsonl", data_root=snapshot)
    if not check.valid:
        raise ValueError("Referenced source files failed integrity validation")
    if any(r["annotation_status"] != "pending" or r["category_label"] is not None
           or r["split"] != "unassigned" or r["image_available"] for r in manifest):
        raise ValueError("Proposal requires untouched pending unassigned text-only records")
    version, categories = load_taxonomy()
    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    states = {"accepted", "ambiguous", "needs_review", "rejected"}
    if (mapping.get("status") != "proposed" or mapping.get("taxonomy_version") != version
            or mapping.get("source_name") != acquisition["source_name"]
            or mapping.get("default_status") not in states):
        raise ValueError("Invalid mapping proposal")
    rules = {}
    for rule in mapping["rules"]:
        key = rule["source_subcategory"].strip()
        label = rule.get("proposed_category")
        state = rule.get("status")
        if (not key or key in rules or state not in states or
                (label is not None and label not in categories) or
                (state == "accepted" and label is None) or (state == "rejected" and label is not None)):
            raise ValueError("Invalid mapping rule")
        rules[key] = rule
    # StringIO preserves embedded newlines; splitlines() would change CSV field contents.
    raw_rows = list(csv.DictReader(io.StringIO((snapshot / "source.csv").read_bytes().decode(
        acquisition["encoding"]), newline="")))
    if len(raw_rows) != acquisition["records_returned"]:
        raise ValueError("Raw row count differs")
    original = {}
    for number, row in enumerate(raw_rows, 1):
        if None in row or any(row.get(k) is None for k in
                              ("description", "category_title", "sub_category_title", "created_at")):
            raise ValueError("Malformed raw CSV")
        if row["description"].strip():
            original[f"{acquisition['raw_sha256'][:12]}-row-{number}"] = (number, row)
    if set(original) != set(source_labels) or len(manifest) != len(original):
        raise ValueError("Raw and source-label identities differ")
    records, texts, fingerprints = [], {}, []
    for item in sorted(manifest, key=lambda r: r["record_id"]):
        identity = item["source_record_id"]
        if identity not in original or item["record_id"] != "icmyc-" + identity:
            raise ValueError("Source identity mismatch")
        number, row = original[identity]
        stored = source_labels[identity]
        if (stored["original_csv_row"] != number or stored["source_category"] != row["category_title"]
                or stored["source_subcategory"] != row["sub_category_title"]
                or stored["created_at"] != row["created_at"]):
            raise ValueError("Source labels differ from immutable CSV")
        raw_text = row["description"].strip()
        if digest(raw_text) != item["text_sha256"]:
            raise ValueError("Manifest text differs from raw CSV")
        derived, spans = screen(raw_text)
        rule = rules.get(row["sub_category_title"].strip(),
                         {"status": mapping["default_status"], "proposed_category": None})
        flags = []
        if len(raw_text) < 20 or len(normalize(raw_text).split()) < 3:
            flags.append("extremely_short")
        if URL.fullmatch(raw_text): flags.append("url_only")
        if HTML.search(raw_text): flags.append("html_like")
        if "\ufffd" in raw_text: flags.append("replacement_character")
        if any(ord(c) < 32 and c not in "\r\n\t" for c in raw_text): flags.append("control_character")
        script = language_bucket(raw_text)
        if script != "latin_script_english_or_transliterated": flags.append("script_review")
        record = {"record_id": item["record_id"], "source_record_id": identity,
                  "source_category": row["category_title"], "source_subcategory": row["sub_category_title"],
                  "source_text_ref": item["text_ref"], "source_text_sha256": item["text_sha256"],
                  "derived_text_ref": f"texts/{item['record_id']}.txt", "derived_text_sha256": digest(derived),
                  "redaction_proposals": spans, "privacy_status": "pending_including_names_addresses",
                  "quality_flags": flags, "script_bucket_not_language": script,
                  "mapping_status": rule["status"], "proposed_category": rule.get("proposed_category"),
                  "proposal_basis": "deterministic_source_mapping_not_human_annotation",
                  "category_label": None, "annotation_status": "pending", "split": "unassigned"}
        records.append(record); texts[item["record_id"]] = derived
        fingerprints.append([(kind, digest(value)) for kind, value in (
            ("raw_normalized", normalize(raw_text)), ("derived_normalized", normalize(derived)),
            ("numeric_url_template", template(raw_text))) if value])
    # Conservative transitive containment groups, NOT confirmed incident identities.
    parents = list(range(len(records)))
    def find(i):
        while parents[i] != i:
            parents[i] = parents[parents[i]]; i = parents[i]
        return i
    seen = {}; links = Counter()
    for i, keys in enumerate(fingerprints):
        for key in keys:
            if key in seen:
                a, b = find(i), find(seen[key]); parents[max(a,b)] = min(a,b)
                links[key[0]] += 1
            else: seen[key] = i
    groups = defaultdict(list)
    for i, row in enumerate(records): groups[find(i)].append(row)
    group_rows = []
    for members in groups.values():
        ids = sorted(r["record_id"] for r in members)
        gid = "proposal-group-" + digest("\n".join(ids))
        labels = sorted({r["proposed_category"] for r in members if r["proposed_category"]})
        mixed = len(labels) > 1
        unresolved = any(r["mapping_status"] != "accepted" for r in members)
        group_rows.append({"group_id": gid, "members": ids, "size": len(ids),
                           "proposed_categories": labels, "category_conflict": mixed,
                           "unresolved_mapping_member": unresolved, "event_identity_verified": False})
        for r in members:
            reasons = list(r["quality_flags"])
            if r["mapping_status"] != "accepted": reasons.append("mapping_" + r["mapping_status"])
            if r["redaction_proposals"]: reasons.append("privacy_pattern_review")
            if mixed: reasons.append("group_category_conflict")
            if unresolved: reasons.append("group_unresolved_mapping")
            r.update(proposed_group_id=gid, review_reasons=sorted(set(reasons)),
                     review_route="targeted_review" if reasons else "candidate_review")
    supports = {}
    for category in sorted(categories):
        mapped = [r for r in records if r["proposed_category"] == category and r["mapping_status"] == "accepted"]
        candidates = [r for r in mapped if r["review_route"] == "candidate_review"]
        supports[category] = {"source_mapping_candidates": len(mapped), "screened_candidate_records": len(candidates),
                              "proposed_groups": len({r["proposed_group_id"] for r in candidates}),
                              "approved_records": 0}
    provenance = {"algorithm": VERSION, "raw_sha256": acquisition["raw_sha256"],
                  "mapping_sha256": _file_hash(mapping_path), "taxonomy_sha256": _file_hash(DEFAULT_TAXONOMY),
                  "input_manifest_sha256": _file_hash(snapshot / "manifest.jsonl"),
                  "source_labels_sha256": _file_hash(snapshot / "source-labels.json"),
                  "code_sha256": {p.name: _file_hash(p) for p in
                                  (Path(__file__), Path(__file__).with_name("audit.py"),
                                   Path(__file__).with_name("review.py"), Path(__file__).with_name("manifest.py"))}}
    report = {"status": "automated_proposal_not_curated_release", "training_approved": False,
              "records": len(records), "provenance": provenance, "class_support": supports,
              "review_route_counts": dict(Counter(r["review_route"] for r in records)),
              "mapping_status_counts": dict(Counter(r["mapping_status"] for r in records)),
              "review_reason_counts": dict(Counter(f for r in records for f in r["review_reasons"])),
              "script_counts_not_languages": dict(Counter(r["script_bucket_not_language"] for r in records)),
              "privacy_flagged_records": sum(bool(r["redaction_proposals"]) for r in records),
              "group_count": len(group_rows), "multi_record_groups": sum(g["size"] > 1 for g in group_rows),
              "largest_group": max(g["size"] for g in group_rows),
              "category_conflict_groups": sum(g["category_conflict"] for g in group_rows),
              "duplicate_link_counts": dict(links),
              "blockers": ["taxonomy_and_mapping_review", "privacy_including_names_addresses",
                           "independent_reference_labels", "event_and_semantic_duplicate_review",
                           "license_and_derivative_terms", "class_language_city_support_and_split_protocol",
                           "explicit_reviewed_release_approval"],
              "limitations": ["Pattern absence does not establish anonymization.",
                              "Template groups can overmerge unrelated incidents and miss semantic duplicates.",
                              "Script counts do not establish English/Hindi/Bengali language quality.",
                              "Candidate groups are not proven independent scenes; no split assigned."]}
    output.mkdir(parents=True)
    (output / "INCOMPLETE").write_text("Proposal incomplete; do not train.\n", encoding="utf-8")
    (output / "texts").mkdir()
    for r in records:
        (output / r["derived_text_ref"]).write_text(texts[r["record_id"]], encoding="utf-8", newline="\n")
    with (output / "proposals.jsonl").open("w", encoding="utf-8", newline="\n") as f:
        for r in records: f.write(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n")
    write_json(output / "groups.json", sorted(group_rows, key=lambda g: g["group_id"]))
    mapping_groups = defaultdict(list)
    for r in records:
        mapping_groups[(r["source_category"], r["source_subcategory"])].append(r)
    write_json(output / "mapping-groups.json", [
        {"source_category": key[0], "source_subcategory": key[1], "records": len(members),
         "mapping_status": members[0]["mapping_status"], "proposed_category": members[0]["proposed_category"],
         "record_ids": [r["record_id"] for r in members], "review_status": "pending"}
        for key, members in sorted(mapping_groups.items())])
    write_json(output / "readiness.json", report)
    for r in records:
        if _file_hash(output / r["derived_text_ref"]) != r["derived_text_sha256"]:
            raise ValueError("Derived file hash mismatch")
    write_json(output / "artifacts.json", {p.relative_to(output).as_posix(): _file_hash(p)
               for p in sorted(output.rglob("*")) if p.is_file() and p.name != "INCOMPLETE"})
    (output / "COMPLETE").write_text("Complete automated proposal only; training_approved=false.\n", encoding="utf-8")
    (output / "INCOMPLETE").unlink()
    return report


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try: report = propose(args.snapshot, args.output)
    except (OSError, ValueError, KeyError) as exc: parser.exit(1, f"Proposal failed: {type(exc).__name__}; inspect inputs locally.\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__": main()
