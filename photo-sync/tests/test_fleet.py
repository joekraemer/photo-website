"""The fleet guard: an unplugged or empty archive drive must never reach a sync."""

import json
import shutil

import boto3
import pytest
from moto import mock_aws

from photo_sync import archive, cli, fleet, sync
from photo_sync.config import Config
from photo_sync.sample_archive import build, make_jpeg
from photo_sync.targets import LocalTarget


@pytest.fixture
def no_sync(monkeypatch):
    """Fail the test if the guard lets a run through to the real CLI."""
    calls = []
    monkeypatch.setattr(cli, "main", lambda argv=None: calls.append(argv) or 0)
    return calls


@pytest.fixture
def env(monkeypatch, tmp_path):
    for key in ("PHOTO_SOURCE_ROOT", "PHOTO_MOUNT_POINT", "PHOTO_REQUIRE_MOUNT", "TARGET",
                "LOCAL_TARGET_DIR", "S3_BUCKET", "S3_KEY_ID", "S3_APP_KEY", "S3_ENDPOINT_URL",
                "PHOTO_ALLOW_SHRINK"):
        monkeypatch.delenv(key, raising=False)
    # fleet.main sets this default on os.environ; pin it so monkeypatch restores it.
    monkeypatch.setenv("PHOTO_REQUIRE_SENTINEL", "1")
    # Never pick up the developer's real photo-sync/.env.
    empty = tmp_path / "empty.env"
    empty.write_text("")
    return ["--env-file", str(empty)]


def test_missing_source_skips(env, no_sync, monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("PHOTO_SOURCE_ROOT", str(tmp_path / "not-plugged-in"))
    assert fleet.main(env + ["--prune"]) == 0
    assert no_sync == []
    assert "Skipping sync" in capsys.readouterr().out


def test_source_that_is_a_file_skips(env, no_sync, monkeypatch, tmp_path):
    f = tmp_path / "file"
    f.write_text("x")
    monkeypatch.setenv("PHOTO_SOURCE_ROOT", str(f))
    assert fleet.main(env + ["--prune"]) == 0
    assert no_sync == []


def test_not_a_mount_skips(env, no_sync, monkeypatch, tmp_path, capsys):
    src = build(tmp_path / "archive")  # real shoots, but a plain folder
    monkeypatch.setenv("PHOTO_SOURCE_ROOT", str(src))
    assert fleet.main(env + ["--prune"]) == 0
    assert no_sync == []
    assert "not a mount point" in capsys.readouterr().out


def test_mount_point_variable_is_checked(env, no_sync, monkeypatch, tmp_path):
    src = build(tmp_path / "archive")
    monkeypatch.setenv("PHOTO_SOURCE_ROOT", str(src))
    monkeypatch.setenv("PHOTO_MOUNT_POINT", "/")  # always a mount
    assert fleet.main(env + ["--prune"]) == 0
    assert len(no_sync) == 1


@pytest.mark.parametrize("layout", [
    [],                                  # empty mount point / stale /Volumes dir
    ["2024"],                            # year folder, no shoots
    ["2024/06-15-2024 Greece"],          # shoot without _web/
    ["Photos/06-15-2024 Greece/_web"],   # not under a YYYY folder
    [".Trashes/x/_web"],                 # macOS metadata only
])
def test_zero_shoots_skips(env, no_sync, monkeypatch, tmp_path, layout, capsys):
    root = tmp_path / "drive"
    root.mkdir()
    (root / ".photo-archive").write_text("")
    for rel in layout:
        (root / rel).mkdir(parents=True)
    monkeypatch.setenv("PHOTO_SOURCE_ROOT", str(root))
    monkeypatch.setenv("PHOTO_REQUIRE_MOUNT", "0")
    assert fleet.main(env + ["--prune"]) == 0
    assert no_sync == []
    assert "no <YEAR>/<shoot>/_web/ folders" in capsys.readouterr().out


def test_real_archive_runs(env, no_sync, monkeypatch, tmp_path):
    src = build(tmp_path / "archive")
    monkeypatch.setenv("PHOTO_SOURCE_ROOT", str(src))
    monkeypatch.setenv("PHOTO_REQUIRE_MOUNT", "0")
    assert fleet.main(env + ["--prune"]) == 0
    assert no_sync == [env + ["--prune"]]


def test_source_flag_wins_over_env(env, no_sync, monkeypatch, tmp_path):
    src = build(tmp_path / "archive")
    monkeypatch.setenv("PHOTO_SOURCE_ROOT", str(src))
    monkeypatch.setenv("PHOTO_REQUIRE_MOUNT", "0")
    argv = env + ["--prune", f"--source={tmp_path / 'gone'}"]
    assert fleet.main(argv) == 0
    assert no_sync == []


def test_check_is_passed_through(env, no_sync, monkeypatch, tmp_path):
    monkeypatch.setenv("PHOTO_SOURCE_ROOT", str(tmp_path / "gone"))
    assert fleet.main(env + ["--check"]) == 0
    assert no_sync == [env + ["--check"]]


@mock_aws
def test_unplugged_drive_leaves_bucket_untouched(env, monkeypatch, tmp_path):
    """End to end against a fake B2: prune with the drive gone deletes nothing."""
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="photos")
    manifest = json.dumps({"version": 1, "albums": [{"slug": "a"}]}).encode()
    s3.put_object(Bucket="photos", Key="photos.json", Body=manifest)
    s3.put_object(Bucket="photos", Key="photos/a/p-12345678-large.webp", Body=b"img")

    root = tmp_path / "drive"
    root.mkdir()  # the mount point exists but the drive is not in it
    monkeypatch.setenv("PHOTO_SOURCE_ROOT", str(root))
    monkeypatch.setenv("PHOTO_REQUIRE_MOUNT", "0")
    monkeypatch.setenv("TARGET", "s3")
    monkeypatch.setenv("S3_BUCKET", "photos")
    monkeypatch.setenv("S3_KEY_ID", "testing")
    monkeypatch.setenv("S3_APP_KEY", "testing")

    assert fleet.main(env + ["--prune"]) == 0
    keys = sorted(o["Key"] for o in s3.list_objects_v2(Bucket="photos")["Contents"])
    assert keys == ["photos.json", "photos/a/p-12345678-large.webp"]
    assert s3.get_object(Bucket="photos", Key="photos.json")["Body"].read() == manifest

    # Second layer: even the unguarded CLI (no sentinel check, plain folder)
    # now refuses to publish the empty source over a non-empty site.
    monkeypatch.setenv("PHOTO_REQUIRE_SENTINEL", "0")
    assert cli.main(env + ["--prune"]) == 1
    keys = sorted(o["Key"] for o in s3.list_objects_v2(Bucket="photos")["Contents"])
    assert keys == ["photos.json", "photos/a/p-12345678-large.webp"]
    assert s3.get_object(Bucket="photos", Key="photos.json")["Body"].read() == manifest

    # Control: with the shrink guard overridden it wipes the site, which is
    # exactly what both guards exist to prevent.
    monkeypatch.setenv("PHOTO_ALLOW_SHRINK", "1")
    assert cli.main(env + ["--prune"]) == 0
    keys = sorted(o["Key"] for o in s3.list_objects_v2(Bucket="photos")["Contents"])
    assert keys == ["photos.json"]
    wiped = json.loads(s3.get_object(Bucket="photos", Key="photos.json")["Body"].read())
    assert wiped["albums"] == []


# --- sentinel -----------------------------------------------------------------

def test_missing_sentinel_skips(env, no_sync, monkeypatch, tmp_path, capsys):
    src = build(tmp_path / "archive")
    (src / ".photo-archive").unlink()
    monkeypatch.setenv("PHOTO_SOURCE_ROOT", str(src))
    monkeypatch.setenv("PHOTO_REQUIRE_MOUNT", "0")
    assert fleet.main(env + ["--prune"]) == 0
    assert no_sync == []
    assert ".photo-archive not found" in capsys.readouterr().out


def _cfg(src, out, **kw):
    e = {"PHOTO_SOURCE_ROOT": str(src), "TARGET": "local", "LOCAL_TARGET_DIR": str(out),
         "PHOTO_REQUIRE_SENTINEL": "1"}
    e.update(kw)
    return Config.from_env(e)


def _snapshot(out):
    return {p.relative_to(out): p.read_bytes() for p in out.rglob("*") if p.is_file()}


def test_sentinel_rechecked_after_scan(tmp_path, monkeypatch):
    """The drive is pulled between the scan and the writes: nothing is published."""
    src, out = build(tmp_path / "archive"), tmp_path / "out"
    sync.run(_cfg(src, out), LocalTarget(out), log=lambda m: None)
    before = _snapshot(out)

    real_scan = archive.scan

    def scan_then_unplug(root, errors=None):
        found = real_scan(root, errors)
        (src / ".photo-archive").unlink()
        shutil.rmtree(src / "2024")
        return found

    monkeypatch.setattr(archive, "scan", scan_then_unplug)
    result = sync.run(_cfg(src, out), LocalTarget(out), log=lambda m: None, prune=True)
    assert result.skipped and ".photo-archive" in result.skipped
    assert not result.manifest_written and not result.deleted
    assert _snapshot(out) == before


def test_sentinel_not_required_by_default(tmp_path):
    src, out = build(tmp_path / "archive"), tmp_path / "out"
    (src / ".photo-archive").unlink()
    result = sync.run(_cfg(src, out, PHOTO_REQUIRE_SENTINEL=""), LocalTarget(out), log=lambda m: None)
    assert result.skipped is None and result.manifest_written


# --- shrink guard ---------------------------------------------------------------

def test_removed_year_is_not_pruned(tmp_path, capsys):
    """Reviewer repro: sync, move a year folder away, re-sync with --prune."""
    src, out = build(tmp_path / "archive"), tmp_path / "out"
    args = ["--source", str(src), "--target", "local", "--local-dir", str(out),
            "--env-file", str(tmp_path / "none.env")]
    assert cli.main(args) == 0
    before = _snapshot(out)
    shutil.move(src / "2024", tmp_path / "2024-moved-aside")
    capsys.readouterr()

    assert cli.main(args + ["--prune"]) == 1  # non-zero: fleet health flags it
    text = capsys.readouterr().out
    assert "ERROR: refusing to publish a smaller site: year(s) 2024 disappeared" in text
    assert "manifest held back" in text and "0 orphans deleted" not in text
    assert _snapshot(out) == before  # manifest unchanged, nothing pruned


def test_allow_shrink_publishes_and_prunes(tmp_path):
    src, out = build(tmp_path / "archive"), tmp_path / "out"
    sync.run(_cfg(src, out), LocalTarget(out), log=lambda m: None)
    shutil.rmtree(src / "2024")
    result = sync.run(_cfg(src, out, PHOTO_ALLOW_SHRINK="1"), LocalTarget(out),
                      log=lambda m: None, prune=True)
    assert result.blocked is None and result.manifest_written
    assert len(result.deleted) == 9
    assert [a["year"] for a in result.manifest["albums"]] == [2023, 2023]


@pytest.mark.parametrize("old_albums,old_photos,new_albums,new_photos,blocked", [
    (10, 100, 9, 90, False),   # 10% drop: fine
    (10, 100, 8, 80, False),   # exactly 20%: fine
    (10, 100, 7, 100, True),   # albums -30%
    (10, 100, 10, 79, True),   # photos -21%
    (10, 100, 12, 130, False),  # growth
])
def test_shrink_thresholds(old_albums, old_photos, new_albums, new_photos, blocked):
    def manifest(n_albums, n_photos):
        per = [n_photos // n_albums] * n_albums
        per[0] += n_photos - sum(per)
        return {"albums": [{"slug": f"a{i}", "year": 2024, "photos": [{}] * k}
                           for i, k in enumerate(per)]}
    reason = sync.shrink_reason(manifest(old_albums, old_photos), manifest(new_albums, new_photos))
    assert bool(reason) is blocked


def test_hiding_an_album_is_not_a_shrink(tmp_path):
    src, out = build(tmp_path / "archive"), tmp_path / "out"
    sync.run(_cfg(src, out), LocalTarget(out), log=lambda m: None)
    (src / "2024" / "06-15-2024 Greece" / "album.md").write_text("---\nhidden: true\n---\n")
    result = sync.run(_cfg(src, out), LocalTarget(out), log=lambda m: None)
    assert result.blocked is None and result.manifest_written
    assert "2024-06-15-greece" not in [a["slug"] for a in result.manifest["albums"]]


# --- per-file errors keep the published manifest --------------------------------

def test_errors_keep_previous_manifest(tmp_path):
    src, out = build(tmp_path / "archive"), tmp_path / "out"
    sync.run(_cfg(src, out), LocalTarget(out), log=lambda m: None)
    published = (out / "photos.json").read_bytes()
    web = src / "2024" / "06-15-2024 Greece" / "_web"
    (web / "DSC04351.jpg").write_bytes(b"truncated")
    make_jpeg(web / "NEW.jpg", label="new photo")

    result = sync.run(_cfg(src, out), LocalTarget(out), log=lambda m: None, prune=True)
    assert result.errors and not result.manifest_written and not result.deleted
    assert (out / "photos.json").read_bytes() == published
    assert result.uploaded_photos == 1  # the new photo's images still went up
    assert any(k.startswith("photos/2024-06-15-greece/new-") for k in map(str, _snapshot(out)))


def test_errors_on_first_sync_still_publish(tmp_path):
    """With no previous manifest there is nothing to lose: publish the rest."""
    src, out = build(tmp_path / "archive"), tmp_path / "out"
    (src / "2024" / "06-15-2024 Greece" / "_web" / "broken.jpg").write_bytes(b"x")
    result = sync.run(_cfg(src, out), LocalTarget(out), log=lambda m: None)
    assert result.errors and result.manifest_written
