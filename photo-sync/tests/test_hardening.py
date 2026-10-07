"""Hardening: watermark font, run lock, large photos, dates, file handling,
automatic covers and friendly camera names."""

import json
import os
import time
import unicodedata

import pytest
from PIL import Image, ImageFont

from photo_sync import archive, cameras, imaging, sync
from photo_sync.cli import main, run_lock
from photo_sync.config import Config
from photo_sync.sample_archive import build, make_jpeg
from photo_sync.targets import LocalTarget


def quiet(_msg):
    pass


def cfg_for(src, out, **env):
    base = {"PHOTO_SOURCE_ROOT": str(src), "TARGET": "local", "LOCAL_TARGET_DIR": str(out)}
    base.update(env)
    return Config.from_env(base)


def sync_dir(src, out, **env):
    return sync.run(cfg_for(src, out, **env), LocalTarget(out), log=quiet)


def album(result, slug):
    return next(a for a in result.manifest["albums"] if a["slug"] == slug)


def stem(photo_id):
    return photo_id.rsplit("-", 1)[0]


# --- watermark font ---------------------------------------------------------

def test_watermark_always_uses_bundled_font(monkeypatch):
    assert imaging.FONT_PATH.is_file()
    assert ImageFont.truetype(str(imaging.FONT_PATH), 20).getname()[0] == "TeX Gyre Heros"
    used = []
    real = ImageFont.truetype
    monkeypatch.setattr(ImageFont, "truetype", lambda name, size: used.append(name) or real(name, size))
    imaging.watermark(Image.new("RGB", (800, 600)), "@jak_creative_", 0.4)
    assert used == [str(imaging.FONT_PATH)]


def test_font_hash_is_in_render_fingerprint(tmp_path, monkeypatch):
    cfg = cfg_for(tmp_path, tmp_path / "o")
    before = sync.render_fingerprint(cfg)
    assert imaging.font_digest().encode() in before
    monkeypatch.setattr(imaging, "font_digest", lambda: "0" * 64)
    assert sync.render_fingerprint(cfg) != before


def test_watermark_draws_bottom_right():
    img = imaging.watermark(Image.new("RGB", (2560, 1707), (0, 0, 0)), "@jak_creative_", 0.4)
    bbox = img.point(lambda v: 255 if v > 20 else 0).getbbox()
    assert bbox and bbox[0] > 2560 * 0.6 and bbox[1] > 1707 * 0.85


# --- run lock -----------------------------------------------------------------

def test_second_sync_exits_cleanly_while_one_runs(tmp_path, capsys):
    src, out = build(tmp_path / "a"), tmp_path / "o"
    args = ["--source", str(src), "--target", "local", "--local-dir", str(out),
            "--env-file", str(tmp_path / "none.env")]
    lock = tmp_path / "photo-sync.lock"  # conftest points PHOTO_LOCK_FILE here
    with run_lock(lock):
        assert main(args) == 0
        text = capsys.readouterr().out
        assert "already in progress" in text and f"pid {os.getpid()}" in text
        assert not (out / "photos.json").exists()
        # --check writes nothing, so it is not locked out.
        assert main(["--check", "--source", str(src), "--env-file", str(tmp_path / "none.env")]) == 0
    assert main(args) == 0
    assert (out / "photos.json").exists()


def test_lock_released_after_a_failed_run(tmp_path, monkeypatch):
    src, out = build(tmp_path / "a"), tmp_path / "o"
    args = ["--source", str(src), "--target", "local", "--local-dir", str(out),
            "--env-file", str(tmp_path / "none.env")]

    def boom(*a, **k):
        raise RuntimeError("crash mid-sync")

    monkeypatch.setattr(sync, "run", boom)
    with pytest.raises(RuntimeError):
        main(args)
    monkeypatch.undo()
    monkeypatch.setenv("PHOTO_LOCK_FILE", str(tmp_path / "photo-sync.lock"))
    with run_lock(tmp_path / "photo-sync.lock"):
        pass  # would raise AlreadyRunning if the crashed run still held it


# --- large photos ---------------------------------------------------------------

def test_panorama_over_pillow_limit_renders(tmp_path, monkeypatch):
    # Shrink Pillow's limit so a small file stands in for a >179 MP panorama.
    monkeypatch.setattr(Image, "MAX_IMAGE_PIXELS", 1_000_000)
    src, out = tmp_path / "a", tmp_path / "o"
    pano = make_jpeg(src / "2024" / "01-01-2024 Pano" / "_web" / "pano.jpg", size=(9000, 1500))
    with pytest.raises(Image.DecompressionBombError):
        Image.open(pano)  # what the old code hit
    result = sync_dir(src, out)
    assert not result.errors
    photo = album(result, "2024-01-01-pano")["photos"][0]
    assert (photo["width"], photo["height"]) == (2560, 427)
    assert Image.MAX_IMAGE_PIXELS == 1_000_000  # the limit is restored after each open


def test_jpeg_decoded_at_reduced_scale(tmp_path, monkeypatch):
    from PIL import JpegImagePlugin

    path = tmp_path / "big.jpg"
    Image.new("L", (20000, 2500), 128).save(path, "JPEG", quality=70)
    decoded = []
    real = JpegImagePlugin.JpegImageFile.draft

    def spy(self, mode, size):
        res = real(self, mode, size)
        decoded.append(self.size)
        return res

    monkeypatch.setattr(JpegImagePlugin.JpegImageFile, "draft", spy)
    img = imaging.load_source(path, 2560)
    assert img.size == (2560, 320)
    # libjpeg decoded at reduced scale, not the full 50 MP.
    assert decoded and decoded[0][0] * decoded[0][1] <= 20000 * 2500 // 4


def test_non_jpeg_over_limit_is_a_clear_error(tmp_path, monkeypatch):
    monkeypatch.setattr(imaging, "MAX_OTHER_PIXELS", 1_000_000)
    src, out = tmp_path / "a", tmp_path / "o"
    web = src / "2024" / "01-01-2024 Big" / "_web"
    web.mkdir(parents=True)
    Image.new("RGB", (2000, 1000)).save(web / "big.png")
    make_jpeg(web / "ok.jpg", size=(600, 400))
    result = sync_dir(src, out)
    assert any("big.png" in e and "MP limit" in e for e in result.errors)
    assert [stem(p["id"]) for p in album(result, "2024-01-01-big")["photos"]] == ["ok"]


# --- dates ----------------------------------------------------------------------

def test_export_time_is_never_the_capture_time(tmp_path):
    src, out = tmp_path / "a", tmp_path / "o"
    make_jpeg(src / "2023" / "Trip" / "_web" / "a.jpg", size=(600, 400),
              taken_at=None, export_time="2026:10:01 12:00:00")
    make_jpeg(src / "2023" / "Trip" / "_web" / "b.jpg", size=(600, 400),
              taken_at="2023:08:20 16:00:00", export_time="2026:10:01 12:00:01")
    result = sync_dir(src, out)
    trip = album(result, "trip")
    by = {stem(p["id"]): p for p in trip["photos"]}
    assert "taken_at" not in by["a"]["exif"]
    assert by["b"]["exif"]["taken_at"] == "2023-08-20T16:00:00"
    assert trip["date"] == "2023-08-20"  # not 2026-10-01


def test_offset_time_original_honoured(tmp_path):
    src, out = tmp_path / "a", tmp_path / "o"
    web = src / "2024" / "Travel" / "_web"
    # 08:00 in Athens (UTC+3) is 05:00Z; 10:00 in Tokyo (UTC+9) is 01:00Z.
    # By wall clock Athens comes first; by the real instant, Tokyo does.
    make_jpeg(web / "athens.jpg", size=(600, 400), taken_at="2024:06:16 08:00:00", offset="+03:00")
    make_jpeg(web / "tokyo.jpg", size=(600, 400), taken_at="2024:06:16 10:00:00", offset="+09:00")
    make_jpeg(web / "bad.jpg", size=(600, 400), taken_at="2024:06:16 09:00:00", offset="junk")
    result = sync_dir(src, out)
    travel = album(result, "travel")
    photos = {stem(p["id"]): p for p in travel["photos"]}
    assert photos["athens"]["exif"]["taken_at"] == "2024-06-16T08:00:00+03:00"
    assert photos["bad"]["exif"]["taken_at"] == "2024-06-16T09:00:00"
    order = [stem(p["id"]) for p in travel["photos"]]
    assert order.index("tokyo") < order.index("athens")
    assert travel["date"] == "2024-06-16"  # local date of the earliest photo


# --- file handling --------------------------------------------------------------

def test_cover_match_ignores_unicode_form_and_case(tmp_path):
    src, out = tmp_path / "a", tmp_path / "o"
    shoot = src / "2024" / "05-01-2024 Paris"
    nfd = unicodedata.normalize("NFD", "Café.jpg")
    make_jpeg(shoot / "_web" / nfd, size=(600, 400), taken_at="2024:05:01 12:00:00")
    make_jpeg(shoot / "_web" / "tower.jpg", size=(400, 600), taken_at="2024:05:01 10:00:00")
    (shoot / "album.md").write_text("---\ncover: " + unicodedata.normalize("NFC", "CAFÉ.JPG") + "\n---\n",
                                    encoding="utf-8")
    result = sync_dir(src, out)
    paris = album(result, "2024-05-01-paris")
    assert stem(paris["cover"]) == "cafe"
    assert not any("not found" in w for w in result.warnings)


def test_other_image_formats_render_and_junk_warns(tmp_path):
    src, out = tmp_path / "a", tmp_path / "o"
    web = src / "2024" / "03-03-2024 Mixed" / "_web"
    make_jpeg(web / "a.jpg", size=(900, 600), taken_at="2024:03:03 10:00:00")
    make_jpeg(web / "b.png", size=(900, 600), taken_at="2024:03:03 11:00:00", fmt="PNG")
    make_jpeg(web / "c.tif", size=(600, 900), taken_at="2024:03:03 12:00:00", fmt="TIFF")
    (web / "notes.txt").write_text("not a photo")
    (web / "d.heic").write_bytes(b"\x00\x00\x00\x18ftypheic not decodable")
    result = sync_dir(src, out)
    mixed = album(result, "2024-03-03-mixed")
    assert sorted(stem(p["id"]) for p in mixed["photos"]) == ["a", "b", "c"]
    assert any("notes.txt" in w and "not an image" in w for w in result.warnings)
    assert any("d.heic" in w for w in result.warnings)
    assert not result.errors  # warnings only: the site keeps updating
    tif = next(p for p in mixed["photos"] if stem(p["id"]) == "c")
    assert tif["exif"]["taken_at"] == "2024-03-03T12:00:00"


def test_damaged_png_is_an_error(tmp_path):
    src, out = tmp_path / "a", tmp_path / "o"
    web = src / "2024" / "03-03-2024 Mixed" / "_web"
    make_jpeg(web / "a.jpg", size=(900, 600))
    (web / "broken.png").write_bytes(b"\x89PNG\r\n\x1a\n truncated")
    result = sync_dir(src, out)
    assert any("broken.png" in e for e in result.errors)


def test_recently_modified_files_hold_the_manifest(tmp_path, capsys):
    src, out = build(tmp_path / "a"), tmp_path / "o"
    sync_dir(src, out)
    before = (out / "photos.json").read_bytes()
    fresh = make_jpeg(src / "2024" / "06-15-2024 Greece" / "_web" / "EXPORTING.jpg", size=(600, 400))
    result = sync.run(cfg_for(src, out, PHOTO_SETTLE_SECONDS="60"), LocalTarget(out),
                      log=quiet, prune=True)
    assert any("EXPORTING.jpg" in w and "still running" in w for w in result.warnings)
    assert not result.errors and not result.blocked  # exit 0: nothing is wrong
    assert not result.manifest_written and not result.deleted
    assert (out / "photos.json").read_bytes() == before

    sync.run(cfg_for(src, out, PHOTO_SETTLE_SECONDS="60"), None, check=True, log=print)
    assert "EXPORTING.jpg" in capsys.readouterr().out

    past = time.time() - 120
    os.utime(fresh, (past, past))
    result = sync_dir(src, out, PHOTO_SETTLE_SECONDS="60")
    assert result.manifest_written and "exporting" in json.dumps(result.manifest)


def test_fresh_copy_of_whole_archive_publishes_nothing(tmp_path):
    """A just-copied archive (every mtime is now) must not publish an empty site."""
    src, out = build(tmp_path / "a"), tmp_path / "o"
    now = time.time()
    for p in src.rglob("*.jpg"):
        os.utime(p, (now, now))
    result = sync_dir(src, out, PHOTO_SETTLE_SECONDS="60")
    assert not (out / "photos.json").exists() and not result.manifest_written


# --- automatic cover -------------------------------------------------------------

def _shoot(tmp_path, specs, album_md=None):
    src = tmp_path / "a"
    shoot = src / "2024" / "07-04-2024 Covers"
    for name, size, hour, rating, style in specs:
        make_jpeg(shoot / "_web" / name, size=size, taken_at=f"2024:07:04 {hour:02d}:00:00",
                  rating=rating, rating_style=style)
    if album_md:
        (shoot / "album.md").write_text(album_md)
    result = sync_dir(src, tmp_path / "o")
    return stem(album(result, "2024-07-04-covers")["cover"])


P, L = (400, 600), (600, 400)


@pytest.mark.parametrize("specs,expected", [
    # highest-rated portrait wins over a better-rated landscape
    ([("l5.jpg", L, 9, 5, "attribute"), ("p3.jpg", P, 10, 3, "attribute"),
      ("p4.jpg", P, 11, 4, "element")], "p4"),
    # ties go to the earliest capture
    ([("late.jpg", P, 12, 4, "attribute"), ("early.jpg", P, 8, 4, "attribute")], "early"),
    # no portraits: highest-rated landscape
    ([("l1.jpg", L, 8, 1, "attribute"), ("l4.jpg", L, 12, 4, "attribute")], "l4"),
    # no ratings anywhere: earliest portrait
    ([("l.jpg", L, 7, None, ""), ("p2.jpg", P, 11, None, ""), ("p1.jpg", P, 9, None, "")], "p1"),
])
def test_automatic_cover(tmp_path, specs, expected):
    assert _shoot(tmp_path, specs) == expected


def test_album_md_cover_beats_ratings(tmp_path):
    specs = [("best.jpg", P, 9, 5, "attribute"), ("chosen.jpg", L, 10, 1, "attribute")]
    assert _shoot(tmp_path, specs, "---\ncover: chosen.jpg\n---\n") == "chosen"


def test_rotated_landscape_counts_as_portrait(tmp_path):
    src = tmp_path / "a"
    web = src / "2024" / "07-04-2024 Covers" / "_web"
    make_jpeg(web / "flat.jpg", size=L, taken_at="2024:07:04 08:00:00", rating=5)
    make_jpeg(web / "turned.jpg", size=L, orientation=6, taken_at="2024:07:04 09:00:00", rating=2)
    result = sync_dir(src, tmp_path / "o")
    assert stem(album(result, "2024-07-04-covers")["cover"]) == "turned"


def test_read_rating_forms():
    assert imaging.read_rating(b'<x:xmpmeta> xmp:Rating="4" </x:xmpmeta>') == 4
    assert imaging.read_rating(b"<x:xmpmeta><xmp:Rating>5</xmp:Rating></x:xmpmeta>") == 5
    assert imaging.read_rating(b"<x:xmpmeta xap:Rating='3'></x:xmpmeta>") == 3
    assert imaging.read_rating(b"no xmp here") is None
    assert imaging.read_rating(b"<x:xmpmeta></x:xmpmeta>") is None


# --- camera names ----------------------------------------------------------------

@pytest.mark.parametrize("make,model,name", [
    ("SONY", "ILCE-6400", "Sony α6400"),
    ("SONY", "ILCE-6700", "Sony α6700"),
    ("SONY", "ILCE-7M3", "Sony α7 III"),
    ("SONY", "ILCE-7M4", "Sony α7 IV"),
    ("SONY", "ILCE-7RM4A", "Sony α7R IVA"),
    ("SONY", "ILCE-7SM3", "Sony α7S III"),
    ("SONY", "ILCE-7CR", "Sony α7CR"),
    ("SONY", "ILCE-7CM2", "Sony α7C II"),
    ("SONY", "ILCE-1", "Sony α1"),
    ("SONY", "DSC-RX100M7", "Sony RX100 VII"),
    ("SONY", "DSC-RX1RM2", "Sony RX1R II"),
    ("SONY", "ZV-E10M2", "Sony ZV-E10 II"),
    ("SONY", "ILME-FX3", "Sony FX3"),
    (None, "ILCE-6400", "Sony α6400"),
    ("Canon", "Canon EOS R5", "Canon EOS R5"),
    ("Canon", "Canon EOS 5D Mark IV", "Canon EOS 5D Mark IV"),
    ("NIKON CORPORATION", "NIKON Z 6_2", "Nikon Z6 II"),
    ("NIKON CORPORATION", "NIKON Z f", "Nikon Zf"),
    ("NIKON CORPORATION", "NIKON D850", "Nikon D850"),
    ("FUJIFILM", "X-T4", "Fujifilm X-T4"),
    ("FUJIFILM", "X100VI", "Fujifilm X100VI"),
    ("Apple", "iPhone 15 Pro", "Apple iPhone 15 Pro"),
    ("OM Digital Solutions", "OM-1", "OM System OM-1"),
    ("SONY", None, None),
    (None, None, None),
])
def test_camera_name(make, model, name):
    assert cameras.camera_name(make, model) == name


def test_body_name_beside_unchanged_camera(tmp_path):
    src, out = tmp_path / "a", tmp_path / "o"
    make_jpeg(src / "2024" / "01-01-2024 N" / "_web" / "n.jpg", size=(600, 400),
              make="NIKON CORPORATION", model="NIKON Z 6_2")
    exif = album(sync_dir(src, out), "2024-01-01-n")["photos"][0]["exif"]
    assert exif["camera"] == "NIKON Z 6_2" and exif["body_name"] == "Nikon Z6 II"
