"""Verify local data and produce a deterministic split proposal, never a training approval."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import platform
import unicodedata

from PIL import Image, ImageOps, __version__ as pillow_version

from .manifest import load_taxonomy, validate_manifest, _file_hash


ALGORITHM = "connected-components-sha256-70-15-15-v1"
# Provenance acceptance only; this is not label/rights/training approval.
SOURCE_COUNTRIES = {"opencity-icmyc-india": "IN"}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fingerprint(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def prepare(manifest: Path, data_root: Path, output: Path, *, seed: int = 42, paired: bool = True):
    """Import an Issue #5 manifest; keep raw files in place and write a new proposal directory.

    Split assignment uses no labels. All duplicate/event connections are transitive.
    Paired mode gives subsequent modality comparisons the same eligible examples.
    """
    if output.exists():
        raise ValueError("Output already exists; use a new version directory")
    root = data_root.resolve(strict=True)
    original_hash = _file_hash(manifest)
    validation = validate_manifest(manifest, data_root=root)
    if not validation.valid:
        raise ValueError("Invalid manifest: " + "; ".join(validation.errors))
    records = [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
    records.sort(key=lambda row: row["record_id"])
    if any(SOURCE_COUNTRIES.get(row["source_name"]) != "IN" for row in records):
        raise ValueError("Indian provenance required: unreviewed or foreign source cannot enter a split proposal")
    if any(row["split"] != "unassigned" for row in records):
        raise ValueError("Already assigned records cannot be resplit; preserve the frozen evaluation set")
    if len({row["dataset_version"] for row in records}) != 1:
        raise ValueError("One dataset version is required per preparation run")
    parents = list(range(len(records)))

    def find(index):
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    def union(left, right):
        left, right = find(left), find(right)
        parents[max(left, right)] = min(left, right)

    seen = {}
    duplicate_kinds = Counter()
    for index, row in enumerate(records):
        keys = [("event", row["group_id"])]
        for modality in ("text", "image"):
            if not row[f"{modality}_available"]:
                continue
            keys.append((modality + "_bytes", row[f"{modality}_sha256"]))
            path = (root / row[f"{modality}_ref"]).resolve(strict=True)
            if not path.is_relative_to(root):
                raise ValueError("File escapes data root")
            if modality == "text":
                if path.stat().st_size > 1_048_576:
                    raise ValueError("Text exceeds 1 MiB")
                text = path.read_text(encoding="utf-8-sig")
                text = " ".join(unicodedata.normalize("NFKC", text).casefold().split())
                if not text:
                    raise ValueError(f"Empty text for {row['record_id']}")
                keys.append(("normalized_text", fingerprint(text)))
            else:
                with Image.open(path) as image:
                    if image.format not in {"JPEG", "PNG"} or getattr(image, "n_frames", 1) != 1:
                        raise ValueError("Only single-frame JPEG/PNG research images are supported")
                    if image.width * image.height > 25_000_000:
                        raise ValueError("Image exceeds 25 million pixels")
                    pixels = ImageOps.exif_transpose(image).convert("RGB")
                    digest = hashlib.sha256(str(pixels.size).encode() + pixels.tobytes()).hexdigest()
                keys.append(("decoded_pixels", digest))
        for key in keys:
            if key in seen:
                union(index, seen[key])
                duplicate_kinds[key[0]] += 1
            else:
                seen[key] = index

    groups = defaultdict(list)
    for index, row in enumerate(records):
        groups[find(index)].append(row)
    assignments, conflicts = [], []
    support = {split: Counter() for split in ("train", "validation", "test")}
    component_support = {split: Counter() for split in support}
    sources = {split: Counter() for split in support}
    source_categories = defaultdict(Counter)
    omitted = Counter()
    for members in groups.values():
        identities = sorted(row["record_id"] for row in members)
        group_id = "component-" + fingerprint(canonical(identities))
        # A conflict in a linked event blocks the whole component for review.
        labels = {row["category_label"] for row in members if row["annotation_status"] == "annotated"}
        disputed = len(labels) > 1 or any(row["annotation_status"] == "needs_adjudication" for row in members)
        if disputed:
            conflicts.append(group_id)
        bucket = int(fingerprint(f"{seed}:{group_id}")[:16], 16) / 2**64
        target = "train" if bucket < .70 else "validation" if bucket < .85 else "test"
        assigned_labels = set()
        for row in members:
            reason = None
            if disputed:
                reason = "component_requires_adjudication"
            elif row["annotation_status"] != "annotated":
                reason = row["annotation_status"]
            elif paired and not (row["text_available"] and row["image_available"]):
                reason = "missing_paired_modality"
            row["group_id"] = group_id
            row["split"] = "unassigned" if reason else target
            if reason:
                omitted[reason] += 1
            else:
                support[target][row["category_label"]] += 1
                sources[target][row["source_name"]] += 1
                source_categories[row["source_name"]][row["category_label"]] += 1
                assigned_labels.add(row["category_label"])
            assignments.append(row)
        component_support[target].update(assigned_labels)
    assignments.sort(key=lambda row: row["record_id"])
    _, categories = load_taxonomy()
    missing = {split: sorted(categories - counts.keys()) for split, counts in support.items()}
    # Recheck immutable input and file hashes after reading contents, before publishing.
    if _file_hash(manifest) != original_hash or not validate_manifest(manifest, data_root=root).valid:
        raise ValueError("Inputs changed during preparation")
    payload = "".join(canonical(row) + "\n" for row in assignments)
    report = {
        "algorithm": ALGORITHM, "seed": seed, "paired": paired,
        "python_version": platform.python_version(), "pillow_version": pillow_version,
        "preparation_code_sha256": _file_hash(Path(__file__)),
        "input_manifest_sha256": original_hash,
        "output_manifest_sha256": fingerprint(payload),
        "taxonomy_sha256": _file_hash(Path(__file__).parents[1] / "taxonomy/category_v1.json"),
        "records": len(records), "components": len(groups),
        "duplicate_connections": dict(duplicate_kinds), "conflicting_components": conflicts,
        "unassigned_reasons": dict(omitted), "class_support": support, "source_support": sources,
        "independent_component_support": component_support,
        "source_category_support": dict(source_categories),
        "missing_categories": missing,
        "training_approved": False,
        "review_required": ["source rights and mapping", "privacy and annotation quality",
                            "near duplicates and related events", "class/source balance and sample adequacy"],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.mkdir()
    incomplete = output / "INCOMPLETE"
    incomplete.write_text("Preparation has not completed; do not use this directory.\n", encoding="utf-8")
    candidate = output / "manifest.jsonl"
    candidate.write_text(payload, encoding="utf-8", newline="\n")
    final_check = validate_manifest(candidate, data_root=root)
    if not final_check.valid:
        raise ValueError("Prepared manifest invalid: " + "; ".join(final_check.errors))
    (output / "report.json").write_text(canonical(report) + "\n", encoding="utf-8")
    incomplete.unlink()
    (output / "COMPLETE").write_text("Validated preparation proposal.\n", encoding="utf-8")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--allow-unpaired", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = prepare(args.manifest, args.data_root, args.output, seed=args.seed, paired=not args.allow_unpaired)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Preparation failed: {exc}\n")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
