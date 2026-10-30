"""Local cache of what a sync learned from each `_web/` export.

Without it every run reads every export in full, hashes it and decodes it for
the placeholders, even when nothing changed. With it, an export whose path,
size and mtime match the cached entry (rendered with the same settings) is not
read at all, as long as its renders are still on the target.

The cache is an optimisation only. A missing, unreadable or malformed cache,
or a malformed entry, means a full read of that file, never a skip. Losing it
costs one slow run.

Location: PHOTO_CACHE_FILE, else $XDG_CACHE_HOME/photo-sync/photo-sync-cache.json,
else ~/.cache/photo-sync/photo-sync-cache.json. In the fleet container HOME is
/home/app, which is the `photo-sync-home` named volume, so the cache survives
container replaces.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path

CACHE_VERSION = 1


def default_path() -> Path:
    explicit = os.environ.get("PHOTO_CACHE_FILE")
    if explicit:
        return Path(explicit).expanduser()
    base = os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache"
    return Path(base) / "photo-sync" / "photo-sync-cache.json"


def _fingerprint_id(fingerprint: bytes) -> str:
    return hashlib.sha256(fingerprint).hexdigest()


def _valid_entry(e) -> bool:
    """Every field the sync uses from an entry, with the right type."""
    return (
        isinstance(e, dict)
        and isinstance(e.get("size"), int)
        and isinstance(e.get("mtime_ns"), int)
        and isinstance(e.get("fingerprint"), str)
        and isinstance(e.get("digest"), str) and len(e["digest"]) == 64
        and isinstance(e.get("exif"), dict)
        and (e.get("description") is None or isinstance(e.get("description"), str))
        and (e.get("rating") is None or isinstance(e.get("rating"), int))
        and isinstance(e.get("width"), int) and isinstance(e.get("height"), int)
        and isinstance(e.get("placeholder"), dict)
    )


class ExportCache:
    def __init__(self, path: Path | None, fingerprint: bytes, entries: dict | None = None):
        self.path = path
        self.fingerprint = _fingerprint_id(fingerprint)
        self._old = entries or {}
        self._new: dict[str, dict] = {}
        self.hits = 0
        self.misses = 0

    @classmethod
    def load(cls, path: Path | None, fingerprint: bytes, log=print) -> "ExportCache":
        """Read the cache. Anything wrong with it gives an empty cache."""
        if path is None:
            return cls(None, fingerprint)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return cls(path, fingerprint)
        except (OSError, ValueError) as exc:
            log(f"Warning: photo-sync cache {path} unreadable ({exc}); reading every export")
            return cls(path, fingerprint)
        if (not isinstance(data, dict) or data.get("version") != CACHE_VERSION
                or not isinstance(data.get("entries"), dict)):
            log(f"Warning: photo-sync cache {path} has an unknown format; reading every export")
            return cls(path, fingerprint)
        return cls(path, fingerprint, data["entries"])

    def lookup(self, rel: str, size: int, mtime_ns: int) -> dict | None:
        """The cached entry for this export, or None if anything differs."""
        e = self._old.get(rel)
        if (_valid_entry(e) and e["size"] == size and e["mtime_ns"] == mtime_ns
                and e["fingerprint"] == self.fingerprint):
            return e
        return None

    def keep(self, rel: str, entry: dict) -> None:
        """Carry an entry (hit or freshly computed) into the next save."""
        self._new[rel] = entry

    def entry(self, *, size: int, mtime_ns: int, digest: str, exif: dict,
              description: str | None, rating: int | None, width: int, height: int,
              placeholder: dict) -> dict:
        return {"size": size, "mtime_ns": mtime_ns, "fingerprint": self.fingerprint,
                "digest": digest, "exif": exif, "description": description,
                "rating": rating, "width": width, "height": height,
                "placeholder": placeholder}

    def save(self, log=print) -> None:
        """Write the entries seen this run, atomically. A failure is a warning."""
        if self.path is None:
            return
        body = json.dumps({"version": CACHE_VERSION, "entries": self._new},
                          ensure_ascii=False, separators=(",", ":"))
        tmp = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp = tempfile.mkstemp(prefix=".photo-sync-cache.", dir=self.path.parent)
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(body)
            os.replace(tmp, self.path)
            tmp = None
        except OSError as exc:
            log(f"Warning: could not write photo-sync cache {self.path} ({exc}); "
                "the next run reads every export")
        finally:
            if tmp:
                try:
                    os.unlink(tmp)
                except OSError:
                    pass
