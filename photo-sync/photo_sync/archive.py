"""Walk the archive, validate shoot folder names, and read album.md."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import yaml

# Exactly "MM-DD-YYYY Name": one space after the date, non-empty name, no
# leading/trailing whitespace. Underscores or other separators are flagged.
SHOOT_RE = re.compile(r"^(\d{2})-(\d{2})-(\d{4}) (\S(?:.*\S)?)$")
DATE_PREFIX_RE = re.compile(r"^\d{2}-\d{2}-\d{4}")
YEAR_RE = re.compile(r"^\d{4}$")
WEB_DIR = "_web"
ALBUM_KEYS = frozenset({"title", "cover", "hidden", "order"})


def name_key(name: str) -> str:
    """Compare file names the way a person would: macOS stores names in NFD,
    an album.md typed by hand is usually NFC, and case should not matter."""
    return unicodedata.normalize("NFC", name).casefold()


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
    # album.md could not be read at all, so whether the album is hidden is
    # unknown. Such shoots are never published.
    meta_unreadable: bool = False


class AlbumMetaError(ValueError):
    """album.md could not be parsed; the album's settings (incl. hidden) are unknown."""


class _FrontmatterLoader(yaml.SafeLoader):
    """SafeLoader that leaves date-looking values as text. Stock YAML turns
    `date: 2024-13-45` into a ValueError (not a YAMLError) that would crash
    the whole run; no album.md field is a date anyway."""


_FrontmatterLoader.yaml_implicit_resolvers = {
    first: [(tag, rx) for tag, rx in resolvers if tag != "tag:yaml.org,2002:timestamp"]
    for first, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text or "untitled"


def parse_shoot_name(name: str, parent_year: int | None) -> tuple[date | None, str | None, list[str]]:
    """Return (date, display_name, problems) for a shoot folder name."""
    m = SHOOT_RE.match(name)
    if not m:
        if DATE_PREFIX_RE.match(name) and name[10:].strip(" _-"):
            return None, None, ["name does not match 'MM-DD-YYYY Name' "
                                "(use a single space after the date)"]
        return None, None, ["name does not match 'MM-DD-YYYY Name'"]
    month, day, year, display = (int(m.group(1)), int(m.group(2)), int(m.group(3)), m.group(4))
    try:
        d = date(year, month, day)
    except ValueError:
        return None, None, [f"impossible date {m.group(1)}-{m.group(2)}-{m.group(3)}"]
    if parent_year is not None and year != parent_year:
        return None, None, [f"year {year} does not match parent folder {parent_year}"]
    return d, display, []


def parse_album_md(path: Path, problems: list[str] | None = None) -> AlbumMeta:
    """Parse album.md. Raises AlbumMetaError when the file or its frontmatter is
    unreadable (then even `hidden` is unknown). A mistake in one field (wrong
    type, unknown key) only ignores that field, keeping its default, and is
    described in `problems` so the caller can warn; `hidden` with an
    unrecognised value is treated as hidden."""
    problems = [] if problems is None else problems
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise AlbumMetaError(f"album.md unreadable: {exc}") from exc
    front: dict = {}
    body = text
    if text.startswith("---"):
        parts = re.split(r"^---[ \t]*$", text, maxsplit=2, flags=re.MULTILINE)
        # parts: ["", frontmatter, body]
        if len(parts) == 3:
            try:
                loaded = yaml.load(parts[1], Loader=_FrontmatterLoader) or {}
            except (yaml.YAMLError, ValueError) as exc:
                raise AlbumMetaError(f"album.md frontmatter is not valid YAML: {exc}") from exc
            if not isinstance(loaded, dict):
                raise AlbumMetaError("album.md frontmatter must be a mapping of key: value")
            front = loaded
            body = parts[2]

    for key in front:
        if key not in ALBUM_KEYS:
            problems.append(f"album.md has unknown key {str(key)!r} (known: "
                            f"{', '.join(sorted(ALBUM_KEYS))}); ignored")

    def text_field(name: str) -> str | None:
        value = front.get(name)
        if value is None or value == "":
            return None
        if isinstance(value, (dict, list)):
            problems.append(f"album.md '{name}' must be text; ignored")
            return None
        return str(value).strip() or None

    order = front.get("order")
    if order is not None and (isinstance(order, bool) or not isinstance(order, int)):
        problems.append(f"album.md 'order' must be a whole number, got {order!r}; ignored")
        order = None

    hidden = front.get("hidden", False)
    if hidden is None:
        hidden = False
    elif not isinstance(hidden, bool):
        problems.append(f"album.md 'hidden' must be true or false, got {hidden!r}; treating as hidden")
        hidden = True

    return AlbumMeta(
        title=text_field("title"),
        cover=text_field("cover"),
        hidden=hidden,
        order=order,
        intro=body.strip(),
    )


def scan(root: Path, errors: list[str] | None = None,
         warnings: list[str] | None = None) -> tuple[list[Shoot], list[NamingIssue]]:
    """Find every shoot with a _web folder. Non-conforming shoots are still returned.

    An album.md that cannot be read at all is appended to `errors`; a mistake
    in one of its fields goes to `warnings`, both as "<rel>: <problem>".
    Every non-hidden file in _web/ is returned as a photo candidate: the sync
    decides whether it is an image it can render."""
    errors = [] if errors is None else errors
    warnings = [] if warnings is None else warnings
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
                (p for p in web.iterdir() if p.is_file() and not p.name.startswith(".")),
                key=lambda p: name_key(p.name),
            )
            meta = AlbumMeta()
            unreadable = False
            md = shoot_dir / "album.md"
            if md.is_file():
                problems_md: list[str] = []
                try:
                    meta = parse_album_md(md, problems_md)
                except AlbumMetaError as exc:
                    unreadable = True
                    errors.append(f"{rel}: {exc}; album not published until fixed")
                warnings.extend(f"{rel}: {p}" for p in problems_md)
            shoots.append(Shoot(
                folder=shoot_dir,
                rel=rel,
                year=parent_year,
                folder_date=d,
                name=display if display else shoot_dir.name,
                conforming=not problems,
                photos=photos,
                meta=meta,
                meta_unreadable=unreadable,
            ))
    return shoots, issues
