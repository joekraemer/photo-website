"""Configuration from environment variables (optionally a gitignored .env file)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_WATERMARK = "@jak_creative_"
DEFAULT_OPACITY = 0.4


class ConfigError(ValueError):
    pass


# Path settings that, when they come from an env file, are resolved relative to
# that file's folder rather than the current directory.
PATH_KEYS = ("PHOTO_SOURCE_ROOT", "LOCAL_TARGET_DIR")


def load_env_file(path: Path, environ: dict | None = None) -> None:
    """Load KEY=VALUE lines into environ without overriding values already set.

    Relative PATH_KEYS values are resolved against the env file's folder, so
    LOCAL_TARGET_DIR=../public/local-photos works from any working directory."""
    environ = os.environ if environ is None else environ
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if key.startswith("export "):
            key = key[len("export "):].strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if key in PATH_KEYS and value:
            p = Path(value).expanduser()
            if not p.is_absolute():
                value = str((path.resolve().parent / p).resolve())
        environ.setdefault(key, value)


def _flag(value: str | None) -> bool:
    return (value or "").strip().lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class Config:
    source_root: Path
    target: str = "local"
    local_target_dir: Path | None = None
    s3_endpoint_url: str | None = None
    s3_bucket: str | None = None
    s3_key_id: str | None = None
    s3_app_key: str | None = None
    public_base_url: str = ""
    watermark_text: str = DEFAULT_WATERMARK
    watermark_opacity: float = DEFAULT_OPACITY
    # Safety switches for unattended runs; see sync.SENTINEL / sync.shrink_reason.
    require_sentinel: bool = False
    allow_shrink: bool = False

    def __repr__(self) -> str:  # never leak secrets into logs or tracebacks
        return (
            f"Config(source_root={str(self.source_root)!r}, target={self.target!r}, "
            f"local_target_dir={str(self.local_target_dir) if self.local_target_dir else None!r}, "
            f"s3_endpoint_url={self.s3_endpoint_url!r}, s3_bucket={self.s3_bucket!r}, "
            f"s3_key_id={'***' if self.s3_key_id else None}, "
            f"s3_app_key={'***' if self.s3_app_key else None}, "
            f"public_base_url={self.public_base_url!r})"
        )

    __str__ = __repr__

    @classmethod
    def from_env(cls, environ: dict | None = None, *, require_target: bool = True,
                 **overrides) -> "Config":
        env = dict(os.environ if environ is None else environ)
        env.update({k: v for k, v in overrides.items() if v is not None})

        def get(name: str, default: str | None = None) -> str | None:
            value = env.get(name)
            return value if value not in (None, "") else default

        source = get("PHOTO_SOURCE_ROOT")
        if not source:
            raise ConfigError("PHOTO_SOURCE_ROOT is required")
        target = (get("TARGET", "local") or "local").lower()
        if target not in ("local", "s3"):
            raise ConfigError(f"TARGET must be 'local' or 's3', got {target!r}")

        try:
            opacity = float(get("WATERMARK_OPACITY", str(DEFAULT_OPACITY)))
        except ValueError as exc:
            raise ConfigError("WATERMARK_OPACITY must be a number") from exc
        if not 0.0 <= opacity <= 1.0:
            raise ConfigError("WATERMARK_OPACITY must be between 0 and 1")

        local_dir = get("LOCAL_TARGET_DIR")
        cfg = cls(
            source_root=Path(source).expanduser(),
            target=target,
            local_target_dir=Path(local_dir).expanduser() if local_dir else None,
            s3_endpoint_url=get("S3_ENDPOINT_URL"),
            s3_bucket=get("S3_BUCKET"),
            s3_key_id=get("S3_KEY_ID"),
            s3_app_key=get("S3_APP_KEY"),
            public_base_url=(get("PUBLIC_BASE_URL", "") or "").rstrip("/"),
            watermark_text=get("WATERMARK_TEXT", DEFAULT_WATERMARK) or "",
            watermark_opacity=opacity,
            require_sentinel=_flag(get("PHOTO_REQUIRE_SENTINEL")),
            allow_shrink=_flag(get("PHOTO_ALLOW_SHRINK")),
        )
        if require_target:
            cfg.validate()
        return cfg

    def validate(self) -> None:
        if self.target == "local" and not self.local_target_dir:
            raise ConfigError("LOCAL_TARGET_DIR is required when TARGET=local")
        if self.target == "s3":
            missing = [
                name
                for name, value in (
                    ("S3_BUCKET", self.s3_bucket),
                    ("S3_KEY_ID", self.s3_key_id),
                    ("S3_APP_KEY", self.s3_app_key),
                )
                if not value
            ]
            if missing:
                raise ConfigError(f"TARGET=s3 requires: {', '.join(missing)}")
