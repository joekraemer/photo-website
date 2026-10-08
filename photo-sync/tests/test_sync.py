import json
from pathlib import Path

import boto3
import pytest
from moto import mock_aws
from PIL import Image

from photo_sync import archive, sync
from photo_sync.cli import main
from photo_sync.config import Config, ConfigError, load_env_file
from photo_sync.imaging import format_shutter
from photo_sync.sample_archive import build, make_jpeg
from botocore.exceptions import ClientError

from photo_sync.targets import LocalTarget, S3Target


def quiet(_msg):
    pass


@pytest.fixture
def src(tmp_path):
    return build(tmp_path / "archive")


@pytest.fixture
def out(tmp_path):
    return tmp_path / "out"


def local_cfg(src, out, **kw):
    env = {"PHOTO_SOURCE_ROOT": str(src), "TARGET": "local", "LOCAL_TARGET_DIR": str(out)}
    env.update(kw)
    return Config.from_env(env)


def run_local(src, out, **kw):
    cfg = local_cfg(src, out)
    return sync.run(cfg, LocalTarget(out), log=quiet, **kw)


# --- naming ---------------------------------------------------------------

@pytest.mark.parametrize("name,year,ok", [
    ("06-15-2024 Greece", 2024, True),
    ("06-15-2024 Greece Islands", 2024, True),
    ("06-15-2024_Greece_Islands", 2024, False),   # underscores
    ("06-15-2024_Greece", 2024, False),
    ("06-15-2024-Greece", 2024, False),
    ("06-15-2024  Greece", 2024, False),       # two spaces
    ("06-15-2024 Greece ", 2024, False),       # trailing space
    ("06-15-2024 ", 2024, False),
    ("2024-06-15 Greece", 2024, False),       # wrong pattern
    ("Greece", 2024, False),
    ("02-30-2024 Leap", 2024, False),         # impossible date
    ("13-01-2024 Month", 2024, False),
    ("06-15-2023 Greece", 2024, False),       # year differs from parent
    ("06-15-2024", 2024, False),              # missing name
])
def test_parse_shoot_name(name, year, ok):
    d, display, problems = archive.parse_shoot_name(name, year)
    assert (not problems) is ok
    if ok:
        assert d.isoformat() == "2024-06-15"
        assert "_" not in display


def test_scan_flags_but_still_publishes(src, out):
    _, issues = archive.scan(src)
    assert [(i.path, "does not match" in i.problem) for i in issues] == [("2023/Road trip", True)]
    result = run_local(src, out)
    road = next(a for a in result.manifest["albums"] if a["slug"] == "road-trip")
    assert road["title"] == "Road trip"
    assert road["date"] == "2023-08-20"  # earliest EXIF DateTimeOriginal


def test_underscore_separator_flagged_but_published(tmp_path):
    root = tmp_path / "a"
    make_jpeg(root / "2023" / "10-02-2023_South_Korea" / "_web" / "a.jpg", size=(300, 200))
    _, issues = archive.scan(root)
    assert [i.path for i in issues] == ["2023/10-02-2023_South_Korea"]
    assert "single space" in issues[0].problem
    result = run_local(root, tmp_path / "out")
    assert [a["slug"] for a in result.manifest["albums"]] == ["10-02-2023-south-korea"]


def test_year_mismatch_and_impossible_date_flagged(tmp_path):
    root = tmp_path / "a"
    make_jpeg(root / "2024" / "06-15-2023 Wrong year" / "_web" / "a.jpg", size=(300, 200))
    make_jpeg(root / "2024" / "02-31-2024 Bad date" / "_web" / "b.jpg", size=(300, 200))
    _, issues = archive.scan(root)
    problems = sorted(i.problem for i in issues)
    assert any("impossible date" in p for p in problems)
    assert any("does not match parent folder 2024" in p for p in problems)


def test_naming_report_printed(src, out):
    lines = []
    sync.run(local_cfg(src, out), LocalTarget(out), log=lines.append)
    assert lines[0].startswith("Naming issues:")
    assert "2023/Road trip" in lines[0]


# --- --check --------------------------------------------------------------

def test_check_makes_no_writes(src, out, capsys):
    before = sorted(p for p in src.rglob("*"))
    rc = main(["--check", "--source", str(src), "--env-file", str(src / "none.env")])
    assert rc == 0
    assert not out.exists()
    assert sorted(p for p in src.rglob("*")) == before
    text = capsys.readouterr().out
    assert "Naming issues:" in text
    assert "3 albums, 1 hidden, 6 photos" in text


def test_check_never_touches_target(src):
    class Exploding:
        def __getattr__(self, name):
            raise AssertionError(f"target.{name} called during --check")
    cfg = Config.from_env({"PHOTO_SOURCE_ROOT": str(src)}, require_target=False)
    sync.run(cfg, Exploding(), check=True, log=quiet)


# --- local end to end -----------------------------------------------------

def test_local_end_to_end(src, out):
    result = run_local(src, out)
    m = json.loads((out / "photos.json").read_text())
    assert m["version"] == 1 and m["base_url"] == "" and m["generated_at"].endswith("Z")
    slugs = [a["slug"] for a in m["albums"]]
    assert slugs == ["2024-06-15-greece", "2023-10-02-south-korea", "road-trip"]  # newest first
    assert "secret" not in json.dumps(m)  # hidden album excluded
    assert not list(out.rglob("*secret*"))

    greece = m["albums"][0]
    assert greece["title"] == "Greece"
    assert greece["intro"] == "Island hopping in the Cyclades."
    assert greece["year"] == 2024 and greece["date"] == "2024-06-15"
    ids = [p["id"] for p in greece["photos"]]
    assert ids[0].startswith("dsc04012-hdr-") and ids[1].startswith("dsc04351-")  # by EXIF time
    assert greece["cover"].startswith("dsc04639-")
    assert result.photos == 6

    for album in m["albums"]:
        for photo in album["photos"]:
            assert set(photo) == {"id", "alt", "width", "height", "aspect", "sizes", "color", "exif"}
            expected_edges = {"thumb": 500, "medium": 1600, "large": 2560}
            for size, key in photo["sizes"].items():
                assert key.startswith(f"photos/{album['slug']}/") and key.endswith(f"-{size}.webp")
                path = out / key
                with Image.open(path) as im:
                    assert im.format == "WEBP"
                    assert not im.getexif()
                    assert "exif" not in im.info and "icc_profile" not in im.info and "xmp" not in im.info
                    assert max(im.size) <= expected_edges[size]
                    if size == "large":
                        assert (im.width, im.height) == (photo["width"], photo["height"])
                raw = path.read_bytes()
                assert b"Exif" not in raw and b"XMP" not in raw and b"GPS" not in raw
            assert photo["aspect"] == round(photo["width"] / photo["height"], 4)


def test_sizes_and_no_upscale(src, out):
    run_local(src, out)
    m = json.loads((out / "photos.json").read_text())
    greece = m["albums"][0]
    tall = next(p for p in greece["photos"] if p["id"].startswith("dsc04639-"))
    with Image.open(out / tall["sizes"]["thumb"]) as im:
        assert im.size == (333, 500)
    with Image.open(out / tall["sizes"]["medium"]) as im:
        assert im.size == (1067, 1600)
    assert (tall["width"], tall["height"]) == (1707, 2560)
    korea = m["albums"][1]
    small = next(p for p in korea["photos"] if p["id"].startswith("dsc00021-"))  # 1200x800 source
    assert (small["width"], small["height"]) == (1200, 800)
    with Image.open(out / small["sizes"]["medium"]) as im:
        assert im.size == (1200, 800)


def test_exif_fields_and_omissions(src, out):
    run_local(src, out)
    m = json.loads((out / "photos.json").read_text())
    by_id = {p["id"].rsplit("-", 1)[0]: p for a in m["albums"] for p in a["photos"]}
    assert by_id["dsc04351"]["exif"] == {
        "camera": "ILCE-6400", "body_name": "Sony α6400", "lens": "E 35mm F1.8 OSS",
        "focal_length": "35mm",
        "aperture": "f/1.8", "shutter": "1/250s", "iso": 100, "taken_at": "2024-06-15T09:00:00",
    }
    assert by_id["dsc04639"]["exif"]["shutter"] == "2.5s"
    assert by_id["dsc04639"]["exif"]["iso"] == 3200
    no_time = by_id["dsc00085"]["exif"]
    assert "taken_at" not in no_time and "lens" not in no_time
    korea = next(a for a in m["albums"] if a["slug"] == "2023-10-02-south-korea")
    assert [p["id"].rsplit("-", 1)[0] for p in korea["photos"]] == ["dsc00021", "dsc00085"]


def test_orientation_applied(tmp_path):
    root = tmp_path / "a"
    make_jpeg(root / "2024" / "01-02-2024 Rotated" / "_web" / "r.jpg", size=(3000, 2000), orientation=6)
    out = tmp_path / "out"
    first = run_local(root, out)
    p = first.manifest["albums"][0]["photos"][0]
    assert (p["width"], p["height"]) == (1707, 2560)
    second = run_local(root, out)  # skipped path must report the same oriented size
    assert second.uploaded_photos == 0
    q = json.loads((out / "photos.json").read_text())["albums"][0]["photos"][0]
    assert (q["width"], q["height"]) == (1707, 2560)


@pytest.mark.parametrize("seconds,text", [
    (1 / 250, "1/250s"), (1 / 8000, "1/8000s"), (0.3, "0.3s"), (1 / 3, "1/3s"), (2.5, "2.5s"), (30, "30s"), (1, "1s"),
])
def test_format_shutter(seconds, text):
    assert format_shutter(seconds) == text


# --- idempotency, change, prune ------------------------------------------

def test_second_run_uploads_nothing(src, out):
    run_local(src, out)
    mtimes = {p: p.stat().st_mtime_ns for p in out.rglob("*") if p.is_file()}
    again = run_local(src, out)
    assert again.uploaded_objects == 0 and again.uploaded_photos == 0
    assert again.skipped_photos == 6 and not again.manifest_written
    assert {p: p.stat().st_mtime_ns for p in out.rglob("*") if p.is_file()} == mtimes


def test_changed_export_gets_new_hash_and_prune(src, out):
    run_local(src, out)
    target = src / "2024" / "06-15-2024 Greece" / "_web" / "DSC04351.jpg"
    old = {p.name for p in out.rglob("dsc04351-*")}
    make_jpeg(target, color=(10, 200, 10), taken_at="2024:06:15 09:00:00")  # re-export

    result = run_local(src, out)
    assert result.uploaded_photos == 1 and result.manifest_written
    new = {p.name for p in out.rglob("dsc04351-*")} - old
    assert len(new) == 3
    assert sorted(Path(k).name for k in result.orphans) == sorted(old)  # reported...
    assert all((out / k).exists() for k in result.orphans)                # ...not deleted

    pruned = run_local(src, out, prune=True)
    assert sorted(Path(k).name for k in pruned.deleted) == sorted(old)
    assert {p.name for p in out.rglob("dsc04351-*")} == new
    assert run_local(src, out).orphans == []


def test_removed_photo_is_orphan(src, out):
    run_local(src, out)
    (src / "2023" / "Road trip" / "_web" / "IMG_0001.jpg").unlink()
    # One album of three is a 33% drop: deliberate here, so allow the shrink.
    cfg = local_cfg(src, out, PHOTO_ALLOW_SHRINK="1")
    result = sync.run(cfg, LocalTarget(out), log=quiet, prune=True)
    assert len(result.deleted) == 3
    assert not (out / "photos" / "road-trip").exists()
    assert "road-trip" not in [a["slug"] for a in result.manifest["albums"]]


# --- album.md -------------------------------------------------------------

def test_album_md_parsing(tmp_path):
    md = tmp_path / "album.md"
    md.write_text("---\ntitle: Cyclades\ncover: B.jpg\nhidden: false\norder: 2\n---\n\nFirst para.\n\nSecond.\n")
    meta = archive.parse_album_md(md)
    assert (meta.title, meta.cover, meta.hidden, meta.order) == ("Cyclades", "B.jpg", False, 2)
    assert meta.intro == "First para.\n\nSecond."

    md.write_text("Just an intro, no frontmatter.\n")
    meta = archive.parse_album_md(md)
    assert meta.title is None and meta.intro == "Just an intro, no frontmatter." and not meta.hidden

    # Date-looking values stay text (and an impossible date doesn't crash).
    md.write_text("---\ntitle: 2024-13-45\n---\n")
    assert archive.parse_album_md(md).title == "2024-13-45"


def test_album_md_order_pins_album(src, out):
    (src / "2023" / "10-02-2023 South Korea" / "album.md").write_text("---\norder: 1\n---\n")
    m = run_local(src, out).manifest
    assert m["albums"][0]["slug"] == "2023-10-02-south-korea"
    assert m["albums"][0]["title"] == "South Korea"  # folder name fallback


def test_missing_cover_warns(src, out):
    (src / "2024" / "06-15-2024 Greece" / "album.md").write_text("---\ncover: nope.jpg\n---\n")
    result = run_local(src, out)
    greece = result.manifest["albums"][0]
    portrait = next(p for p in greece["photos"] if p["height"] > p["width"])
    assert greece["cover"] == portrait["id"]  # automatic pick, not the named file
    assert any("nope.jpg" in w and "automatically" in w for w in result.warnings)
    assert not result.errors


# --- config ---------------------------------------------------------------

def test_config_requires_s3_settings(src):
    with pytest.raises(ConfigError, match="S3_BUCKET"):
        Config.from_env({"PHOTO_SOURCE_ROOT": str(src), "TARGET": "s3"})


def test_config_repr_hides_secrets(src):
    cfg = Config.from_env({"PHOTO_SOURCE_ROOT": str(src), "TARGET": "s3", "S3_BUCKET": "b",
                           "S3_KEY_ID": "KEYID123", "S3_APP_KEY": "SUPERSECRET"})
    assert "SUPERSECRET" not in repr(cfg) and "KEYID123" not in str(cfg)
    assert cfg.watermark_text == "@jak_creative_" and cfg.watermark_opacity == 0.55
    assert cfg.watermark_size == 0.07


def test_env_file_paths_relative_to_file(tmp_path, monkeypatch):
    d = tmp_path / "photo-sync"
    d.mkdir()
    f = d / ".env"
    f.write_text("LOCAL_TARGET_DIR=../public/local-photos\nPHOTO_SOURCE_ROOT=/abs/archive\n")
    monkeypatch.chdir(tmp_path.parent)
    env = {}
    load_env_file(f, env)
    assert env["LOCAL_TARGET_DIR"] == str((tmp_path / "public" / "local-photos").resolve())
    assert env["PHOTO_SOURCE_ROOT"] == "/abs/archive"


def test_env_file_does_not_override(tmp_path):
    f = tmp_path / ".env"
    f.write_text("# c\nA=from_file\nexport B='quoted'\n")
    env = {"A": "from_env"}
    load_env_file(f, env)
    assert env == {"A": "from_env", "B": "quoted"}


# --- s3 target (moto) -----------------------------------------------------

@mock_aws
def test_s3_target(src, monkeypatch):
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    client = boto3.client("s3", region_name="us-east-1",
                          aws_access_key_id="x", aws_secret_access_key="y")
    client.create_bucket(Bucket="photos-test")
    cfg = Config.from_env({
        "PHOTO_SOURCE_ROOT": str(src), "TARGET": "s3", "S3_BUCKET": "photos-test",
        "S3_KEY_ID": "x", "S3_APP_KEY": "y", "PUBLIC_BASE_URL": "https://photos.example.com/",
    })
    target = S3Target("photos-test", client)

    first = sync.run(cfg, target, log=quiet)
    assert first.uploaded_photos == 6
    keys = target.list_keys("")
    assert "photos.json" in keys and len(keys) == 19
    manifest = json.loads(client.get_object(Bucket="photos-test", Key="photos.json")["Body"].read())
    assert manifest["base_url"] == "https://photos.example.com"
    head = client.head_object(Bucket="photos-test", Key=manifest["albums"][0]["photos"][0]["sizes"]["large"])
    assert head["ContentType"] == "image/webp"
    assert "immutable" in head["CacheControl"]

    second = sync.run(cfg, target, log=quiet)
    assert second.uploaded_objects == 0 and not second.manifest_written

    client.put_object(Bucket="photos-test", Key="photos/old/stale-thumb.webp", Body=b"x")
    report = sync.run(cfg, target, log=quiet)
    assert report.orphans == ["photos/old/stale-thumb.webp"]
    sync.run(cfg, target, prune=True, log=quiet)
    assert "photos/old/stale-thumb.webp" not in target.list_keys("photos/")


# --- render settings in keys ------------------------------------------------

@pytest.mark.parametrize("change", [
    {"WATERMARK_TEXT": "@someone_else"},
    {"WATERMARK_OPACITY": "0.7"},
    {"WATERMARK_SIZE": "0.05"},
])
def test_render_setting_change_rerenders(src, out, change):
    run_local(src, out)
    old = set(run_local(src, out).manifest["albums"][0]["photos"][0]["sizes"].values())
    cfg = local_cfg(src, out, **change)
    result = sync.run(cfg, LocalTarget(out), log=quiet)
    assert result.uploaded_photos == 6 and result.skipped_photos == 0
    new = set(result.manifest["albums"][0]["photos"][0]["sizes"].values())
    assert new.isdisjoint(old)
    assert old <= set(result.orphans)


def test_render_version_and_quality_change_keys(src, out, monkeypatch):
    cfg = local_cfg(src, out)
    base = sync.render_fingerprint(cfg)
    monkeypatch.setattr(sync, "RENDER_VERSION", sync.RENDER_VERSION + 1)
    assert sync.render_fingerprint(cfg) != base
    monkeypatch.undo()
    monkeypatch.setattr(sync.imaging, "WEBP_QUALITY", 50)
    assert sync.render_fingerprint(cfg) != base
    monkeypatch.undo()
    monkeypatch.setattr(sync.imaging, "SIZES", {"thumb": 400, "medium": 1600, "large": 2560})
    assert sync.render_fingerprint(cfg) != base
    assert sync.content_digest(b"x", base) != sync.content_digest(b"x", sync.render_fingerprint(cfg))


# --- per-file error isolation ---------------------------------------------

GREECE = ("2024", "06-15-2024 Greece")


def test_corrupt_jpeg_skipped_rest_published(src, out, capsys):
    (src.joinpath(*GREECE, "_web", "broken.jpg")).write_bytes(b"\xff\xd8\xff not really a jpeg")
    result = run_local(src, out)
    assert result.photos == 6 and result.manifest_written
    assert any("broken.jpg" in e for e in result.errors)
    assert "broken" not in json.dumps(result.manifest)

    rc = main(["--source", str(src), "--target", "local", "--local-dir", str(out),
               "--env-file", str(src / "none.env")])
    assert rc == 1
    assert (out / "photos.json").exists()

    rc = main(["--check", "--source", str(src), "--env-file", str(src / "none.env")])
    text = capsys.readouterr().out
    assert rc == 1 and "broken.jpg" in text and "1 errors" in text


def test_errors_block_prune(src, out):
    run_local(src, out)
    victim = src.joinpath(*GREECE, "_web", "DSC04351.jpg")
    victim.write_bytes(b"truncated")
    result = run_local(src, out, prune=True)
    assert result.orphans and not result.deleted
    assert all((out / k).exists() for k in result.orphans)


def test_malformed_album_md_yaml(src, out, capsys):
    md = src.joinpath(*GREECE, "album.md")
    md.write_text("---\ntitle: [unclosed\n---\nintro\n")
    result = run_local(src, out)
    assert any("not valid YAML" in e for e in result.errors)
    slugs = [a["slug"] for a in result.manifest["albums"]]
    assert "2024-06-15-greece" not in slugs  # hidden state unknown: not published
    assert len(slugs) == 2
    rc = main(["--check", "--source", str(src), "--env-file", str(src / "none.env")])
    assert rc == 1 and "not valid YAML" in capsys.readouterr().out


@pytest.mark.parametrize("front,err,check", [
    ("order: first", "'order' must be a whole number", lambda a: "order" not in a),
    ("title: [a, b]", "'title' must be text", lambda a: a["title"] == "Greece"),
    ("titel: Cyclades", "unknown key 'titel'", lambda a: a["title"] == "Greece"),
    ("date: 2024-13-45", "unknown key 'date'", lambda a: a["date"] == "2024-06-15"),
    ("cover: [x.jpg]", "'cover' must be text", lambda a: a["cover"].startswith("dsc04639-")),
])
def test_bad_album_md_field_types(src, out, front, err, check):
    src.joinpath(*GREECE, "album.md").write_text(f"---\n{front}\n---\nHi.\n")
    result = run_local(src, out)
    assert any(err in w for w in result.warnings)
    assert not result.errors
    greece = next(a for a in result.manifest["albums"] if a["slug"] == "2024-06-15-greece")
    assert check(greece) and greece["intro"] == "Hi."


def test_album_md_field_mistake_does_not_freeze_the_site(src, out, capsys):
    """Regression: a typo in an optional album.md field used to be an error,
    and any error holds photos.json back, so every later sync kept the old
    manifest and new photos never appeared."""
    run_local(src, out)
    src.joinpath(*GREECE, "album.md").write_text("---\ntitle: Greece\norder: first\n---\n")
    make_jpeg(src.joinpath(*GREECE, "_web", "NEW.jpg"), size=(800, 600), taken_at="2024:06:15 20:00:00")
    result = run_local(src, out)
    assert result.manifest_written and not result.errors and not result.blocked
    published = json.loads((out / "photos.json").read_text())
    assert any(p["id"].startswith("new-") for a in published["albums"] for p in a["photos"])
    rc = main(["--source", str(src), "--target", "local", "--local-dir", str(out),
               "--env-file", str(src / "none.env")])
    assert rc == 0 and "'order' must be a whole number" in capsys.readouterr().out
    rc = main(["--check", "--source", str(src), "--env-file", str(src / "none.env")])
    text = capsys.readouterr().out
    assert rc == 0 and "'order' must be a whole number" in text and "0 errors" in text


@pytest.mark.parametrize("content", [
    "---\ntitle: [unclosed\n---\n",   # YAML broken: hidden unknown
    "---\n- a\n- b\n---\n",           # not a mapping
])
def test_unusable_album_md_still_errors(src, out, content):
    src.joinpath(*GREECE, "album.md").write_text(content)
    result = run_local(src, out)
    assert result.errors
    assert "2024-06-15-greece" not in [a["slug"] for a in result.manifest["albums"]]


def test_bad_hidden_value_treated_as_hidden(tmp_path):
    md = tmp_path / "album.md"
    md.write_text("---\nhidden: maybe\n---\n")
    problems = []
    assert archive.parse_album_md(md, problems).hidden is True
    assert problems and "hidden" in problems[0]


def test_slug_collision_warns(tmp_path):
    root = tmp_path / "a"
    make_jpeg(root / "2024" / "Trip" / "_web" / "a.jpg", size=(300, 200))
    make_jpeg(root / "2024" / "trip!" / "_web" / "b.jpg", size=(300, 200))
    result = run_local(root, tmp_path / "out")
    assert sorted(a["slug"] for a in result.manifest["albums"]) == ["trip", "trip-2"]
    assert any("already used" in w for w in result.warnings)


# --- hidden albums --------------------------------------------------------

def test_hiding_album_deletes_its_objects_without_prune(src, out):
    run_local(src, out)
    greece_dir = out / "photos" / "2024-06-15-greece"
    assert len(list(greece_dir.iterdir())) == 9
    src.joinpath(*GREECE, "album.md").write_text("---\nhidden: true\n---\n")
    result = run_local(src, out)  # no --prune
    assert len(result.hidden_deleted) == 9
    assert not greece_dir.exists()
    assert "2024-06-15-greece" not in [a["slug"] for a in result.manifest["albums"]]
    assert result.orphans == []
    assert len(list((out / "photos").rglob("*.webp"))) == 9  # other albums untouched


@mock_aws
def test_s3_read_missing_key_returns_none(monkeypatch):
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    client = boto3.client("s3", region_name="us-east-1",
                          aws_access_key_id="x", aws_secret_access_key="y")
    client.create_bucket(Bucket="photos-missing")
    assert S3Target("photos-missing", client).read("photos.json") is None


class _FakeClient:
    """Raises a botocore ClientError with a given code, like providers that
    answer a missing key with a plain 404 instead of NoSuchKey."""

    class exceptions:
        class NoSuchKey(Exception):
            pass

    def __init__(self, code):
        self.code = code

    def get_object(self, **_kw):
        raise ClientError({"Error": {"Code": self.code, "Message": "x"}}, "GetObject")


@pytest.mark.parametrize("code", ["404", "NoSuchKey", "NotFound"])
def test_s3_read_404_variants_return_none(code):
    assert S3Target("b", _FakeClient(code)).read("photos.json") is None


@pytest.mark.parametrize("code", ["403", "AccessDenied", "InternalError"])
def test_s3_read_other_errors_raise(code):
    with pytest.raises(ClientError):
        S3Target("b", _FakeClient(code)).read("photos.json")


def test_s3_client_disables_default_checksums():
    cfg = Config.from_env({"PHOTO_SOURCE_ROOT": "/x", "TARGET": "s3", "S3_BUCKET": "b",
                           "S3_KEY_ID": "k", "S3_APP_KEY": "s",
                           "S3_ENDPOINT_URL": "https://s3.us-west-004.backblazeb2.com"})
    client = S3Target.from_config(cfg).client
    assert client.meta.config.request_checksum_calculation == "when_required"
    assert client.meta.config.response_checksum_validation == "when_required"
