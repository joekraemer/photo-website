"""Image rendering (resize, sRGB, watermark, WebP) and EXIF extraction."""

from __future__ import annotations

import hashlib
import io
import math
import re
import warnings
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageCms, ImageDraw, ImageFont, ImageOps

from .cameras import camera_name

SIZES = {"thumb": 500, "medium": 1600, "large": 2560}
WEBP_QUALITY = 82

# EXIF tag ids
_MAKE, _MODEL, _DESCRIPTION = 0x010F, 0x0110, 0x010E
_EXIF_IFD = 0x8769
_EXPOSURE, _FNUMBER, _ISO = 0x829A, 0x829D, 0x8827
_DT_ORIGINAL, _DT_DIGITIZED, _FOCAL, _LENS = 0x9003, 0x9004, 0x920A, 0xA434
_OFFSET_ORIGINAL, _OFFSET_DIGITIZED = 0x9011, 0x9012

# The watermark is always drawn with this bundled font (TeX Gyre Heros, a
# Helvetica-like face under the GUST Font License; see fonts/README.md). The
# container has no Helvetica, and a system-font fallback would make the mark
# depend on where the sync ran.
FONT_PATH = Path(__file__).resolve().parent / "fonts" / "texgyreheros-regular.otf"

# Pixel limits. Pillow refuses anything over 2 x Image.MAX_IMAGE_PIXELS
# (~179 MP) as a possible decompression bomb, which a stitched panorama can
# exceed. A JPEG is decoded at 1/2, 1/4 or 1/8 scale (libjpeg "draft" mode)
# before the resize, so even a 1 GP JPEG needs a few hundred MB at most. Other
# formats are decoded at full size, so they keep Pillow's limit.
MAX_JPEG_PIXELS = 1_000_000_000
MAX_OTHER_PIXELS = 2 * 89_478_485  # Pillow's own DecompressionBombError threshold

_XMP_START, _XMP_END = b"<x:xmpmeta", b"</x:xmpmeta>"
# Lightroom writes the star rating as an attribute (xmp:Rating="4") or, in
# some exporters, as an element (<xmp:Rating>4</xmp:Rating>). Old files use
# the xap: prefix.
_RATING_RE = re.compile(
    rb"(?:xmp|xap):Rating\s*=\s*[\"']\s*(-?\d+)\s*[\"']|<(?:xmp|xap):Rating>\s*(-?\d+)\s*</")


class ImageTooLarge(ValueError):
    pass


@lru_cache(maxsize=1)
def font_digest() -> str:
    """SHA-256 of the bundled watermark font (part of the render fingerprint)."""
    return hashlib.sha256(FONT_PATH.read_bytes()).hexdigest()


@dataclass
class Rendered:
    data: bytes
    width: int
    height: int


def _num(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def format_shutter(seconds: float) -> str:
    if seconds <= 0:
        raise ValueError("exposure must be positive")
    if seconds >= 1:
        return f"{seconds:g}s" if seconds == int(seconds) else f"{round(seconds, 1):g}s"
    denom = round(1 / seconds)
    if denom and abs(1 / denom - seconds) / seconds < 0.05:
        return f"1/{denom}s"
    return f"{round(seconds, 2):g}s"  # e.g. 0.3s, as cameras display it


def _exif_time(sub, dt_tag: int, offset_tag: int) -> str | None:
    """ISO 8601 capture time, with the UTC offset when the camera recorded one."""
    raw = sub.get(dt_tag)
    if not raw:
        return None
    try:
        taken = datetime.strptime(str(raw).strip("\x00 ")[:19], "%Y:%m:%d %H:%M:%S")
    except ValueError:
        return None
    text = taken.isoformat()
    offset = str(sub.get(offset_tag) or "").strip("\x00 ")
    if re.fullmatch(r"[+-]\d{2}:\d{2}", offset):
        text += offset
    return text


def read_exif(img: Image.Image) -> dict:
    """Return the display EXIF subset. Missing fields are omitted."""
    exif = img.getexif()
    sub = exif.get_ifd(_EXIF_IFD)
    out: dict = {}

    model = exif.get(_MODEL)
    if model:
        out["camera"] = str(model).strip("\x00 ").strip()
    body_name = camera_name(exif.get(_MAKE), model)
    if body_name:
        out["body_name"] = body_name
    lens = sub.get(_LENS)
    if lens:
        out["lens"] = str(lens).strip("\x00 ").strip()
    focal = _num(sub.get(_FOCAL))
    if focal:
        out["focal_length"] = f"{round(focal):d}mm"
    fnum = _num(sub.get(_FNUMBER))
    if fnum:
        out["aperture"] = f"f/{round(fnum, 1):g}"
    exposure = _num(sub.get(_EXPOSURE))
    if exposure and exposure > 0:
        out["shutter"] = format_shutter(exposure)
    iso = sub.get(_ISO)
    if isinstance(iso, (tuple, list)):
        iso = iso[0] if iso else None
    if iso:
        try:
            out["iso"] = int(iso)
        except (TypeError, ValueError):
            pass
    # Capture time only. IFD0 DateTime (0x0132) is when Lightroom exported the
    # file, not when it was taken, so it is never used.
    taken = (_exif_time(sub, _DT_ORIGINAL, _OFFSET_ORIGINAL)
             or _exif_time(sub, _DT_DIGITIZED, _OFFSET_DIGITIZED))
    if taken:
        out["taken_at"] = taken
    return {k: v for k, v in out.items() if v not in (None, "")}


def read_rating(raw: bytes) -> int | None:
    """Lightroom star rating (XMP xmp:Rating) from the file bytes, or None."""
    start = raw.find(_XMP_START)
    if start < 0:
        return None
    end = raw.find(_XMP_END, start)
    packet = raw[start:end if end > 0 else start + 65536]
    m = _RATING_RE.search(packet)
    if not m:
        return None
    return int(m.group(1) or m.group(2))


def read_description(img: Image.Image) -> str | None:
    desc = img.getexif().get(_DESCRIPTION)
    if desc:
        desc = str(desc).strip("\x00 ").strip()
    return desc or None


def _to_srgb(img: Image.Image) -> Image.Image:
    icc = img.info.get("icc_profile")
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    if icc:
        try:
            src = ImageCms.ImageCmsProfile(io.BytesIO(icc))
            dst = ImageCms.createProfile("sRGB")
            img = ImageCms.profileToProfile(img, src, dst, outputMode="RGB")
        except (ImageCms.PyCMSError, OSError):
            img = img.convert("RGB")
    return img.convert("RGB")


def _font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_PATH), size)


def watermark(img: Image.Image, text: str, opacity: float) -> Image.Image:
    if not text or opacity <= 0:
        return img
    w, h = img.size
    size = max(12, round(min(w, h) * 0.022))
    font = _font(size)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    margin = max(8, round(min(w, h) * 0.02))
    x = w - (right - left) - margin - left
    y = h - (bottom - top) - margin - top
    alpha = round(255 * opacity)
    # Faint shadow keeps the mark legible on light skies without being loud.
    shadow = max(1, size // 16)
    draw.text((x + shadow, y + shadow), text, font=font, fill=(0, 0, 0, round(alpha * 0.6)))
    draw.text((x, y), text, font=font, fill=(255, 255, 255, alpha))
    return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")


def open_image(source) -> Image.Image:
    """Open an image lazily (header only), with photo-sync's own size limits.

    Pillow's decompression-bomb check is replaced, not just disabled: JPEGs
    may be up to MAX_JPEG_PIXELS because they are decoded at reduced scale;
    everything else keeps Pillow's limit. Raises ImageTooLarge above that."""
    saved = Image.MAX_IMAGE_PIXELS
    Image.MAX_IMAGE_PIXELS = None
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", Image.DecompressionBombWarning)
            img = Image.open(source)
    finally:
        Image.MAX_IMAGE_PIXELS = saved
    w, h = img.size
    limit = MAX_JPEG_PIXELS if img.format == "JPEG" else MAX_OTHER_PIXELS
    if w * h > limit:
        fmt = img.format or "this"
        img.close()
        raise ImageTooLarge(f"{w}x{h} is {w * h / 1e6:.0f} MP, over the {limit / 1e6:.0f} MP "
                            f"limit for {fmt} files; export a smaller copy")
    return img


def average_color(source) -> str | None:
    """The photo's average sRGB colour as '#rrggbb', for the site's loading
    placeholder. A JPEG is decoded at 1/8 scale, so this is cheap even when the
    sync reuses existing renders. Returns None if the image can't be read."""
    try:
        img = open_image(source)
        if img.format == "JPEG":
            img.draft("RGB", (64, 64))
        rgb = _to_srgb(img)
        r, g, b = rgb.resize((1, 1), Image.Resampling.BOX).getpixel((0, 0))[:3]
    except Exception:  # noqa: BLE001 - a missing colour must never fail a sync
        return None
    return f"#{r:02x}{g:02x}{b:02x}"


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


def load_source(source, long_edge: int | None = None) -> Image.Image:
    """Decode an image, shrunk to at most `long_edge` on its long side.

    For a JPEG the shrink starts inside the decoder: libjpeg is asked for the
    smallest 1/2, 1/4 or 1/8 scale that is still at least twice the final
    size (Pillow's own quality margin), so a large panorama never sits in
    memory at full size. (Image.thumbnail's built-in draft asks for a
    long_edge-square box, which a panorama's short side never reaches.)

    The final size is computed from the ORIGINAL dimensions, so it matches
    fit_size() exactly, which the sync's skip-unchanged path relies on. A
    long_edge-square box fits the long side whatever the EXIF orientation,
    so this is safe before exif_transpose."""
    img = open_image(source)
    w, h = img.size
    if not long_edge or max(w, h) <= long_edge:
        img.load()
        return img
    final = fit_size(w, h, long_edge)
    if img.format == "JPEG":
        img.draft(img.mode, (2 * final[0], 2 * final[1]))
    return img.resize(final, Image.Resampling.LANCZOS, reducing_gap=2.0)


def prepare(img: Image.Image) -> Image.Image:
    """Apply EXIF orientation and convert to sRGB, dropping all metadata."""
    oriented = ImageOps.exif_transpose(img)
    rgb = _to_srgb(oriented)
    clean = Image.new("RGB", rgb.size)
    clean.paste(rgb)
    return clean


def render(base: Image.Image, long_edge: int, wm_text: str | None = None, wm_opacity: float = 0.0) -> Rendered:
    img = base.copy()
    if max(img.size) > long_edge:  # never upscale
        img.thumbnail((long_edge, long_edge), Image.Resampling.LANCZOS)
    if wm_text:
        img = watermark(img, wm_text, wm_opacity)
    buf = io.BytesIO()
    img.save(buf, "WEBP", quality=WEBP_QUALITY, method=6, exif=b"", icc_profile=None)
    return Rendered(buf.getvalue(), img.width, img.height)
