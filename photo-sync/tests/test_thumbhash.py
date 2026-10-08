import base64
import io

from PIL import Image

from photo_sync import imaging, sync
from photo_sync.config import Config
from photo_sync.sample_archive import build
from photo_sync.targets import LocalTarget


def _landscape():
    w, h = 32, 24
    return w, h, [(x * 8, y * 10, (x * y) % 256) for y in range(h) for x in range(w)]


def _portrait():
    w, h = 18, 32
    return w, h, [(255 - y * 7, x * 13, 128) for y in range(h) for x in range(w)]


def test_matches_reference_encoder():
    # Expected values come from the reference JS encoder (npm thumbhash
    # 0.1.1, rgbaToThumbHash) on the same pixels, fully opaque. The site
    # decodes with that package, so the bytes must match exactly.
    for (w, h, px), expected in ((_landscape(), "2xgOHZpgdodwiIiGiGeIh/OkD/eI"),
                                 (_portrait(), "IEgKNBhw93d4h4iIiIhwj/j4iA==")):
        assert base64.b64encode(imaging._thumbhash_rgb(w, h, px)).decode() == expected


def _jpeg(size, color=(30, 140, 200)):
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, "JPEG", quality=95)
    buf.seek(0)
    return buf


def test_large_photo_hash_is_small():
    th = imaging.thumbhash(_jpeg((4000, 2667)))
    assert th and len(base64.b64decode(th)) <= 25


def test_unreadable_gives_no_placeholders():
    assert imaging.placeholders(io.BytesIO(b"not an image")) == {}
    assert imaging.thumbhash(io.BytesIO(b"not an image")) is None


def test_colour_unchanged_by_shared_decode():
    assert imaging.placeholders(_jpeg((800, 600)))["color"] == imaging.average_color(_jpeg((800, 600)))


def test_manifest_has_thumbhash_on_fresh_and_reused_runs(tmp_path):
    src = build(tmp_path / "archive")
    out = tmp_path / "out"
    cfg = Config.from_env({"PHOTO_SOURCE_ROOT": str(src), "TARGET": "local",
                           "LOCAL_TARGET_DIR": str(out)})
    first = sync.run(cfg, LocalTarget(out), log=lambda _m: None)
    second = sync.run(cfg, LocalTarget(out), log=lambda _m: None)
    assert second.uploaded_photos == 0  # reuse path, nothing re-rendered
    for result in (first, second):
        photos = [p for a in result.manifest["albums"] for p in a["photos"]]
        assert photos and all(len(base64.b64decode(p["thumbhash"])) <= 25 for p in photos)
    assert first.manifest["albums"] == second.manifest["albums"]
