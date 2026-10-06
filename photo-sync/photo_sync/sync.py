"""Sync orchestration: archive -> web sizes + photos.json on a target."""

from __future__ import annotations

import hashlib
import io
import json
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable

from PIL import Image

from . import archive, imaging
from .targets import MANIFEST_CACHE, PHOTO_CACHE

MANIFEST_KEY = "photos.json"
PHOTO_PREFIX = "photos/"
MANIFEST_VERSION = 1


@dataclass
class Result:
    albums: int = 0
    hidden_albums: int = 0
    photos: int = 0
    uploaded_photos: int = 0
    skipped_photos: int = 0
    uploaded_objects: int = 0
    manifest_written: bool = False
    orphans: list[str] = field(default_factory=list)
    deleted: list[str] = field(default_factory=list)
    issues: list[archive.NamingIssue] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    manifest: dict | None = None


def photo_keys(album_slug: str, photo_slug: str, digest: str) -> dict[str, str]:
    stem = f"{PHOTO_PREFIX}{album_slug}/{photo_slug}-{digest[:8]}"
    return {size: f"{stem}-{size}.webp" for size in imaging.SIZES}


def fit_size(width: int, height: int, long_edge: int) -> tuple[int, int]:
    """Mirror PIL.Image.thumbnail's size math so skipped photos report exact dimensions."""
    if width <= long_edge and height <= long_edge:
        return width, height
    aspect = width / height
    x = y = long_edge

    def round_aspect(number, key):
        return max(min(math.floor(number), math.ceil(number), key=key), 1)

    if x / y >= aspect:
        x = round_aspect(y * aspect, key=lambda n: abs(aspect - n / y))
    else:
        y = round_aspect(x / aspect, key=lambda n: 0 if n == 0 else abs(aspect - x / n))
    return x, y


def _oriented_size(img: Image.Image) -> tuple[int, int]:
    orientation = img.getexif().get(0x0112, 1)
    w, h = img.size
    return (h, w) if orientation in (5, 6, 7, 8) else (w, h)


def format_issues(issues: list[archive.NamingIssue]) -> str:
    lines = ["Naming issues:"]
    if not issues:
        lines.append("  none")
    for issue in issues:
        lines.append(f"  - {issue.path}: {issue.problem}")
    return "\n".join(lines)


def _strip_volatile(manifest: dict | None) -> dict | None:
    if manifest is None:
        return None
    return {k: v for k, v in manifest.items() if k != "generated_at"}


def run(cfg, target=None, *, check: bool = False, prune: bool = False,
        log: Callable[[str], None] = print) -> Result:
    result = Result()
    shoots, issues = archive.scan(cfg.source_root)
    result.issues = issues
    log(format_issues(issues))

    if check:
        visible = [s for s in shoots if not s.meta.hidden]
        result.albums = len(visible)
        result.hidden_albums = len(shoots) - len(visible)
        result.photos = sum(len(s.photos) for s in visible)
        log(f"Check: {result.albums} albums, {result.hidden_albums} hidden, "
            f"{result.photos} photos, {len(issues)} naming issues. No changes made.")
        return result

    if target is None:
        raise ValueError("a target is required unless check=True")

    existing = target.list_keys(PHOTO_PREFIX)
    expected: set[str] = set()
    albums: list[dict] = []
    used_slugs: set[str] = set()

    for shoot in shoots:
        if shoot.meta.hidden:
            result.hidden_albums += 1
            continue
        if not shoot.photos:
            result.warnings.append(f"{shoot.rel}: _web/ has no JPEGs; skipped")
            continue

        if shoot.conforming:
            base_slug = f"{shoot.folder_date.isoformat()}-{archive.slugify(shoot.name)}"
        else:
            base_slug = archive.slugify(shoot.folder.name)
        slug, n = base_slug, 2
        while slug in used_slugs:
            slug, n = f"{base_slug}-{n}", n + 1
        used_slugs.add(slug)

        title = shoot.meta.title or shoot.name
        photos: list[dict] = []
        cover_id = None
        seen_ids: set[str] = set()

        for src in shoot.photos:
            raw = src.read_bytes()
            digest = hashlib.sha256(raw).hexdigest()
            photo_slug = archive.slugify(src.stem)
            keys = photo_keys(slug, photo_slug, digest)
            photo_id = f"{photo_slug}-{digest[:8]}"
            if photo_id in seen_ids:
                result.warnings.append(f"{shoot.rel}/_web/{src.name}: duplicate of another export; skipped")
                continue
            seen_ids.add(photo_id)
            expected.update(keys.values())

            img = imaging.load_source(io.BytesIO(raw))
            exif = imaging.read_exif(img)
            description = imaging.read_description(img)

            if all(k in existing for k in keys.values()):
                width, height = fit_size(*_oriented_size(img), imaging.SIZES["large"])
                result.skipped_photos += 1
            else:
                base = imaging.prepare(img)
                width = height = 0
                for size, edge in imaging.SIZES.items():
                    is_large = size == "large"
                    out = imaging.render(
                        base, edge,
                        wm_text=cfg.watermark_text if is_large else None,
                        wm_opacity=cfg.watermark_opacity,
                    )
                    target.put(keys[size], out.data, "image/webp", PHOTO_CACHE)
                    result.uploaded_objects += 1
                    if is_large:
                        width, height = out.width, out.height
                result.uploaded_photos += 1
                log(f"  + {shoot.rel}/_web/{src.name}")

            if shoot.meta.cover and src.name.lower() == shoot.meta.cover.lower():
                cover_id = photo_id
            photos.append({
                "id": photo_id,
                "alt": description or f"{title} — {src.stem}",
                "width": width,
                "height": height,
                "aspect": round(width / height, 4) if height else None,
                "sizes": dict(keys),
                "exif": exif,
                "_name": src.name,
            })

        photos.sort(key=lambda p: (p["exif"].get("taken_at") is None,
                                   p["exif"].get("taken_at", ""), p["_name"].lower()))
        for p in photos:
            p.pop("_name")
        if not photos:
            continue
        if shoot.meta.cover and cover_id is None:
            result.warnings.append(f"{shoot.rel}: cover '{shoot.meta.cover}' not found in _web/; using first photo")

        if shoot.folder_date is not None:
            album_date = shoot.folder_date.isoformat()
        else:
            times = [p["exif"]["taken_at"] for p in photos if p["exif"].get("taken_at")]
            album_date = min(times)[:10] if times else None
            if album_date is None:
                result.warnings.append(f"{shoot.rel}: no folder date and no EXIF date; album date unknown")

        album = {
            "slug": slug,
            "title": title,
            "date": album_date,
            "intro": shoot.meta.intro,
            "cover": cover_id or photos[0]["id"],
            "year": shoot.year,
            "photos": photos,
        }
        if shoot.meta.order is not None:
            album["order"] = shoot.meta.order
        albums.append(album)
        result.photos += len(photos)

    # Newest first; undated albums last. An explicit album.md `order` pins albums
    # to the top, lowest number first.
    albums.sort(key=lambda a: (a.get("date") or ""), reverse=True)
    albums.sort(key=lambda a: (a.get("order") is None, a.get("order") or 0))
    result.albums = len(albums)

    manifest = {
        "version": MANIFEST_VERSION,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "base_url": cfg.public_base_url,
        "albums": albums,
    }
    result.manifest = manifest

    previous = None
    prev_raw = target.read(MANIFEST_KEY)
    if prev_raw:
        try:
            previous = json.loads(prev_raw)
        except ValueError:
            previous = None
    if _strip_volatile(previous) != _strip_volatile(manifest):
        body = json.dumps(manifest, indent=2, ensure_ascii=False).encode("utf-8")
        target.put(MANIFEST_KEY, body, "application/json; charset=utf-8", MANIFEST_CACHE)
        result.uploaded_objects += 1
        result.manifest_written = True
    else:
        result.manifest = previous

    result.orphans = sorted(existing - expected)
    if result.orphans:
        verb = "Deleting" if prune else "Orphaned (run with --prune to delete)"
        log(f"{verb}: {len(result.orphans)} objects")
        for key in result.orphans:
            log(f"  - {key}")
            if prune:
                target.delete(key)
                result.deleted.append(key)

    for warning in result.warnings:
        log(f"Warning: {warning}")
    log(f"Done: {result.albums} albums, {result.photos} photos, "
        f"{result.uploaded_photos} rendered, {result.skipped_photos} unchanged, "
        f"{result.uploaded_objects} objects written, manifest "
        f"{'updated' if result.manifest_written else 'unchanged'}, "
        f"{len(result.orphans)} orphans{' deleted' if prune and result.orphans else ''}.")
    return result
