"""Read-only evidence consistency audit for operators and recovery checks."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from civicai.config import database_url
from civicai.database import build_engine
from civicai.models import Complaint
from civicai.uploads import REFERENCE_PREFIX, upload_directory


@dataclass(frozen=True)
class MediaAudit:
    database_references: int
    stored_files: int
    missing_files: tuple[str, ...]
    orphan_files: tuple[str, ...]
    invalid_references: tuple[str, ...]

    @property
    def consistent(self) -> bool:
        return not (self.missing_files or self.orphan_files or self.invalid_references)


def audit_inventory(directory: Path, references: list[str]) -> MediaAudit:
    expected: set[str] = set()
    invalid: list[str] = []
    for reference in references:
        if reference.startswith(REFERENCE_PREFIX):
            filename = reference.removeprefix(REFERENCE_PREFIX)
            if filename and Path(filename).name == filename:
                expected.add(filename)
                continue
        invalid.append(reference)

    stored = {
        path.name
        for path in directory.iterdir()
        if path.is_file() and not path.is_symlink()
    } if directory.is_dir() else set()
    return MediaAudit(
        database_references=len(references),
        stored_files=len(stored),
        missing_files=tuple(sorted(expected - stored)),
        orphan_files=tuple(sorted(stored - expected)),
        invalid_references=tuple(sorted(invalid)),
    )


def main() -> int:
    engine = build_engine(database_url())
    try:
        with Session(engine) as session:
            references = list(
                session.scalars(select(Complaint.image_ref).where(Complaint.image_ref.is_not(None)))
            )
        report = audit_inventory(upload_directory(), references)
        payload = asdict(report) | {"consistent": report.consistent}
        print(json.dumps(payload, indent=2))
        return 0 if report.consistent else 2
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
