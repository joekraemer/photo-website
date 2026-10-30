"""The export cache (issue #53): an unchanged export is not read again, and
anything doubtful (changed file, missing renders, bad cache) means a full read."""

import json
import os
import pathlib

import pytest

from photo_sync import cli, imaging, sync
from photo_sync.cache import ExportCache, default_path
from photo_sync.config import Config
from photo_sync.sample_archive import build, make_jpeg
from photo_sync.targets import LocalTarget


@pytest.fixture
def src(tmp_path):
    return build(tmp_path / "archive")


@pytest.fixture
def out(tmp_path):
    return tmp_path / "out"


@pytest.fixture
def cache_file(tmp_path):
    return tmp_path / "cache.json"


@pytest.fixture
def reads(monkeypatch):
    """Paths of every _web/ export whose bytes are read (or opened by Pillow)."""
    seen: list[str] = []
    real_read_bytes = pathlib.Path.read_bytes
    real_open = imaging.open_image

    def read_bytes(self):
        if "_web" in self.parts:
            seen.append(self.name)
        return real_read_bytes(self)

    def open_image(source):
        if isinstance(source, (str, os.PathLike)) and "_web" in pathlib.Path(source).parts:
            seen.append(pathlib.Path(source).name)
        return real_open(source)

    monkeypatch.setattr(pathlib.Path, "read_bytes", read_bytes)
    monkeypatch.setattr(imaging, "open_image", open_image)
    return seen


def cfg_for(src, out, **env):
    base = {"PHOTO_SOURCE_ROOT": str(src), "TARGET": "local", "LOCAL_TARGET_DIR": str(out)}
    base.update(env)
    return Config.from_env(base)


def sync_once(src, out, cache_file, logs=None, **env):
    log = logs.append if logs is not None else (lambda _m: None)
    return sync.run(cfg_for(src, out, **env), LocalTarget(out), log=log, cache_path=cache_file)


def exports(src):
    return sorted(p for p in src.rglob("_web/*") if p.is_file())


def same_site(a, b):
    strip = sync._strip_volatile
    return strip(a.manifest) == strip(b.manifest)


def test_second_run_reads_no_export(src, out, cache_file, reads):
    first = sync_once(src, out, cache_file)
    assert len(reads) == len(exports(src)) - 1  # all but the hidden album's
    reads.clear()

    second = sync_once(src, out, cache_file)
    assert reads == []
    assert second.skipped_photos == second.photos == first.photos
    assert second.uploaded_objects == 0 and not second.manifest_written
    assert same_site(first, second)


def test_cached_manifest_matches_a_fresh_read(src, out, cache_file, tmp_path):
    """A cache hit publishes exactly what a full read would."""
    sync_once(src, out, cache_file)
    cached = sync_once(src, out, cache_file)
    uncached = sync.run(cfg_for(src, out), LocalTarget(out), log=lambda _m: None)
    assert json.dumps(sync._strip_volatile(cached.manifest), sort_keys=True) == \
        json.dumps(sync._strip_volatile(uncached.manifest), sort_keys=True)


def test_changed_export_is_read_again(src, out, cache_file, reads):
    sync_once(src, out, cache_file)
    photo = src / "2024/06-15-2024 Greece/_web/DSC04639.jpg"
    old = photo.stat()
    make_jpeg(photo, color=(200, 10, 10))  # new content, new size
    os.utime(photo, ns=(old.st_atime_ns, old.st_mtime_ns + 5_000_000_000))
    reads.clear()

    result = sync_once(src, out, cache_file)
    assert reads == ["DSC04639.jpg"]
    assert result.uploaded_photos == 1  # new digest, new renders


def test_same_size_new_mtime_is_read_again(src, out, cache_file, reads):
    """Size alone is not trusted: a touched file is re-read (and, with the
    same bytes, reused without re-rendering)."""
    sync_once(src, out, cache_file)
    photo = src / "2023/Road trip/_web/IMG_0001.jpg"
    st = photo.stat()
    os.utime(photo, ns=(st.st_atime_ns, st.st_mtime_ns + 1))
    reads.clear()

    result = sync_once(src, out, cache_file)
    assert reads.count("IMG_0001.jpg") >= 1 and set(reads) == {"IMG_0001.jpg"}
    assert result.uploaded_photos == 0
    reads.clear()
    sync_once(src, out, cache_file)
    assert reads == []  # and cached again under the new mtime


def test_missing_renders_on_target_force_a_full_read(src, out, cache_file, reads):
    first = sync_once(src, out, cache_file)
    photo = first.manifest["albums"][0]["photos"][0]
    (out / photo["sizes"]["large"]).unlink()
    reads.clear()

    result = sync_once(src, out, cache_file)
    assert len(reads) >= 1
    assert result.uploaded_photos == 1
    assert (out / photo["sizes"]["large"]).is_file()


def test_render_settings_change_invalidates_the_cache(src, out, cache_file, reads):
    sync_once(src, out, cache_file)
    reads.clear()
    result = sync_once(src, out, cache_file, WATERMARK_TEXT="@someone_else")
    assert len(reads) >= result.photos > 0
    assert result.uploaded_photos == result.photos


def test_missing_cache_is_a_full_read(src, out, cache_file, reads):
    first = sync_once(src, out, cache_file)
    cache_file.unlink()
    reads.clear()
    second = sync_once(src, out, cache_file)
    assert len(reads) == len(exports(src)) - 1
    assert second.uploaded_photos == 0  # renders were still on the target
    assert same_site(first, second)
    assert cache_file.is_file()


@pytest.mark.parametrize("body", [
    "{not json",
    "[]",
    json.dumps({"version": 999, "entries": {}}),
])
def test_corrupt_cache_is_a_full_read(src, out, cache_file, reads, body):
    first = sync_once(src, out, cache_file)
    cache_file.write_text(body, encoding="utf-8")
    reads.clear()
    logs = []
    second = sync_once(src, out, cache_file, logs)
    assert len(reads) == len(exports(src)) - 1
    assert same_site(first, second)
    assert any("cache" in m and "Warning" in m for m in logs)
    # ... and the run writes a good cache again.
    reads.clear()
    sync_once(src, out, cache_file)
    assert reads == []


@pytest.mark.parametrize("field,value", [
    ("digest", "short"),
    ("exif", "nope"),
    ("mtime_ns", 1.5),
])
def test_malformed_entry_is_a_full_read_of_that_file(src, out, cache_file, reads, field, value):
    first = sync_once(src, out, cache_file)
    data = json.loads(cache_file.read_text(encoding="utf-8"))
    rel = "2023/Road trip/_web/IMG_0001.jpg"
    data["entries"][rel][field] = value
    cache_file.write_text(json.dumps(data), encoding="utf-8")
    reads.clear()
    second = sync_once(src, out, cache_file)
    assert set(reads) == {"IMG_0001.jpg"}
    assert same_site(first, second)


def test_unwritable_cache_only_warns(src, out, tmp_path):
    blocker = tmp_path / "file"
    blocker.write_text("x")
    logs = []
    result = sync_once(src, out, blocker / "cache.json", logs)
    assert result.photos > 0 and not result.errors
    assert any("could not write photo-sync cache" in m for m in logs)


def test_no_cache_path_means_no_cache(src, out, reads):
    sync.run(cfg_for(src, out), LocalTarget(out), log=lambda _m: None)
    reads.clear()
    sync.run(cfg_for(src, out), LocalTarget(out), log=lambda _m: None)
    assert len(reads) == len(exports(src)) - 1


def test_removed_exports_drop_out_of_the_cache(src, out, cache_file):
    sync_once(src, out, cache_file)
    (src / "2023/Road trip/_web/IMG_0001.jpg").unlink()
    sync_once(src, out, cache_file, PHOTO_ALLOW_SHRINK="1")
    entries = json.loads(cache_file.read_text(encoding="utf-8"))["entries"]
    assert "2023/Road trip/_web/IMG_0001.jpg" not in entries


def test_cli_uses_photo_cache_file(src, out, tmp_path, monkeypatch, reads):
    target = tmp_path / "state" / "c.json"
    monkeypatch.setenv("PHOTO_CACHE_FILE", str(target))
    argv = ["--source", str(src), "--target", "local", "--local-dir", str(out),
            "--env-file", str(tmp_path / "none.env")]
    assert cli.main(argv) == 0
    assert target.is_file()
    reads.clear()
    assert cli.main(argv) == 0
    assert reads == []


def test_default_path(monkeypatch, tmp_path):
    monkeypatch.delenv("PHOTO_CACHE_FILE", raising=False)
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    assert default_path() == tmp_path / "photo-sync" / "photo-sync-cache.json"
    monkeypatch.delenv("XDG_CACHE_HOME")
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    assert default_path() == tmp_path / "home" / ".cache" / "photo-sync" / "photo-sync-cache.json"


def test_lookup_requires_every_key_to_match():
    c = ExportCache(None, b"fp")
    entry = c.entry(size=10, mtime_ns=20, digest="a" * 64, exif={}, description=None,
                    rating=None, width=1, height=1, placeholder={})
    c._old = {"x": entry}
    assert c.lookup("x", 10, 20) == entry
    assert c.lookup("x", 11, 20) is None
    assert c.lookup("x", 10, 21) is None
    assert c.lookup("y", 10, 20) is None
    assert ExportCache(None, b"other", {"x": entry}).lookup("x", 10, 20) is None
