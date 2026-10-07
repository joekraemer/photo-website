"""Storage targets: a local directory or an S3-compatible bucket (Backblaze B2)."""

from __future__ import annotations

from pathlib import Path

PHOTO_CACHE = "public, max-age=31536000, immutable"
MANIFEST_CACHE = "public, max-age=300"


class LocalTarget:
    def __init__(self, root: Path):
        self.root = Path(root)

    def describe(self) -> str:
        return f"local:{self.root}"

    def list_keys(self, prefix: str) -> set[str]:
        base = self.root / prefix
        if not base.exists():
            return set()
        return {p.relative_to(self.root).as_posix() for p in base.rglob("*") if p.is_file()}

    def read(self, key: str) -> bytes | None:
        path = self.root / key
        return path.read_bytes() if path.is_file() else None

    def put(self, key: str, data: bytes, content_type: str, cache_control: str) -> None:
        path = self.root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_bytes(data)
        tmp.replace(path)

    def delete(self, key: str) -> None:
        path = self.root / key
        if path.is_file():
            path.unlink()
        parent = path.parent
        while parent != self.root and parent.is_dir() and not any(parent.iterdir()):
            parent.rmdir()
            parent = parent.parent


class S3Target:
    def __init__(self, bucket: str, client):
        self.bucket = bucket
        self.client = client

    @classmethod
    def from_config(cls, cfg) -> "S3Target":
        import boto3
        from botocore.config import Config as BotoConfig

        client = boto3.client(
            "s3",
            endpoint_url=cfg.s3_endpoint_url,
            aws_access_key_id=cfg.s3_key_id,
            aws_secret_access_key=cfg.s3_app_key,
            config=BotoConfig(
                retries={"max_attempts": 5, "mode": "standard"},
                # boto3 >= 1.36 sends CRC32 checksum headers by default, which some
                # S3-compatible providers (incl. B2 at times) reject.
                request_checksum_calculation="when_required",
                response_checksum_validation="when_required",
            ),
        )
        return cls(cfg.s3_bucket, client)

    def describe(self) -> str:
        return f"s3://{self.bucket}"

    def list_keys(self, prefix: str) -> set[str]:
        keys: set[str] = set()
        paginator = self.client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
            for obj in page.get("Contents", []) or []:
                keys.add(obj["Key"])
        return keys

    def read(self, key: str) -> bytes | None:
        try:
            return self.client.get_object(Bucket=self.bucket, Key=key)["Body"].read()
        except self.client.exceptions.NoSuchKey:
            return None
        except Exception as exc:  # botocore ClientError for 404 on some providers
            code = getattr(exc, "response", {}).get("Error", {}).get("Code")
            if code in ("404", "NoSuchKey", "NotFound"):
                return None
            raise

    def put(self, key: str, data: bytes, content_type: str, cache_control: str) -> None:
        self.client.put_object(
            Bucket=self.bucket, Key=key, Body=data,
            ContentType=content_type, CacheControl=cache_control,
        )

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key)


def make_target(cfg):
    if cfg.target == "local":
        return LocalTarget(cfg.local_target_dir)
    return S3Target.from_config(cfg)
