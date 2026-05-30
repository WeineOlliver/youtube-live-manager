import pickle
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock
from core.youtube_api import (
    get_token_status,
    create_live_stream,
    create_broadcast,
    bind_broadcast,
    update_tags,
    get_stream_status,
    transition_broadcast,
    delete_broadcast,
    delete_live_stream,
    cleanup_resources,
)


class _FakeCreds:
    """Picklable stand-in for google.oauth2.credentials.Credentials."""

    def __init__(self, valid=True, expiry_mins=60):
        self.valid = valid
        self.expired = not valid
        self.refresh_token = "fake_refresh"
        self.expiry = datetime.utcnow() + timedelta(minutes=expiry_mins)


def _make_creds(valid=True, expiry_mins=60):
    return _FakeCreds(valid=valid, expiry_mins=expiry_mins)


def _write_pickle(path, obj):
    with open(path, "wb") as f:
        pickle.dump(obj, f)


def test_token_status_valid_shows_minutes(tmp_path, monkeypatch):
    creds = _make_creds(valid=True, expiry_mins=45)
    _write_pickle(tmp_path / "token.pickle", creds)
    monkeypatch.setattr("core.youtube_api.TOKEN_PATH", str(tmp_path / "token.pickle"))
    is_valid, label = get_token_status()
    assert is_valid is True
    assert "válido" in label
    assert "44" in label or "45" in label


def test_token_status_expired(tmp_path, monkeypatch):
    creds = _make_creds(valid=False, expiry_mins=-10)
    _write_pickle(tmp_path / "token.pickle", creds)
    monkeypatch.setattr("core.youtube_api.TOKEN_PATH", str(tmp_path / "token.pickle"))
    is_valid, label = get_token_status()
    assert is_valid is False
    assert "expirado" in label


def test_token_status_no_file(tmp_path, monkeypatch):
    monkeypatch.setattr("core.youtube_api.TOKEN_PATH", str(tmp_path / "nonexistent.pickle"))
    is_valid, label = get_token_status()
    assert is_valid is False
    assert "não encontrado" in label


def _mock_youtube():
    return MagicMock()


def test_create_live_stream_calls_insert():
    yt = _mock_youtube()
    yt.liveStreams().insert().execute.return_value = {"id": "stream123"}
    create_live_stream(yt, "RTMP_STREAM_FULLHD", resolution="1440p")
    call_kwargs = yt.liveStreams().insert.call_args.kwargs
    assert call_kwargs["body"]["cdn"]["resolution"] == "1440p"
    assert call_kwargs["body"]["snippet"]["title"] == "RTMP_STREAM_FULLHD"


def test_create_broadcast_privacy_and_latency():
    yt = _mock_youtube()
    yt.liveBroadcasts().insert().execute.return_value = {"id": "bc456"}
    result = create_broadcast(yt, "My Live", "Desc", privacy="private", latency="ultraLow")
    call_kwargs = yt.liveBroadcasts().insert.call_args.kwargs
    assert call_kwargs["body"]["status"]["privacyStatus"] == "private"
    assert call_kwargs["body"]["contentDetails"]["latencyPreference"] == "ultraLow"


def test_get_stream_status_active():
    yt = _mock_youtube()
    yt.liveStreams().list().execute.return_value = {
        "items": [{"status": {"streamStatus": "active"}}]
    }
    status = get_stream_status(yt, "stream123")
    assert status == "active"


def test_get_stream_status_no_items_returns_inactive():
    yt = _mock_youtube()
    yt.liveStreams().list().execute.return_value = {"items": []}
    status = get_stream_status(yt, "stream123")
    assert status == "inactive"


def test_update_tags_patches_snippet():
    yt = _mock_youtube()
    yt.videos().list().execute.return_value = {
        "items": [{"snippet": {"title": "My Live", "categoryId": "20"}}]
    }
    yt.videos().update().execute.return_value = {}
    update_tags(yt, "vid123", ["tag1", "tag2"])
    update_kwargs = yt.videos().update.call_args.kwargs
    assert update_kwargs["body"]["snippet"]["tags"] == ["tag1", "tag2"]


def test_delete_broadcast_calls_api():
    yt = _mock_youtube()
    delete_broadcast(yt, "bc123")
    yt.liveBroadcasts.return_value.delete.assert_called_once_with(id="bc123")
    yt.liveBroadcasts.return_value.delete.return_value.execute.assert_called_once()


def test_delete_live_stream_calls_api():
    yt = _mock_youtube()
    delete_live_stream(yt, "s123")
    yt.liveStreams.return_value.delete.assert_called_once_with(id="s123")
    yt.liveStreams.return_value.delete.return_value.execute.assert_called_once()


def test_cleanup_resources_deletes_all_present():
    yt = _mock_youtube()
    ids = {
        "bc_fhd_id": "bc1",
        "bc_shorts_id": "bc2",
        "stream_fhd_id": "s1",
        "stream_shorts_id": "s2",
    }
    errors = cleanup_resources(yt, ids)
    assert errors == []
    assert yt.liveBroadcasts.return_value.delete.call_count == 2
    assert yt.liveStreams.return_value.delete.call_count == 2


def test_cleanup_resources_skips_missing_keys():
    yt = _mock_youtube()
    errors = cleanup_resources(yt, {"bc_fhd_id": "bc1"})
    assert errors == []
    yt.liveBroadcasts.return_value.delete.assert_called_once_with(id="bc1")
    assert yt.liveStreams.return_value.delete.call_count == 0


def test_cleanup_resources_returns_errors_on_failure():
    yt = _mock_youtube()
    yt.liveBroadcasts.return_value.delete.return_value.execute.side_effect = Exception("quota")
    ids = {"bc_fhd_id": "bc1", "bc_shorts_id": "bc2"}
    errors = cleanup_resources(yt, ids)
    assert len(errors) == 2
    assert "bc_fhd_id" in errors[0]
    assert "bc_shorts_id" in errors[1]


def test_cleanup_resources_empty_ids_returns_no_errors():
    yt = _mock_youtube()
    errors = cleanup_resources(yt, {})
    assert errors == []
