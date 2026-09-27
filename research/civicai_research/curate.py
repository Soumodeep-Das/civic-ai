"""Stage-B gate helpers: deterministic redaction and readiness checks, without model training."""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re

from .audit import EMAIL, PHONE
from .manifest import _file_hash
from .review import _schema


def redact_text(text: str, redaction_types: set[str], spans: str = "") -> tuple[str, list[dict[str, object]]]:
    """Return a derived redaction; never changes the caller's raw source string."""
    replacements = []
    if "email" in redaction_types:
        replacements.extend((match.start(), match.end(), "[EMAIL]") for match in EMAIL.finditer(text))
    if "phone" in redaction_types:
        replacements.extend((match.start(), match.end(), "[PHONE]") for match in PHONE.finditer(text))
    span_kinds = set()
    for value in filter(None, spans.split("|")):
        match = re.fullmatch(r"(\d+):(\d+):(name|address|identifier|other)", value)
        if not match: raise ValueError("Redaction spans must use start:end:type")
        start, end, kind = int(match.group(1)), int(match.group(2)), match.group(3)
        span_kinds.add(kind)
        if start < 0 or end <= start or end > len(text): raise ValueError("Redaction span is outside text")
        replacements.append((start, end, f"[{kind.upper()}]"))
    complex_types = redaction_types - {"phone", "email"}
    if complex_types != span_kinds:
        raise ValueError("Every non-pattern redaction type requires matching explicit spans")
    replacements.sort()
    if any(left[1] > right[0] for left, right in zip(replacements, replacements[1:])):
        raise ValueError("Redaction spans overlap")
    value = text
    applied = []
    for start, end, replacement in reversed(replacements):
        value = value[:start] + replacement + value[end:]
        applied.append({"start": start, "end": end, "replacement": replacement})
    applied.reverse()
    return value, applied


def assess_readiness(package_path: Path, decisions_path: Path):
    package = json.loads(package_path.read_text(encoding="utf-8"))
    decisions = json.loads(decisions_path.read_text(encoding="utf-8")); _schema()
    if decisions.get("dataset_version") != package.get("dataset_version"):
        raise ValueError("Decision dataset version differs from package")
    if decisions.get("package_sha256") != _file_hash(package_path):
        raise ValueError("Decisions were produced from a different review package")
    resolved = {(row["review_type"], row["item_id"]): row for row in decisions["resolved"]}
    unresolved = Counter()
    for review_type, expected in package["counts"].items():
        available = sum(key[0] == review_type for key in resolved)
        unresolved[review_type] = expected - available
    conflict_count = len(decisions.get("conflicts", []))
    blocking_states = {
        "taxonomy": {"propose_revision", "remove", "needs_discussion"},
        "mapping": {"ambiguous", "record_level_review", "propose_revision"},
        "privacy": {"additional_review"},
        "record": {"needs_adjudication", "defer"},
        "duplicate": {"needs_adjudication"},
        "license": {"needs_review", "rejected"},
    }
    blocking_decisions = sum(row["payload"]["decision"] in blocking_states.get(row["review_type"], set())
                             for row in decisions["resolved"])
    approval = [row for row in decisions["resolved"] if row["review_type"] == "dataset_approval"]
    explicit_approval = len(approval) == 1 and approval[0]["payload"]["decision"] == "approve_for_text_baseline"
    ready = not any(unresolved.values()) and conflict_count == 0 and blocking_decisions == 0 and explicit_approval
    return {"dataset_version": package["dataset_version"], "unresolved_by_review_type": dict(unresolved),
        "conflicts": conflict_count, "blocking_review_decisions": blocking_decisions,
        "explicit_dataset_approval": explicit_approval, "training_approved": ready}


def write_readiness_report(package_path: Path, decisions_path: Path, output: Path):
    if output.exists():
        raise ValueError("Readiness output exists; use a new version directory")
    report = assess_readiness(package_path, decisions_path)
    output.mkdir(parents=True)
    (output / "readiness.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    (output / "STAGE_B_REQUIRED").write_text(
        "This is a gate report, not a curated dataset or training approval.\n", encoding="utf-8"
    )
    return report


def main(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--decisions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        report = write_readiness_report(args.package, args.decisions, args.output)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        parser.exit(1, f"Curation gate failed: {exc}\n")
    print(json.dumps(report, indent=2)); return 0


if __name__ == "__main__": raise SystemExit(main())
