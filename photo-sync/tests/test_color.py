import io

from PIL import Image

from photo_sync import imaging, sync
from photo_sync.config import Config
from photo_sync.sample_archive import build
from photo_sync.targets import LocalTarget


def _jpeg(color, size=(800, 600)):
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, "JPEG", quality=95)
    buf.seek(0)
    return buf


def test_average_color_of_flat_image():
    hex_ = imaging.average_color(_jpeg((200, 40, 90)))
    r, g, b = (int(hex_[i:i + 2], 16) for i in (1, 3, 5))
    assert abs(r - 200) <= 3 and abs(g - 40) <= 3 and abs(b - 90) <= 3


def test_average_color_unreadable_is_none():
    assert imaging.average_color(io.BytesIO(b"not an image")) is None


def test_manifest_has_color_on_fresh_and_reused_runs(tmp_path):
    src = build(tmp_path / "archive")
    out = tmp_path / "out"
    cfg = Config.from_env({"PHOTO_SOURCE_ROOT": str(src), "TARGET": "local",
                           "LOCAL_TARGET_DIR": str(out)})
    first = sync.run(cfg, LocalTarget(out), log=lambda _m: None)
    second = sync.run(cfg, LocalTarget(out), log=lambda _m: None)
    assert second.uploaded_photos == 0  # reuse path, nothing re-rendered
    for result in (first, second):
        photos = [p for a in result.manifest["albums"] for p in a["photos"]]
        assert photos and all(len(p["color"]) == 7 and p["color"].startswith("#") for p in photos)
    assert first.manifest["albums"] == second.manifest["albums"]
