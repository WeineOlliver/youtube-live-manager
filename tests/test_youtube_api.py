import pickle

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock
from core.youtube_api import (
    get_token_status,
    create_broadcast,
    bind_broadcast,
    update_tags,
    get_stream_status,
    transition_broadcast,
    delete_broadcast,
    find_stream_id_by_key,
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


def test_cleanup_resources_deletes_both_broadcasts():
    yt = _mock_youtube()
    errors = cleanup_resources(yt, {"bc_fhd_id": "bc1", "bc_shorts_id": "bc2"})
    assert errors == []
    deleted = [c.kwargs["id"] for c in yt.liveBroadcasts.return_value.delete.call_args_list]
    assert deleted == ["bc1", "bc2"]


def test_cleanup_resources_skips_missing_keys():
    yt = _mock_youtube()
    errors = cleanup_resources(yt, {"bc_shorts_id": "bc2"})
    assert errors == []
    yt.liveBroadcasts.return_value.delete.assert_called_once_with(id="bc2")


def test_cleanup_resources_never_deletes_stream():
    yt = _mock_youtube()
    cleanup_resources(yt, {"bc_fhd_id": "bc1", "stream_id": "s1"})
    assert yt.liveStreams.return_value.delete.call_count == 0


def test_cleanup_resources_returns_errors_on_failure():
    yt = _mock_youtube()
    yt.liveBroadcasts.return_value.delete.return_value.execute.side_effect = Exception("quota")
    errors = cleanup_resources(yt, {"bc_fhd_id": "bc1", "bc_shorts_id": "bc2"})
    assert len(errors) == 2
    assert "bc_fhd_id" in errors[0]
    assert "bc_shorts_id" in errors[1]


def test_cleanup_resources_empty_ids_returns_no_errors():
    yt = _mock_youtube()
    errors = cleanup_resources(yt, {})
    assert errors == []


def _stream(stream_id, key):
    return {"id": stream_id, "cdn": {"ingestionInfo": {"streamName": key}}}


def test_find_stream_id_by_key_returns_matching_id():
    yt = _mock_youtube()
    yt.liveStreams().list().execute.return_value = {
        "items": [_stream("s1", "aaaa-bbbb"), _stream("s2", "cccc-dddd")]
    }
    assert find_stream_id_by_key(yt, "cccc-dddd") == "s2"


def test_find_stream_id_by_key_strips_whitespace():
    yt = _mock_youtube()
    yt.liveStreams().list().execute.return_value = {"items": [_stream("s1", "aaaa-bbbb")]}
    assert find_stream_id_by_key(yt, "  aaaa-bbbb\n") == "s1"


def test_find_stream_id_by_key_follows_pagination():
    yt = _mock_youtube()
    yt.liveStreams().list().execute.side_effect = [
        {"items": [_stream("s1", "aaaa-bbbb")], "nextPageToken": "p2"},
        {"items": [_stream("s2", "cccc-dddd")]},
    ]
    assert find_stream_id_by_key(yt, "cccc-dddd") == "s2"


def test_find_stream_id_by_key_raises_when_missing():
    yt = _mock_youtube()
    yt.liveStreams().list().execute.return_value = {"items": [_stream("s1", "aaaa-bbbb")]}
    with pytest.raises(ValueError, match="não encontrada"):
        find_stream_id_by_key(yt, "zzzz-zzzz")
