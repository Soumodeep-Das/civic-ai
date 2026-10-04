"""Private evidence storage adapters. Credentials and objects never reach browsers directly."""
from __future__ import annotations

import re
import os
from pathlib import Path
from typing import Protocol

from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
import boto3

from civicai.config import EvidenceSettings

OBJECT_KEY = re.compile(r"^[0-9a-f]{32}\.(?:jpg|png)$")


class EvidenceStorageError(OSError):
    pass


class EvidenceStorage(Protocol):
    def put(self, key: str, content: bytes, content_type: str) -> None: ...
    def get(self, key: str) -> tuple[bytes, str]: ...
    def delete(self, key: str) -> None: ...
    def ready(self) -> bool: ...


def validate_key(key: str) -> str:
    if not OBJECT_KEY.fullmatch(key):
        raise FileNotFoundError(key)
    return key


class LocalEvidenceStorage:
    def __init__(self, directory: Path):
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)

    def put(self, key: str, content: bytes, content_type: str) -> None:
        path = self.directory / validate_key(key)
        with path.open("xb") as target:
            target.write(content)

    def get(self, key: str) -> tuple[bytes, str]:
        path = self.directory / validate_key(key)
        if not path.is_file() or path.is_symlink():
            raise FileNotFoundError(key)
        return path.read_bytes(), "image/jpeg" if key.endswith(".jpg") else "image/png"

    def delete(self, key: str) -> None:
        (self.directory / validate_key(key)).unlink(missing_ok=True)

    def ready(self) -> bool:
        return self.directory.is_dir() and os.access(self.directory, os.R_OK | os.W_OK)


class S3EvidenceStorage:
    def __init__(self, settings: EvidenceSettings):
        self.bucket = settings.s3_bucket
        self.client = boto3.client(
            "s3", endpoint_url=settings.s3_endpoint_url, region_name=settings.s3_region,
            aws_access_key_id=settings.s3_access_key_id,
            aws_secret_access_key=settings.s3_secret_access_key,
            config=Config(connect_timeout=5, read_timeout=10, retries={"max_attempts": 2}, s3={"addressing_style": "path"}),
        )

    def put(self, key: str, content: bytes, content_type: str) -> None:
        try:
            self.client.put_object(Bucket=self.bucket, Key=validate_key(key), Body=content, ContentType=content_type)
        except (BotoCoreError, ClientError) as exc:
            raise EvidenceStorageError("Evidence storage write failed") from exc

    def get(self, key: str) -> tuple[bytes, str]:
        try:
            result = self.client.get_object(Bucket=self.bucket, Key=validate_key(key))
            return result["Body"].read(), result.get("ContentType") or ("image/jpeg" if key.endswith(".jpg") else "image/png")
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in {"NoSuchKey", "404", "NotFound"}:
                raise FileNotFoundError(key) from exc
            raise EvidenceStorageError("Evidence storage read failed") from exc
        except BotoCoreError as exc:
            raise EvidenceStorageError("Evidence storage read failed") from exc

    def delete(self, key: str) -> None:
        try:
            self.client.delete_object(Bucket=self.bucket, Key=validate_key(key))
        except (BotoCoreError, ClientError) as exc:
            raise EvidenceStorageError("Evidence storage delete failed") from exc

    def ready(self) -> bool:
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except (BotoCoreError, ClientError) as exc:
            raise EvidenceStorageError("Evidence storage readiness failed") from exc
        return True


def build_evidence_storage(settings: EvidenceSettings) -> EvidenceStorage:
    return LocalEvidenceStorage(settings.local_directory) if settings.backend == "local" else S3EvidenceStorage(settings)
