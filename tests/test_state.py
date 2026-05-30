import json
import pytest
from core.state import load_config, save_config, DEFAULT_CONFIG, DEFAULT_PROFILE


def test_load_returns_defaults_when_no_file(tmp_path, monkeypatch):
    monkeypatch.setattr("core.state.CONFIG_PATH", str(tmp_path / "config.json"))
    result = load_config()
    assert result == DEFAULT_CONFIG


def test_save_and_load_roundtrip(tmp_path, monkeypatch):
    path = str(tmp_path / "config.json")
    monkeypatch.setattr("core.state.CONFIG_PATH", path)
    data = {**DEFAULT_CONFIG}
    data["profiles"][0]["title"] = "AO VIVO: TEST"
    save_config(data)
    loaded = load_config()
    assert loaded["profiles"][0]["title"] == "AO VIVO: TEST"


def test_load_migration_from_single_config(tmp_path, monkeypatch):
    path = str(tmp_path / "config.json")
    monkeypatch.setattr("core.state.CONFIG_PATH", path)
    old_data = {
        "title": "OLD TITLE",
        "description": "OLD DESC",
        "test_mode": True
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(old_data, f)
    
    result = load_config()
    assert "profiles" in result
    assert len(result["profiles"]) == 1
    assert result["profiles"][0]["title"] == "OLD TITLE"
    assert result["profiles"][0]["description"] == "OLD DESC"
    assert result["profiles"][0]["name"] == "Imported Profile"
    assert result["test_mode"] is True


def test_load_merges_missing_keys(tmp_path, monkeypatch):
    path = str(tmp_path / "config.json")
    monkeypatch.setattr("core.state.CONFIG_PATH", path)
    # New structure partial load
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"test_mode": True}, f)
    result = load_config()
    assert result["test_mode"] is True
    assert "profiles" in result
    assert len(result["profiles"]) == 1


def test_save_preserves_unicode(tmp_path, monkeypatch):
    path = str(tmp_path / "config.json")
    monkeypatch.setattr("core.state.CONFIG_PATH", path)
    data = {**DEFAULT_CONFIG}
    data["profiles"][0]["description"] = "💚 Membro do Canal"
    save_config(data)
    loaded = load_config()
    assert loaded["profiles"][0]["description"] == "💚 Membro do Canal"
