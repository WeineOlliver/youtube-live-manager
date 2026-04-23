import json
import pytest
from core.state import load_config, save_config, DEFAULT_CONFIG


def test_load_returns_defaults_when_no_file(tmp_path, monkeypatch):
    monkeypatch.setattr("core.state.CONFIG_PATH", str(tmp_path / "config.json"))
    result = load_config()
    assert result == DEFAULT_CONFIG


def test_save_and_load_roundtrip(tmp_path, monkeypatch):
    path = str(tmp_path / "config.json")
    monkeypatch.setattr("core.state.CONFIG_PATH", path)
    data = {**DEFAULT_CONFIG, "title": "AO VIVO: TEST"}
    save_config(data)
    loaded = load_config()
    assert loaded["title"] == "AO VIVO: TEST"


def test_load_merges_missing_keys(tmp_path, monkeypatch):
    path = str(tmp_path / "config.json")
    monkeypatch.setattr("core.state.CONFIG_PATH", path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"title": "PARTIAL"}, f)
    result = load_config()
    assert result["title"] == "PARTIAL"
    assert result["description"] == ""
    assert result["test_mode"] is False


def test_save_preserves_unicode(tmp_path, monkeypatch):
    path = str(tmp_path / "config.json")
    monkeypatch.setattr("core.state.CONFIG_PATH", path)
    data = {**DEFAULT_CONFIG, "description": "💚 Membro do Canal"}
    save_config(data)
    loaded = load_config()
    assert loaded["description"] == "💚 Membro do Canal"
