"""Acquire the Indian IChangeMyCity text log for local curation; never infer gold labels."""
import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path

import httpx

from .manifest import validate_manifest

CATALOGUE = "https://data.opencity.in/dataset/i-change-my-city-data"
METADATA = "https://data.opencity.in/api/3/action/package_show?id=i-change-my-city-data"
RESOURCE_ID = "a60abf5c-3a15-4967-af32-c3074248580f"
SOURCE = "opencity-icmyc-india"


def sha(content):
    return hashlib.sha256(content).hexdigest()


def fetch(client, url):
    if not url.startswith("https://data.opencity.in/"):
        raise ValueError("Unexpected source host")
    with client.stream("GET", url) as response:
        response.raise_for_status()
        chunks, total = [], 0
        for chunk in response.iter_bytes():
            total += len(chunk)
            if total > 20 * 1024 * 1024:
                raise ValueError("Response exceeds 20 MiB limit")
            chunks.append(chunk)
    return b"".join(chunks)


def ingest(raw, output, metadata):
    if output.exists():
        raise ValueError("Output exists; preserve snapshot and select a new version directory")
    try:
        text, encoding = raw.decode("utf-8-sig"), "utf-8-sig"
    except UnicodeDecodeError:
        # The published CSV contains Windows smart-quote bytes. Never replace/drop bytes.
        text, encoding = raw.decode("cp1252"), "cp1252"
    reader = csv.DictReader(io.StringIO(text, newline=""))
    required = {"title", "description", "category_title", "sub_category_title", "created_at"}
    if not reader.fieldnames or not required <= set(reader.fieldnames):
        raise ValueError("Source schema changed")
    digest = sha(raw)
    version = "icmyc-" + digest[:12]
    categories, subcategories, omissions = Counter(), Counter(), Counter()
    rows, source_rows, texts = [], [], {}
    total = 0
    for number, record in enumerate(reader, 1):
        total += 1
        if None in record or any(record[key] is None for key in required):
            raise ValueError(f"Malformed CSV row {number}")
        description = record["description"].strip()
        if not description:
            omissions["empty_description"] += 1
            continue
        content = description.encode("utf-8")
        if len(content) > 1_048_576:
            raise ValueError("Description exceeds limit")
        identity = f"{digest[:12]}-row-{number}"
        reference = f"texts/{identity}.txt"
        texts[reference] = content
        categories[record["category_title"]] += 1
        subcategories[record["sub_category_title"]] += 1
        source_rows.append(dict(source_record_id=identity, original_csv_row=number,
            source_category=record["category_title"], source_subcategory=record["sub_category_title"],
            created_at=record["created_at"]))
        rows.append(dict(record_id=f"icmyc-{identity}", source_name=SOURCE,
            source_record_id=identity, source_terms_ref=CATALOGUE,
            consent_or_basis="Publisher states CC BY-SA; local Indian data curation, not training approval",
            dataset_version=version, taxonomy_version="civicai-category-v1",
            annotation_status="pending", category_label=None, annotator_id=None,
            annotation_notes=None, exclusion_reason=None, group_id=f"icmyc-{identity}",
            split="unassigned", text_available=True, text_ref=reference, text_sha256=sha(content),
            image_available=False, image_ref=None, image_sha256=None))
    if not rows:
        raise ValueError("No descriptions available")
    report = dict(dataset_version=version, country="IN", source_name=SOURCE,
        catalogue=CATALOGUE, resource_id=RESOURCE_ID, raw_sha256=digest,
        metadata_sha256=sha(metadata), encoding=encoding,
        retrieved_at=datetime.now(timezone.utc).isoformat(), records_returned=total,
        records_ingested=len(rows), omissions=dict(omissions), source_categories=dict(categories),
        source_subcategories=dict(subcategories), images=0, training_approved=False,
        limitations=["Bengaluru source is not representative of all India",
                     "Language, privacy, duplicates and label mapping need review",
                     "No image pairing available; no human labels assigned",
                     "Row identities are snapshot-specific; compare hashes across versions"])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.mkdir()
    incomplete = output / "INCOMPLETE"
    incomplete.write_text("Acquisition has not completed; do not use this directory.\n", encoding="utf-8")
    try:
        (output / "texts").mkdir()
        (output / "source.csv").write_bytes(raw)
        (output / "publisher-metadata.json").write_bytes(metadata)
        for reference, content in texts.items():
            (output / reference).write_bytes(content)
        for name, value in [("acquisition.json", report), ("source-labels.json", source_rows)]:
            (output / name).write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8")
        manifest = output / "manifest.jsonl"
        manifest.write_text("".join(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8", newline="\n")
        checked = validate_manifest(manifest, data_root=output)
        if not checked.valid:
            raise ValueError("Imported manifest invalid: " + "; ".join(checked.errors[:10]))
        incomplete.unlink()
        (output / "COMPLETE").write_text("Validated snapshot. See acquisition.json for provenance.\n", encoding="utf-8")
    except Exception:
        # Preserve partial evidence with INCOMPLETE marker for diagnosis; never treat it as a snapshot.
        raise
    return report


def acquire(output, client=None):
    if output.exists():
        raise ValueError("Output exists")
    if client is None:
        with httpx.Client(timeout=60, follow_redirects=False) as session:
            return acquire(output, session)
    metadata = fetch(client, METADATA)
    payload = json.loads(metadata)
    source = payload["result"]
    if source.get("license_id") != "cc-by-sa":
        raise ValueError("Source license changed; review required")
    resources = [r for r in source["resources"] if r.get("id") == RESOURCE_ID]
    if len(resources) != 1:
        raise ValueError("Source resource changed")
    raw = fetch(client, resources[0]["url"])
    return ingest(raw, output, metadata)


def verify_existing(output: Path):
    """Resume the integrity gate for an interrupted, already-downloaded snapshot."""
    if not output.is_dir():
        raise ValueError("Snapshot directory does not exist")
    if not (output / "INCOMPLETE").is_file() or (output / "COMPLETE").exists():
        raise ValueError("Snapshot is not an incomplete acquisition")
    acquisition = json.loads((output / "acquisition.json").read_text(encoding="utf-8"))
    if acquisition.get("country") != "IN" or acquisition.get("source_name") != SOURCE:
        raise ValueError("Reviewed Indian provenance is required")
    if sha((output / "source.csv").read_bytes()) != acquisition.get("raw_sha256"):
        raise ValueError("Raw source checksum mismatch")
    if sha((output / "publisher-metadata.json").read_bytes()) != acquisition.get("metadata_sha256"):
        raise ValueError("Publisher metadata checksum mismatch")
    checked = validate_manifest(output / "manifest.jsonl", data_root=output)
    if not checked.valid:
        raise ValueError("Imported manifest invalid: " + "; ".join(checked.errors[:10]))
    if checked.records != acquisition.get("records_ingested"):
        raise ValueError("Manifest/acquisition record counts differ")
    (output / "INCOMPLETE").unlink()
    (output / "COMPLETE").write_text(
        "Validated snapshot. See acquisition.json for provenance.\n", encoding="utf-8"
    )
    return {"records": checked.records, "warnings": len(checked.warnings), "valid": True}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--verify-existing", action="store_true",
                        help="Finish the integrity gate for an INCOMPLETE local snapshot without downloading")
    args = parser.parse_args(argv)
    try:
        report = verify_existing(args.output) if args.verify_existing else acquire(args.output)
    except (ValueError, OSError, KeyError, httpx.HTTPError) as exc:
        parser.exit(1, f"Acquisition failed: {exc}\n")
    print(json.dumps(report, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
