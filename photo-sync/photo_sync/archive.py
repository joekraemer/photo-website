"""Walk the archive, validate shoot folder names, and read album.md."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import yaml

SHOOT_RE = re.compile(r"^(\d{2})-(\d{2})-(\d{4})[ _]+(\S.*)$")
YEAR_RE = re.compile(r"^\d{4}$")
WEB_DIR = "_web"
JPEG_SUFFIXES = {".jpg", ".jpeg"}


@dataclass
class NamingIssue:
    path: str  # relative to the archive root
    problem: str


@dataclass
class AlbumMeta:
    title: str | None = None
    cover: str | None = None
    hidden: bool = False
    order: int | None = None
    intro: str = ""


@dataclass
class Shoot:
    folder: Path
    rel: str  # "<YEAR>/<folder>"
    year: int
    folder_date: date | None  # None when the name did not conform
    name: str  # display name from the folder (or the raw folder name)
    conforming: bool
    photos: list[Path] = field(default_factory=list)
    meta: AlbumMeta = field(default_factory=AlbumMeta)


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text or "untitled"


def parse_shoot_name(name: str, parent_year: int | None) -> tuple[date | None, str | None, list[str]]:
    """Return (date, display_name, problems) for a shoot folder name."""
    m = SHOOT_RE.match(name)
    if not m:
        return None, None, ["name does not match 'MM-DD-YYYY Name'"]
    month, day, year, rest = (int(m.group(1)), int(m.group(2)), int(m.group(3)), m.group(4))
    display = re.sub(r"[ _]+", " ", rest).strip()
    try:
        d = date(year, month, day)
    except ValueError:
        return None, None, [f"impossible date {m.group(1)}-{m.group(2)}-{m.group(3)}"]
    if parent_year is not None and year != parent_year:
        return None, None, [f"year {year} does not match parent folder {parent_year}"]
    return d, display, []


def parse_album_md(path: Path) -> AlbumMeta:
    text = path.read_text(encoding="utf-8")
    front: dict = {}
    body = text
    if text.startswith("---"):
        parts = re.split(r"^---[ \t]*$", text, maxsplit=2, flags=re.MULTILINE)
        # parts: ["", frontmatter, body]
        if len(parts) == 3:
            loaded = yaml.safe_load(parts[1]) or {}
            if not isinstance(loaded, dict):
                raise ValueError(f"{path}: frontmatter must be a mapping")
            front = loaded
            body = parts[2]
    order = front.get("order")
    return AlbumMeta(
        title=str(front["title"]).strip() if front.get("title") else None,
        cover=str(front["cover"]).strip() if front.get("cover") else None,
        hidden=bool(front.get("hidden", False)),
        order=int(order) if order is not None else None,
        intro=body.strip(),
    )


def scan(root: Path) -> tuple[list[Shoot], list[NamingIssue]]:
    """Find every shoot with a _web folder. Non-conforming shoots are still returned."""
    root = Path(root)
    if not root.is_dir():
        raise FileNotFoundError(f"PHOTO_SOURCE_ROOT does not exist: {root}")
    shoots: list[Shoot] = []
    issues: list[NamingIssue] = []

    for year_dir in sorted(p for p in root.iterdir() if p.is_dir() and not p.name.startswith(".")):
        if not YEAR_RE.match(year_dir.name):
            issues.append(NamingIssue(year_dir.name, "top-level folder is not a YYYY year; skipped"))
            continue
        parent_year = int(year_dir.name)
        for shoot_dir in sorted(p for p in year_dir.iterdir() if p.is_dir() and not p.name.startswith(".")):
            web = shoot_dir / WEB_DIR
            if not web.is_dir():
                continue
            rel = f"{year_dir.name}/{shoot_dir.name}"
            d, display, problems = parse_shoot_name(shoot_dir.name, parent_year)
            for problem in problems:
                issues.append(NamingIssue(rel, problem))
            photos = sorted(
                p for p in web.iterdir()
                if p.is_file() and p.suffix.lower() in JPEG_SUFFIXES and not p.name.startswith(".")
            )
            meta = AlbumMeta()
            md = shoot_dir / "album.md"
            if md.is_file():
                meta = parse_album_md(md)
            shoots.append(Shoot(
                folder=shoot_dir,
                rel=rel,
                year=parent_year,
                folder_date=d,
                name=display if display else shoot_dir.name,
                conforming=not problems,
                photos=photos,
                meta=meta,
            ))
    return shoots, issues
