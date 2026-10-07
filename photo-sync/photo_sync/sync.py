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
# Bump when rendering code changes in a way that should re-render every photo.
RENDER_VERSION = 1
# A file at the archive root that proves the real drive is there (not an empty
# mount point or a half-unmounted volume). Checked before and after the scan
# when cfg.require_sentinel is set (the fleet entry point sets it).
SENTINEL = ".photo-archive"
# A sync that would drop more than this share of albums or photos, or lose a
# whole year, is held back (no manifest write, no prune) unless
# PHOTO_ALLOW_SHRINK=1.
MAX_SHRINK = 0.20


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
    hidden_deleted: list[str] = field(default_factory=list)
    issues: list[archive.NamingIssue] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    # Per-file problems (unreadable JPEG, bad album.md). The run continues
    # without the affected photo/album; the CLI exits non-zero.
    errors: list[str] = field(default_factory=list)
    manifest: dict | None = None
    # Set when the run was skipped before writing anything (sentinel missing).
    skipped: str | None = None
    # Set when the shrink guard held back the manifest and the prune. The CLI
    # exits non-zero so the fleet health check flags it.
    blocked: str | None = None


def render_fingerprint(cfg) -> bytes:
    """Every setting that changes the rendered bytes. Folded into object keys so a
    change produces new keys (old ones become orphans) instead of being skipped or
    served stale from an `immutable` cache."""
    settings = {
        "render_version": RENDER_VERSION,
        "sizes": imaging.SIZES,
        "webp_quality": imaging.WEBP_QUALITY,
        "watermark_text": cfg.watermark_text,
        "watermark_opacity": cfg.watermark_opacity,
    }
    return json.dumps(settings, sort_keys=True).encode("utf-8")


def content_digest(raw: bytes, fingerprint: bytes) -> str:
    h = hashlib.sha256(raw)
    h.update(b"\0")
    h.update(fingerprint)
    return h.hexdigest()


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


def format_errors(errors: list[str]) -> str:
    lines = ["Errors:"]
    if not errors:
        lines.append("  none")
    lines.extend(f"  - {e}" for e in errors)
    return "\n".join(lines)


def _strip_volatile(manifest: dict | None) -> dict | None:
    if manifest is None:
        return None
    return {k: v for k, v in manifest.items() if k != "generated_at"}


def sentinel_missing(cfg) -> str | None:
    if not getattr(cfg, "require_sentinel", False):
        return None
    try:
        if (cfg.source_root / SENTINEL).is_file():
            return None
    except OSError:
        pass
    return f"{cfg.source_root}/{SENTINEL} not found (archive drive missing or pulled?)"


def shrink_reason(previous: dict | None, manifest: dict,
                  hidden_prefixes: list[str] = ()) -> str | None:
    """Why publishing `manifest` over `previous` looks like a lost source, or None.

    Albums the archive now marks hidden are left out of the comparison: hiding
    one is a deliberate removal, seen in album.md, not a missing folder."""
    if not previous or not previous.get("albums"):
        return None

    def hidden(album: dict) -> bool:
        return f"{PHOTO_PREFIX}{album.get('slug')}/" in hidden_prefixes

    old = [a for a in previous["albums"] if not hidden(a)]
    new = manifest["albums"]
    if not old:
        return None
    old_years = {a.get("year") for a in old if a.get("year") is not None}
    new_years = {a.get("year") for a in new if a.get("year") is not None}
    gone = sorted(old_years - new_years)
    if gone:
        return f"year(s) {', '.join(map(str, gone))} disappeared from the source"
    old_photos = sum(len(a.get("photos", [])) for a in old)
    new_photos = sum(len(a.get("photos", [])) for a in new)
    for what, before, after in (("albums", len(old), len(new)), ("photos", old_photos, new_photos)):
        if before and after < before * (1 - MAX_SHRINK):
            return f"{what} would drop from {before} to {after} (more than {MAX_SHRINK:.0%})"
    return None


def _base_slug(shoot: archive.Shoot) -> str:
    if shoot.conforming:
        return f"{shoot.folder_date.isoformat()}-{archive.slugify(shoot.name)}"
    return archive.slugify(shoot.folder.name)


def run(cfg, target=None, *, check: bool = False, prune: bool = False,
        log: Callable[[str], None] = print) -> Result:
    result = Result()
    if not check and (reason := sentinel_missing(cfg)):
        result.skipped = reason
        log(f"Skipping sync: {reason}. Nothing was uploaded or deleted.")
        return result
    shoots, issues = archive.scan(cfg.source_root, result.errors)
    result.issues = issues
    log(format_issues(issues))

    if check:
        visible = [s for s in shoots if not s.meta.hidden and not s.meta_unreadable]
        result.albums = len(visible)
        result.hidden_albums = sum(1 for s in shoots if s.meta.hidden)
        for shoot in visible:
            for src in shoot.photos:
                try:
                    with Image.open(src) as img:
                        img.verify()
                    result.photos += 1
                except Exception as exc:  # noqa: BLE001 - any decode failure is a per-file error
                    result.errors.append(f"{shoot.rel}/_web/{src.name}: unreadable image ({exc})")
        log(format_errors(result.errors))
        log(f"Check: {result.albums} albums, {result.hidden_albums} hidden, "
            f"{result.photos} photos, {len(issues)} naming issues, "
            f"{len(result.errors)} errors. No changes made.")
        return result

    if target is None:
        raise ValueError("a target is required unless check=True")

    # Again after the scan: a drive pulled mid-scan reads as missing folders.
    if reason := sentinel_missing(cfg):
        result.skipped = reason
        log(f"Skipping sync: {reason}. Nothing was uploaded or deleted.")
        return result

    existing = target.list_keys(PHOTO_PREFIX)
    expected: set[str] = set()
    albums: list[dict] = []
    used_slugs: set[str] = set()
    hidden_prefixes: list[str] = []
    fingerprint = render_fingerprint(cfg)

    for shoot in shoots:
        if shoot.meta.hidden:
            result.hidden_albums += 1
            hidden_prefixes.append(f"{PHOTO_PREFIX}{_base_slug(shoot)}/")
            continue
        if shoot.meta_unreadable:
            continue  # already in result.errors
        if not shoot.photos:
            result.warnings.append(f"{shoot.rel}: _web/ has no JPEGs; skipped")
            continue

        base_slug = _base_slug(shoot)
        slug, n = base_slug, 2
        while slug in used_slugs:
            slug, n = f"{base_slug}-{n}", n + 1
        used_slugs.add(slug)
        if slug != base_slug:
            result.warnings.append(
                f"{shoot.rel}: slug '{base_slug}' already used by another album; published as '{slug}'")

        title = shoot.meta.title or shoot.name
        photos: list[dict] = []
        cover_id = None
        seen_ids: set[str] = set()

        for src in shoot.photos:
            raw = src.read_bytes()
            digest = content_digest(raw, fingerprint)
            photo_slug = archive.slugify(src.stem)
            keys = photo_keys(slug, photo_slug, digest)
            photo_id = f"{photo_slug}-{digest[:8]}"
            if photo_id in seen_ids:
                result.warnings.append(f"{shoot.rel}/_web/{src.name}: duplicate of another export; skipped")
                continue
            seen_ids.add(photo_id)

            reuse = all(k in existing for k in keys.values())
            try:
                if reuse:
                    # Lazy open: EXIF and size come from the header, no full decode.
                    img = Image.open(io.BytesIO(raw))
                else:
                    img = imaging.load_source(io.BytesIO(raw))
                exif = imaging.read_exif(img)
                description = imaging.read_description(img)
                if reuse:
                    width, height = fit_size(*_oriented_size(img), imaging.SIZES["large"])
                    rendered = None
                else:
                    base = imaging.prepare(img)
                    rendered = {}
                    for size, edge in imaging.SIZES.items():
                        is_large = size == "large"
                        rendered[size] = imaging.render(
                            base, edge,
                            wm_text=cfg.watermark_text if is_large else None,
                            wm_opacity=cfg.watermark_opacity,
                        )
                    width, height = rendered["large"].width, rendered["large"].height
            except Exception as exc:  # noqa: BLE001 - any decode/render failure skips just this photo
                result.errors.append(f"{shoot.rel}/_web/{src.name}: unreadable image ({exc}); skipped")
                continue

            expected.update(keys.values())
            if rendered is None:
                result.skipped_photos += 1
            else:
                for size, out in rendered.items():
                    target.put(keys[size], out.data, "image/webp", PHOTO_CACHE)
                    result.uploaded_objects += 1
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

    # The published manifest is what the shrink and error guards compare
    # against. If it is there but can't be read or parsed, those guards would
    # be blind, so the run is held instead of treated as a first sync.
    previous = None
    manifest_problem = None
    try:
        prev_raw = target.read(MANIFEST_KEY)
    except Exception as exc:  # noqa: BLE001 - permission, network, provider errors
        prev_raw = None
        manifest_problem = f"the published photos.json could not be read ({type(exc).__name__})"
    if prev_raw is not None:
        try:
            previous = json.loads(prev_raw)
            if not isinstance(previous, dict) or not isinstance(previous.get("albums"), list):
                raise ValueError("no 'albums' list")
        except ValueError as exc:
            previous = None
            manifest_problem = f"the published photos.json is not valid JSON ({exc})"

    # The drive may have gone away while rendering; publish nothing then.
    if reason := sentinel_missing(cfg):
        result.skipped = reason
        log(f"Skipping manifest and prune: {reason}. Rendered images were uploaded; "
            "nothing was deleted.")
        return result

    hold = None
    if previous is None and manifest_problem is None and existing and prune:
        # No photos.json but photos/ objects exist: someone deleted the
        # manifest, or a previous run died before writing it. There is nothing
        # to compare against, so publish but don't delete anything this run.
        log(f"WARNING: no published photos.json but {len(existing)} objects under "
            f"{PHOTO_PREFIX}; not pruning this run.")
        prune = False

    if manifest_problem:
        hold = "unreadable"
        result.blocked = manifest_problem
        log(f"ERROR: {manifest_problem}. photos.json was not updated and nothing was "
            "pruned. Fix or delete the published photos.json, then re-run.")
    elif result.errors and previous is not None:
        # Keep the published manifest rather than drop the photos that failed.
        hold = "errors"
        log("Not updating photos.json: fix the errors below first, so an unreadable "
            "file does not disappear from the site. Rendered images were still uploaded.")
    elif (reason := shrink_reason(previous, manifest, hidden_prefixes)) and not getattr(cfg, "allow_shrink", False):
        hold = "shrink"
        result.blocked = reason
        log(f"ERROR: refusing to publish a smaller site: {reason}. photos.json was not "
            "updated and nothing was pruned. If this is a deliberate cleanup, re-run with "
            "PHOTO_ALLOW_SHRINK=1.")
    elif reason:
        log(f"Warning: {reason}; publishing anyway because PHOTO_ALLOW_SHRINK=1")

    if hold:
        result.manifest = previous
        prune = False
    elif _strip_volatile(previous) != _strip_volatile(manifest):
        body = json.dumps(manifest, indent=2, ensure_ascii=False).encode("utf-8")
        target.put(MANIFEST_KEY, body, "application/json; charset=utf-8", MANIFEST_CACHE)
        result.uploaded_objects += 1
        result.manifest_written = True
    else:
        result.manifest = previous

    # Hiding an album must take it off the bucket now, not at the next --prune:
    # its keys are guessable (slug + 8 hex chars). Only keys no visible album
    # uses are touched, so a visible album sharing the slug is safe.
    #
    # This runs even while photos.json is held back (errors, shrink, unreadable
    # manifest). Then the published manifest still lists the hidden album and
    # the site shows broken images for it until the hold clears. That is on
    # purpose: hiding an album is a privacy decision, and taking its images
    # offline now matters more than a tidy page in the meantime.
    hidden_keys = sorted(k for k in existing - expected
                         if any(k.startswith(p) for p in hidden_prefixes))
    if hidden_keys:
        log(f"Deleting {len(hidden_keys)} objects of hidden albums")
        for key in hidden_keys:
            log(f"  - {key}")
            target.delete(key)
            result.hidden_deleted.append(key)
        existing -= set(hidden_keys)

    result.orphans = sorted(existing - expected)
    if prune and result.errors and result.orphans:
        log("Not pruning: fix the errors below first, so a temporarily unreadable "
            "file does not delete its published copies.")
        prune = False
    if result.orphans:
        if prune:
            verb = "Deleting"
        elif hold:
            verb = "Orphaned (kept while photos.json is held back)"
        else:
            verb = "Orphaned (run with --prune to delete)"
        log(f"{verb}: {len(result.orphans)} objects")
        for key in result.orphans:
            log(f"  - {key}")
            if prune:
                target.delete(key)
                result.deleted.append(key)

    for warning in result.warnings:
        log(f"Warning: {warning}")
    if result.errors:
        log(format_errors(result.errors))
    log(f"Done: {result.albums} albums, {result.photos} photos, "
        f"{result.uploaded_photos} rendered, {result.skipped_photos} unchanged, "
        f"{result.uploaded_objects} objects written, manifest "
        f"{'updated' if result.manifest_written else ('held back' if hold else 'unchanged')}, "
        f"{len(result.orphans)} orphans{' deleted' if prune and result.orphans else ''}, "
        f"{len(result.errors)} errors.")
    return result
