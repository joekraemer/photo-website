"""Generate a small fake archive for tests and local development.

    python -m photo_sync.sample_archive /path/to/out

Creates Pillow-drawn JPEGs with camera EXIF *and* GPS so tests can prove that
the published files carry no metadata.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw

GPS_IFD = 0x8825
EXIF_IFD = 0x8769


def make_jpeg(path: Path, size=(3000, 2000), color=(70, 120, 180), *,
              taken_at="2024:06:15 10:00:00", model="ILCE-6400", make="SONY",
              lens="E 35mm F1.8 OSS", focal=35.0, fnumber=1.8, exposure=1 / 250,
              iso=100, gps=True, orientation=1, description=None, label=None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", size, color)
    draw = ImageDraw.Draw(img)
    w, h = size
    draw.rectangle([w // 10, h // 10, w // 2, h // 2], fill=(240, 200, 80))
    draw.ellipse([w // 2, h // 2, w - w // 10, h - h // 10], fill=(30, 30, 30))
    if label:
        draw.text((20, 20), label, fill=(255, 255, 255))

    exif = Image.Exif()
    if make:
        exif[0x010F] = make
    if model:
        exif[0x0110] = model
    if description:
        exif[0x010E] = description
    exif[0x0112] = orientation
    sub = exif.get_ifd(EXIF_IFD)
    if taken_at:
        sub[0x9003] = taken_at
    if lens:
        sub[0xA434] = lens
    if focal:
        sub[0x920A] = focal
    if fnumber:
        sub[0x829D] = fnumber
    if exposure:
        sub[0x829A] = exposure
    if iso:
        sub[0x8827] = iso
    if gps:
        g = exif.get_ifd(GPS_IFD)
        g[1] = "N"
        g[2] = (37.0, 58.0, 12.5)
        g[3] = "E"
        g[4] = (23.0, 43.0, 40.0)
    img.save(path, "JPEG", quality=90, exif=exif.tobytes())
    return path


def build(root: Path) -> Path:
    root = Path(root)
    greece = root / "2024" / "06-15-2024 Greece"
    make_jpeg(greece / "_web" / "DSC04351.jpg", taken_at="2024:06:15 09:00:00", label="Greece 1")
    make_jpeg(greece / "_web" / "DSC04639.jpg", size=(2000, 3000), color=(160, 90, 60),
              taken_at="2024:06:15 18:30:00", exposure=2.5, iso=3200, label="Greece 2")
    make_jpeg(greece / "_web" / "DSC04012-HDR.JPG", color=(40, 140, 90),
              taken_at="2024:06:15 07:15:00", label="Greece 3")
    (greece / "a6400").mkdir(parents=True, exist_ok=True)
    (greece / "a6400" / "DSC04351.dng").write_bytes(b"not a real raw")
    (greece / "album.md").write_text(
        "---\ntitle: Greece\ncover: DSC04639.jpg\n---\nIsland hopping in the Cyclades.\n",
        encoding="utf-8",
    )

    korea = root / "2023" / "10-02-2023_South_Korea"
    make_jpeg(korea / "_web" / "DSC00021.jpg", size=(1200, 800), color=(200, 60, 90),
              taken_at="2023:10:02 12:00:00", fnumber=4.0, focal=18.0, label="Korea 1")
    make_jpeg(korea / "_web" / "DSC00085.jpg", size=(800, 1200), color=(90, 60, 200),
              taken_at=None, lens=None, label="Korea 2")

    flagged = root / "2023" / "Road trip"  # non-conforming: still published, flagged
    make_jpeg(flagged / "_web" / "IMG_0001.jpg", size=(1600, 1000), color=(120, 120, 40),
              taken_at="2023:08:20 16:00:00", label="Road trip")

    hidden = root / "2022" / "05-01-2022 Private"
    make_jpeg(hidden / "_web" / "secret.jpg", size=(800, 600), taken_at="2022:05:01 10:00:00")
    (hidden / "album.md").write_text("---\nhidden: true\n---\n", encoding="utf-8")

    no_web = root / "2022" / "04-01-2022 Unedited"
    (no_web / "a6400").mkdir(parents=True, exist_ok=True)
    (no_web / "a6400" / "DSC00001.dng").write_bytes(b"raw")
    return root


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python -m photo_sync.sample_archive OUTDIR", file=sys.stderr)
        raise SystemExit(2)
    print(build(Path(sys.argv[1])))
