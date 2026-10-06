"""Image rendering (resize, sRGB, watermark, WebP) and EXIF extraction."""

from __future__ import annotations

import io
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageCms, ImageDraw, ImageFont, ImageOps

SIZES = {"thumb": 500, "medium": 1600, "large": 2560}
WEBP_QUALITY = 82

# EXIF tag ids
_MAKE, _MODEL, _DESCRIPTION = 0x010F, 0x0110, 0x010E
_EXIF_IFD = 0x8769
_EXPOSURE, _FNUMBER, _ISO = 0x829A, 0x829D, 0x8827
_DT_ORIGINAL, _FOCAL, _LENS = 0x9003, 0x920A, 0xA434

_FONT_CANDIDATES = (
    "DejaVuSans.ttf",
    "Arial.ttf",
    "Helvetica.ttc",
    "/System/Library/Fonts/Helvetica.ttc",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/Library/Fonts/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "C:/Windows/Fonts/arial.ttf",
)


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


def read_exif(img: Image.Image) -> dict:
    """Return the display EXIF subset. Missing fields are omitted."""
    exif = img.getexif()
    sub = exif.get_ifd(_EXIF_IFD)
    out: dict = {}

    model = exif.get(_MODEL)
    if model:
        out["camera"] = str(model).strip("\x00 ").strip()
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
    taken = sub.get(_DT_ORIGINAL) or exif.get(0x0132)
    if taken:
        try:
            out["taken_at"] = datetime.strptime(str(taken).strip("\x00 "), "%Y:%m:%d %H:%M:%S").isoformat()
        except ValueError:
            pass
    return {k: v for k, v in out.items() if v not in (None, "")}


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


def _font(size: int) -> ImageFont.ImageFont:
    for name in _FONT_CANDIDATES:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=size)  # Pillow >= 10.1
    except TypeError:
        return ImageFont.load_default()


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


def load_source(path: Path) -> Image.Image:
    img = Image.open(path)
    img.load()
    return img


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
