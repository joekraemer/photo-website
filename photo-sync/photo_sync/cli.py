"""Command line entry point: `python -m photo_sync [--check] [--prune]`."""

from __future__ import annotations

import argparse
import fcntl
import os
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

from . import sync
from .config import Config, ConfigError, load_env_file
from .targets import make_target


def default_lock_path() -> Path:
    return Path(os.environ.get("PHOTO_LOCK_FILE") or Path(tempfile.gettempdir()) / "photo-sync.lock")


class AlreadyRunning(RuntimeError):
    pass


@contextmanager
def run_lock(path: Path):
    """Hold an exclusive flock on `path` for the duration of a sync, so two
    syncs (the daily loop and a manual run, say) never write the same target
    at once. The kernel drops the lock when the process exits, even on a
    crash, so a stale lock file never blocks later runs."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fh = open(path, "a+", encoding="utf-8")
    try:
        try:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            fh.seek(0)
            holder = fh.read().strip()
            raise AlreadyRunning(holder) from None
        fh.seek(0)
        fh.truncate()
        fh.write(f"{os.getpid()}\n")
        fh.flush()
        yield
    finally:
        fh.close()  # releases the lock


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m photo_sync",
        description="Render <ROOT>/<YEAR>/<MM-DD-YYYY Name>/_web/* into web sizes "
                    "and publish them plus photos.json to a local folder or B2. "
                    "A bad file (unreadable image, broken album.md) is skipped and reported; "
                    "the rest still publishes and the exit code is 1. "
                    "Only one sync runs at a time (see PHOTO_LOCK_FILE).",
    )
    p.add_argument("--check", action="store_true",
                   help="report naming issues and counts; write and upload nothing")
    p.add_argument("--prune", action="store_true",
                   help="delete orphaned objects under photos/ on the target (objects of albums marked hidden are always deleted, with or without --prune)")
    p.add_argument("--env-file", type=Path, default=None,
                   help="env file to load (default: photo-sync/.env if present)")
    p.add_argument("--source", help="override PHOTO_SOURCE_ROOT")
    p.add_argument("--target", choices=["local", "s3"], help="override TARGET")
    p.add_argument("--local-dir", help="override LOCAL_TARGET_DIR")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    env_file = args.env_file or Path(__file__).resolve().parent.parent / ".env"
    load_env_file(env_file)
    try:
        cfg = Config.from_env(
            require_target=not args.check,
            PHOTO_SOURCE_ROOT=args.source, TARGET=args.target, LOCAL_TARGET_DIR=args.local_dir,
        )
    except ConfigError as exc:
        print(f"Config error: {exc}", file=sys.stderr)
        return 2
    try:
        if args.check:
            result = sync.run(cfg, None, check=True)
        else:
            lock = default_lock_path()
            try:
                with run_lock(lock):
                    target = make_target(cfg)
                    print(f"Syncing {cfg.source_root} -> {target.describe()}")
                    result = sync.run(cfg, target, prune=args.prune)
            except AlreadyRunning as exc:
                who = f" (pid {exc})" if str(exc) else ""
                print(f"Another photo-sync run is already in progress{who}, holding {lock}. "
                      "Exiting without changes; the next run will pick up anything new.")
                return 0
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    return 1 if result.errors or result.blocked else 0
