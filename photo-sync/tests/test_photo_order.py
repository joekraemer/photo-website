"""Per-album photo order from album.md `sort:` and `photos:` (#32)."""

import pytest

from photo_sync import archive, sync
from photo_sync.config import Config
from photo_sync.sample_archive import make_jpeg
from photo_sync.targets import LocalTarget


def quiet(_msg):
    pass


def order_of(tmp_path, album_md=None, undated=()):
    """Sync one shoot of b (08:00), c (09:00), a (10:00) plus any undated
    photos; return (photo stems in manifest order, cover stem, warnings)."""
    src = tmp_path / "a"
    shoot = src / "2024" / "07-04-2024 Order"
    for name, hour in (("b.jpg", 8), ("c.jpg", 9), ("a.jpg", 10)):
        make_jpeg(shoot / "_web" / name, size=(600, 400), taken_at=f"2024:07:04 {hour:02d}:00:00")
    for name in undated:
        make_jpeg(shoot / "_web" / name, size=(600, 400), taken_at=None)
    if album_md is not None:
        (shoot / "album.md").write_text(album_md, encoding="utf-8")
    cfg = Config.from_env({"PHOTO_SOURCE_ROOT": str(src), "TARGET": "local",
                           "LOCAL_TARGET_DIR": str(tmp_path / "o")})
    result = sync.run(cfg, LocalTarget(tmp_path / "o"), log=quiet)
    album = result.manifest["albums"][0]
    stems = [p["id"].rsplit("-", 1)[0] for p in album["photos"]]
    for p in album["photos"]:
        assert "_name" not in p and "_rating" not in p
    return stems, album["cover"].rsplit("-", 1)[0], result.warnings


def test_default_is_capture_order(tmp_path):
    assert order_of(tmp_path)[0] == ["b", "c", "a"]


@pytest.mark.parametrize("sort,expected", [
    ("date", ["b", "c", "a", "z"]),
    ("date-desc", ["a", "c", "b", "z"]),  # undated stays last
    ("name", ["a", "b", "c", "z"]),
    ("Name", ["a", "b", "c", "z"]),
])
def test_sort_modes(tmp_path, sort, expected):
    stems, _, warnings = order_of(tmp_path, f"---\nsort: {sort}\n---\n", undated=("z.jpg",))
    assert stems == expected
    assert not any("sort" in w for w in warnings)


def test_listed_photos_first_then_sort(tmp_path):
    md = "---\nsort: name\nphotos:\n  - c.jpg\n  - B.JPG\n---\n"
    stems, _, warnings = order_of(tmp_path, md)
    assert stems == ["c", "b", "a"]
    assert warnings == []


def test_unknown_listed_name_warns_and_is_skipped(tmp_path):
    md = "---\nphotos:\n  - missing.jpg\n  - a.jpg\n---\n"
    stems, _, warnings = order_of(tmp_path, md)
    assert stems == ["a", "b", "c"]
    assert any("'missing.jpg'" in w and "not found" in w for w in warnings)


def test_order_does_not_change_automatic_cover_or_date(tmp_path):
    # The cover tie-break and album date still use capture order.
    stems, cover, _ = order_of(tmp_path, "---\nsort: date-desc\n---\n")
    assert stems[0] == "a"
    assert cover == "b"


@pytest.mark.parametrize("front,problem", [
    ("sort: random", "'sort' must be one of"),
    ("sort: 3", "'sort' must be one of"),
    ("photos: a.jpg", "'photos' must be a list"),
    ("photos:\n  - a.jpg\n  - a.jpg", "twice"),
    ("photos:\n  - {x: 1}", "is not a file name"),
])
def test_field_mistakes_are_warnings(tmp_path, front, problem):
    md = tmp_path / "album.md"
    md.write_text(f"---\n{front}\n---\n", encoding="utf-8")
    problems = []
    meta = archive.parse_album_md(md, problems)
    assert any(problem in p for p in problems), problems
    assert meta.sort == "date"


def test_bad_sort_still_publishes(tmp_path):
    stems, _, warnings = order_of(tmp_path, "---\nsort: random\n---\n")
    assert stems == ["b", "c", "a"]
    assert any("'sort' must be one of" in w for w in warnings)
