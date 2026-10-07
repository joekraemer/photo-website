"""Fleet entry point: the same CLI, behind a guard for an unplugged archive drive.

The masters live on a USB HDD that is often unplugged. A sync against an empty
or missing source would publish an empty photos.json (the site goes blank) and,
with --prune, delete every photo on the bucket. So before handing over to the
CLI, this module checks the source and SKIPS the run when:

  * PHOTO_SOURCE_ROOT does not exist or is not a directory;
  * PHOTO_MOUNT_POINT (default: PHOTO_SOURCE_ROOT) is not a mount point, unless
    PHOTO_REQUIRE_MOUNT=0 (the fleet sets 0: under Colima the drive is not a
    separate mount inside the container, so the check cannot see it);
  * the sentinel file <source>/.photo-archive is missing (PHOTO_REQUIRE_SENTINEL,
    on by default here; sync.run checks it again after the scan);
  * the source holds zero shoot folders (<YEAR>/<shoot>/_web/), which is what an
    empty mount point or a stale macOS /Volumes/<name> folder looks like.

A source that is there but smaller than what is published (a year folder
moved away, a drive pulled mid-scan) is caught later by sync.run's shrink
guard, which holds back photos.json and the prune unless PHOTO_ALLOW_SHRINK=1.

A skip returns 0 and logs one INFO line: an unplugged drive is the normal case,
not a failure for the fleet health check to open an issue about.

`--check` is passed straight through: it writes nothing, so it is always safe.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from . import archive, cli, sync
from .config import _flag, load_env_file


def _truthy(value: str | None, default: bool) -> bool:
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() not in ("0", "false", "no", "off")


def count_shoots(root: Path) -> int:
    """Shoot folders with a _web/ subfolder, by the same rules archive.scan uses."""
    n = 0
    for year_dir in root.iterdir():
        if not year_dir.is_dir() or year_dir.name.startswith(".") or not archive.YEAR_RE.match(year_dir.name):
            continue
        for shoot_dir in year_dir.iterdir():
            if shoot_dir.is_dir() and not shoot_dir.name.startswith(".") and (shoot_dir / archive.WEB_DIR).is_dir():
                n += 1
    return n


def skip_reason(environ: dict | None = None) -> str | None:
    """Why this run must not touch the target, or None if the source looks real."""
    env = os.environ if environ is None else environ
    source = (env.get("PHOTO_SOURCE_ROOT") or "").strip()
    if not source:
        return None  # let the CLI report the missing setting as a config problem
    root = Path(source).expanduser()
    try:
        if not root.is_dir():
            return f"source {root} is missing (archive drive not plugged in?)"
        if _truthy(env.get("PHOTO_REQUIRE_MOUNT"), True):
            mount = Path((env.get("PHOTO_MOUNT_POINT") or "").strip() or root).expanduser()
            if not os.path.ismount(mount):
                return (f"{mount} is not a mount point (archive drive not mounted?); "
                        "set PHOTO_REQUIRE_MOUNT=0 to sync from a plain folder")
        if _flag(env.get("PHOTO_REQUIRE_SENTINEL", "1")) and not (root / sync.SENTINEL).is_file():
            return (f"{root}/{sync.SENTINEL} not found (archive drive not plugged in?); "
                    "create that empty file at the archive root to mark the real drive")
        shoots = count_shoots(root)
    except OSError as exc:  # drive yanked mid-scan, permission denied, ...
        return f"source {root} is unreadable ({exc.strerror or exc})"
    if shoots == 0:
        return f"source {root} has no <YEAR>/<shoot>/_web/ folders"
    return None


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else list(argv)
    if "-h" in argv or "--help" in argv:
        return cli.main(argv)
    # Unattended runs always check the sentinel, before and after the scan.
    os.environ.setdefault("PHOTO_REQUIRE_SENTINEL", "1")
    args, _ = cli.build_parser().parse_known_args(argv)
    if not args.check:
        # Resolve the source exactly as the CLI will: .env fills gaps in the
        # real environment, and --source wins over both.
        env = dict(os.environ)
        load_env_file(args.env_file or Path(cli.__file__).resolve().parent.parent / ".env", env)
        if args.source:
            env["PHOTO_SOURCE_ROOT"] = args.source
        reason = skip_reason(env)
        if reason:
            print(f"Skipping sync: {reason}. Nothing was uploaded or deleted.")
            return 0
    return cli.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
