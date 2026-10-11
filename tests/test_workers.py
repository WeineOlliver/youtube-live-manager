from unittest.mock import MagicMock

import pytest

from core import youtube_api
from ui import workers
from ui.workers import CreateLivesWorker


@pytest.fixture
def thumbs(tmp_path):
    fhd = tmp_path / "fhd.png"
    shorts = tmp_path / "shorts.png"
    fhd.write_bytes(b"x")
    shorts.write_bytes(b"x")
    return str(fhd), str(shorts)


@pytest.fixture
def _cfg(thumbs):
    def make(**overrides):
        return _base_cfg(thumbs, **overrides)
    return make


def _base_cfg(thumbs, **overrides):
    cfg = {
        "title": "Minha Live",
        "description": "desc",
        "tags": ["a"],
        "thumbnail_normal": thumbs[0],
        "thumbnail_shorts": thumbs[1],
        "test_mode": True,
        "enable_fhd": True,
        "enable_shorts": True,
        "stream_key": "key-fhd",
        "stream_key_shorts": "key-shorts",
    }
    cfg.update(overrides)
    return cfg


@pytest.fixture
def fake_yt(monkeypatch):
    fake = MagicMock()
    fake.find_stream_id_by_key.side_effect = lambda _yt, key: f"stream-{key}"
    counter = iter(["bc1", "bc2"])
    fake.create_broadcast.side_effect = lambda *a, **k: {"id": next(counter)}
    fake.cleanup_resources.return_value = []
    fake.studio_url = youtube_api.studio_url
    fake.describe_error = youtube_api.describe_error
    monkeypatch.setattr(workers, "yt", fake)
    return fake


def _run(cfg):
    worker = CreateLivesWorker(cfg)
    results = {"done": None, "failed": False, "logs": []}
    worker.done.connect(lambda ids: results.update(done=ids))
    worker.failed.connect(lambda: results.update(failed=True))
    worker.log_line.connect(results["logs"].append)
    worker.run()
    return results


def test_creates_fhd_and_shorts_with_their_own_keys(fake_yt, _cfg):
    results = _run(_cfg())
    assert results["done"] == {"bc_fhd_id": "bc1", "bc_shorts_id": "bc2"}
    binds = [c.args[1:] for c in fake_yt.bind_broadcast.call_args_list]
    assert binds == [("bc1", "stream-key-fhd"), ("bc2", "stream-key-shorts")]
    titles = [c.args[1] for c in fake_yt.create_broadcast.call_args_list]
    assert titles == ["Minha Live", "Minha Live | SHORTS"]
    uploaded = [c.args[2] for c in fake_yt.upload_thumbnail.call_args_list]
    assert uploaded == [_cfg()["thumbnail_normal"], _cfg()["thumbnail_shorts"]]


def test_shorts_only_does_not_require_fhd_key(fake_yt, _cfg):
    results = _run(_cfg(enable_fhd=False, stream_key=""))
    assert results["done"] == {"bc_shorts_id": "bc1"}
    fake_yt.bind_broadcast.assert_called_once_with(fake_yt.get_youtube_client.return_value, "bc1", "stream-key-shorts")


def test_missing_shorts_key_fails_before_calling_api(fake_yt, _cfg):
    results = _run(_cfg(stream_key_shorts=" "))
    assert results["failed"] is True
    assert any("Shorts" in line for line in results["logs"])
    fake_yt.get_youtube_client.assert_not_called()


def test_no_type_selected_fails(fake_yt, _cfg):
    results = _run(_cfg(enable_fhd=False, enable_shorts=False))
    assert results["failed"] is True
    fake_yt.get_youtube_client.assert_not_called()


def test_shorts_failure_rolls_back_fhd_broadcast(fake_yt, _cfg):
    fake_yt.find_stream_id_by_key.side_effect = ["stream-fhd", ValueError("Chave RTMP não encontrada na conta")]
    results = _run(_cfg())
    assert results["failed"] is True
    fake_yt.cleanup_resources.assert_called_once()
    assert fake_yt.cleanup_resources.call_args.args[1] == {"bc_fhd_id": "bc1"}


def test_logs_studio_link_for_each_broadcast(fake_yt, _cfg):
    results = _run(_cfg())
    links = [line for line in results["logs"] if line.startswith("🔗")]
    assert links == [
        "🔗 Studio Full HD: https://studio.youtube.com/video/bc1/livestreaming",
        "🔗 Studio Shorts: https://studio.youtube.com/video/bc2/livestreaming",
    ]


def test_missing_thumbnail_fails_before_calling_api(fake_yt, _cfg):
    results = _run(_cfg(thumbnail_shorts="C:/nao/existe.png"))
    assert results["failed"] is True
    assert any("Thumbnail Shorts" in line for line in results["logs"])
    fake_yt.get_youtube_client.assert_not_called()
