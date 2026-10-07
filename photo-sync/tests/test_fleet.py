"""The fleet guard: an unplugged or empty archive drive must never reach a sync."""

import json

import boto3
import pytest
from moto import mock_aws

from photo_sync import cli, fleet
from photo_sync.sample_archive import build


@pytest.fixture
def no_sync(monkeypatch):
    """Fail the test if the guard lets a run through to the real CLI."""
    calls = []
    monkeypatch.setattr(cli, "main", lambda argv=None: calls.append(argv) or 0)
    return calls


@pytest.fixture
def env(monkeypatch, tmp_path):
    for key in ("PHOTO_SOURCE_ROOT", "PHOTO_MOUNT_POINT", "PHOTO_REQUIRE_MOUNT", "TARGET",
                "LOCAL_TARGET_DIR", "S3_BUCKET", "S3_KEY_ID", "S3_APP_KEY", "S3_ENDPOINT_URL"):
        monkeypatch.delenv(key, raising=False)
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

    # Control: the unguarded CLI on the same empty source wipes the site, which
    # is exactly what the guard exists to prevent.
    assert cli.main(env + ["--prune"]) == 0
    keys = sorted(o["Key"] for o in s3.list_objects_v2(Bucket="photos")["Contents"])
    assert keys == ["photos.json"]
    wiped = json.loads(s3.get_object(Bucket="photos", Key="photos.json")["Body"].read())
    assert wiped["albums"] == []
