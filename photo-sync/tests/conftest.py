import pytest

from photo_sync import config


@pytest.fixture(autouse=True)
def _no_settle_delay(monkeypatch, tmp_path):
    """Tests write files and sync them straight away; the 60 s "still being
    exported" guard would skip all of them. Tests of that guard set
    PHOTO_SETTLE_SECONDS themselves. Each test also gets its own run lock."""
    monkeypatch.setattr(config, "DEFAULT_SETTLE_SECONDS", 0)
    monkeypatch.setenv("PHOTO_LOCK_FILE", str(tmp_path / "photo-sync.lock"))
